#!/usr/bin/env python3
"""Is SecuRAX ready to launch? The go/no-go gates, worked out from the repository (doc: docs/securax/release-readiness.md).

    ./securax release ready                the verdict for the public launch and for the paid edition, and what blocks each
    ./securax release ready --all          the same, with the gates that already pass
    ./securax release ready --launch paid  exit 1 unless the paid edition is GO (the default checks the public launch)
    ./securax release ready --json         for the cockpit or a routine
    ./securax release ready --for-tag v1.0.0   what the release workflow asks: a 1.0.0 or later tag needs the public launch GO

Two launches are judged: 'open' (the public launch of the free core) and 'paid' (charging for an edition). Each gate in
governance/release-gates.json is a PROBE or an ATTEST. A probe is a small function below that reads the repository, so a
gate's state is never typed in: it is GO when the thing is there. An attest is something only the owner can confirm (a
repository setting, a lawyer's letter): it is GO once it carries a date and where the evidence is kept. A failing probe
must carry open_since, a queue id and a due date; fitness `release-gates` fails one that goes red without that record,
and a record left behind on a gate that is green. Standard library only; it reads files and runs nothing but `git ls-files`.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "governance" / "release-gates.json"
WORKFLOWS = ROOT / ".github" / "workflows"
FIRST_PARTY = {"actions", "github"}                      # GitHub's own build steps; everyone else's are pinned by commit
TRACKERS = ("google-analytics.com", "googletagmanager.com", "doubleclick.net", "connect.facebook.net", "cdn.segment.com",
            "mixpanel.com", "hotjar.com", "clarity.ms", "amplitude.com", "posthog.com", "sentry.io", "plausible.io",
            "fonts.googleapis.com", "fonts.gstatic.com", "cdn.jsdelivr.net", "unpkg.com", "cdnjs.cloudflare.com")
PRICE_FEEDS = ("api.kite.trade", "finance.yahoo.com", "alphavantage.co", "mfapi.in", "api.coingecko.com", "nseindia.com/api",
               "api.bseindia.com", "tradingview.com", "twelvedata.com", "finnhub.io", "polygon.io", "iexcloud.io")
ADVICE = {                                               # the shapes that turn education into advice (SEBI adviser rules)
    "tells the person to trade": r"\b(buy|sell|accumulate|book profits? in|exit)\b[^.\n\"']{0,40}\b(shares?|stocks?|scrips?|mutual funds?|ETFs?|bonds?|crypto|gold)\b",
    "promises a return": r"\b(guaranteed|assured|sure[- ]shot|risk[- ]free)\b[^.\n\"']{0,30}\b(returns?|profits?|gains?|income|allotment)|\bmultibagger|\btarget price\b|double your money",
    "calls us an adviser": r"\b(your|our) (financial|investment|wealth|robo)[- ]?(advis[eo]r|planner)\b|\bwe (recommend|advise) (you )?(to )?(invest|buy|sell)",
    "picks products": r"\b(best|top)( \d+)? (mutual funds?|stocks?|shares|schemes?|ETFs?)\b",
}
NOT_OPEN_SOURCE = (r"open[- ]source (edition|core|version|product|platform|launch|release)|\b(is|are|stays?|remains?|fully|100%) open[- ]source\b"
                   r"|free and open[- ]source|\bFOSS\b")
PRIVACY_PARTS = ("who is responsible", "what we collect", "what leaves your device", "your rights", "how to complain", "children", "how long we keep")
DISCLAIMER_PARTS = ("security", "compliance", "money and tax", "health", "ai answers", "authorised use")
TERMS_PARTS = ("price and renewal", "cancelling and refunds", "liability", "governing law")
COERCION = r"coerc|stalk|without (their|the person'?s?) (knowledge|consent)|someone else'?s? (phone|mailbox|device)|partner|another person'?s"


def read(rel: str) -> str:
    try:
        return (ROOT / rel).read_text("utf-8", "ignore")
    except OSError:
        return ""


def load() -> dict:
    return json.loads(REGISTRY.read_text("utf-8"))


def tracked() -> list[str]:
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], text=True, capture_output=True, timeout=30)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        pass
    skip = {".git", "node_modules", "vault", "backups", "evidence"}          # no git here (a source archive): walk what is on disk
    return [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and not skip & set(p.relative_to(ROOT).parts)]


def workflows() -> dict[str, str]:
    return {p.name: p.read_text("utf-8") for p in sorted(WORKFLOWS.glob("*.yml"))}


def shipped_pages() -> list[str]:
    """What a person's browser loads: the site's own pages and every app (never the generated docs)."""
    keep = []
    for f in tracked():
        if f.startswith(("website/docs/", "guiding-map/tests/", "guiding-map/node_modules/", "guiding-map/ocr/")):
            continue
        if f.startswith(("website/", "guiding-map/", "portal/")) and f.endswith((".html", ".js", ".css")):
            keep.append(f)
    return keep


def money_copy() -> list[str]:
    """Every file whose words about money a person reads."""
    return [f for f in tracked() if f == "README.md" or f == "guiding-map/index.html"
            or (f.startswith(("guiding-map/kit/", "guiding-map/levers/", "guiding-map/systems/")) and f.endswith(".json") and "/i18n/" not in f)
            or (f.startswith("website/") and f.endswith(".html") and not f.startswith("website/docs/"))]


def latin_only(text: str) -> bool:
    return not re.search(r"[ऀ-ॿ؀-ۿ֐-׿]", text)


# ─────────────────────────────────────────────── the probes ───────────────────────────────────────────────
def secrets_scanned(reg: dict) -> tuple[bool, str]:
    ci, pre = read(".github/workflows/devsecops.yml"), read(".pre-commit-config.yaml")
    missing = [n for n, ok in (("the gitleaks step in devsecops.yml", "gitleaks/gitleaks-action" in ci),
                               ("a full-history checkout (fetch-depth: 0) for it", "fetch-depth: 0" in ci),
                               ("a run on every pull request", bool(re.search(r"^\s*pull_request:", ci, re.M))),
                               ("the gitleaks pre-commit hook", "id: gitleaks" in pre)) if not ok]
    return not missing, "missing: " + "; ".join(missing) if missing else "gitleaks on every push and pull request over the whole history, and before a commit"


def no_secret_files(reg: dict) -> tuple[bool, str]:
    bad = [f for f in tracked() if re.search(r"(^|/)\.env($|\.)|\.(pem|key|p12|pfx|kdbx|jks)$|(^|/)id_(rsa|ed25519)|^vault/|(^|/)\.(npmrc|pypirc|netrc)$", f)
           and not re.search(r"example|sample|template", f, re.I)]
    return not bad, "tracked: " + ", ".join(bad[:5]) if bad else "no key file, environment file or vault content is tracked"


def release_signed(reg: dict) -> tuple[bool, str]:
    rel = read(".github/workflows/release.yml")
    need = {"the SBOM step": "anchore/sbom-action", "SHA256SUMS": "SHA256SUMS", "signed provenance": "actions/attest-build-provenance",
            "permission to sign (id-token: write)": "id-token: write", "permission to store the attestation": "attestations: write",
            "a draft first": "draft: true", "publishing only after every file is attached": "--draft=false",
            "the tests before the release (needs: verify)": "needs: verify", "the tag matching VERSION": "Tag matches VERSION"}
    missing = [n for n, s in need.items() if s not in rel]
    return not missing, "release.yml lost: " + "; ".join(missing) if missing else "SBOM, checksums and signed provenance; drafted, then published"


def unpinned_actions() -> list[str]:
    out = []
    for name, text in workflows().items():
        for m in re.finditer(r"^\s*-?\s*uses:\s*([^\s#]+)", text, re.M):
            use = m.group(1).strip("\"'")
            if use.startswith("./"):
                continue
            who, _, ref = use.partition("@")
            if who.split("/")[0] not in FIRST_PARTY and not re.fullmatch(r"[0-9a-f]{40}", ref):
                out.append(f"{name}: {use}")
    return sorted(set(out))


def actions_pinned(reg: dict) -> tuple[bool, str]:
    bad = unpinned_actions()
    return not bad, f"{len(bad)} step(s) on a movable tag: " + ", ".join(b.split(": ")[1] for b in bad[:4]) + ("…" if len(bad) > 4 else "") if bad else "every third-party step is pinned to a commit"


def workflow_problems(flows: dict[str, str]) -> list[str]:
    probs = []
    risky = re.compile(r"\$\{\{[^}]*github\.(head_ref|event\.(issue|pull_request|comment|review|discussion|head_commit)\.[a-z_.]*(title|body|message|ref|label|name|email))")
    for name, text in flows.items():
        if "pull_request_target" in text:
            probs.append(f"{name}: pull_request_target runs with write access on a stranger's pull request")
        if re.search(r"^permissions:\s*write-all", text, re.M):
            probs.append(f"{name}: permissions write-all")
        if not re.search(r"^permissions:", text, re.M):
            probs.append(f"{name}: no top-level permissions (the default may be write)")
        for line in text.splitlines():
            if risky.search(line):
                key = re.match(r"\s*-?\s*([A-Za-z_][A-Za-z0-9_-]*):\s", line)
                if not key or key.group(1) == "run":                 # safe only as an env value, an input or an if: never inside a script
                    probs.append(f"{name}: a stranger's text goes into a shell: {line.strip()[:70]}")
    return probs


def workflows_safe(reg: dict) -> tuple[bool, str]:
    probs = workflow_problems(workflows())
    return not probs, "; ".join(probs[:3]) if probs else "no workflow gives a stranger write access, secrets or a shell"


def third_party_notices(reg: dict) -> tuple[bool, str]:
    files, rel = tracked(), read(".github/workflows/release.yml")
    missing = [n for n, ok in (("THIRD-PARTY-NOTICES.md", "THIRD-PARTY-NOTICES.md" in files),
                               ("a licence text beside the bundled text reader (guiding-map/ocr/)", any(re.match(r"guiding-map/ocr/[^/]*(LICEN[CS]E|NOTICE)", f, re.I) for f in files)),
                               ("an SBOM of the source in the release (sbom-source)", "sbom-source" in rel)) if not ok]
    return not missing, "missing: " + "; ".join(missing) if missing else "notices, licence texts and a source SBOM travel with the release"


def dependencies_watched(reg: dict) -> tuple[bool, str]:
    dep = read(".github/dependabot.yml")
    missing = [e for e in ("pip", "npm", "github-actions", "docker") if f'package-ecosystem: "{e}"' not in dep]
    return not missing, "not watched: " + ", ".join(missing) if missing else "pip, npm, containers and build steps are watched weekly"


def verify_documented(reg: dict) -> tuple[bool, str]:
    docs = [f for f in tracked() if f.startswith("docs/") and f.endswith(".md")]
    hit = [f for f in docs if "gh attestation verify" in read(f) and "SHA256SUMS" in read(f)]
    return bool(hit), f"shown in {hit[0]}" if hit else "no doc shows both the checksum and the attestation check"


def contributions_signed_off(reg: dict) -> tuple[bool, str]:
    ok = any("Signed-off-by" in t for t in workflows().values())
    return ok, "a sign-off check runs on pull requests" if ok else "no workflow checks for a Signed-off-by line"


def _models() -> dict:
    return json.loads(read("governance/threat-models.json") or "{}")


def threat_models_hold(reg: dict) -> tuple[bool, str]:
    spec = importlib.util.spec_from_file_location("securax_fitness", ROOT / "lifecycle" / "fitness.py")
    fit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fit)
    # Shape only: a review date that has passed is fitness `threat-modelled`'s to fail (it turns main red by itself), so this gate
    # never flips on a date and the same lapse is not reported twice.
    import datetime
    probs = fit.threat_model_problems(_models(), ROOT, fit.cfg()["budgets"].get("threat_models_baseline", 0), today=datetime.date.min)
    return not probs, "; ".join(probs[:2]) if probs else f"{len(_models().get('models', {}))} models, each complete (review dates are held by fitness threat-modelled)"


def hosted_origin_own(reg: dict) -> tuple[bool, str]:
    left = [t for t in _models().get("models", {}).get("hosted-apps", {}).get("threats", []) if t.get("status") == "accepted" and t.get("stride") in ("I", "E")]
    return not left, (f"{len(left)} accepted, review " + ", ".join(sorted({str(t.get('review')) for t in left})) + ": shared origin, no headers") if left else "the hosted apps have their own origin and real headers"


def _modelled(reg: dict, launch: str) -> tuple[bool, str]:
    have = set(_models().get("models", {}))
    missing = [m for m in reg.get("required_models", {}).get(launch, []) if m not in have]
    return not missing, "no model yet: " + ", ".join(missing) if missing else "every required surface has a model"


def launch_surfaces_modelled(reg: dict) -> tuple[bool, str]:
    return _modelled(reg, "open")


def paid_surfaces_modelled(reg: dict) -> tuple[bool, str]:
    return _modelled(reg, "paid")


def guest_sends_nothing(reg: dict) -> tuple[bool, str]:
    test, pkg = read("guiding-map/tests/test120.js"), read("guiding-map/package.json")
    ok = "leaves its own origin" in test and bool(re.search(r"\btest120\b", pkg))
    return ok, "guiding-map/tests/test120.js runs in npm test" if ok else "the egress test is missing or not in npm test"


def no_trackers(reg: dict) -> tuple[bool, str]:
    bad = []
    foreign = re.compile(r"<script[^>]+src=[\"']https?://|<link[^>]+href=[\"']https?://[^>]*stylesheet|<link[^>]+stylesheet[^>]+href=[\"']https?://"
                         r"|@import\s+(url\()?[\"']?https?://|importScripts\(\s*[\"']https?://|<iframe[^>]+src=[\"']https?://", re.I)
    for f in shipped_pages():
        text = read(f)
        bad += [f"{f}: names {t}" for t in TRACKERS if t in text]
        if foreign.search(text):
            bad.append(f"{f}: loads code or style from another site")
    return not bad, "; ".join(bad[:3]) if bad else "no page loads anything from another site or names a tracker"


def code_hosts() -> set[str]:
    hosts = set()
    for f in shipped_pages():
        hosts |= {h.lower() for h in re.findall(r"\b[A-Z][A-Z0-9_]{2,}\s*=\s*[\"']https://([A-Za-z0-9.-]+)", read(f))}
    return hosts


def flows_declared(reg: dict) -> tuple[bool, str]:
    probs, declared = [], set()
    for fl in reg.get("flows", []):
        declared |= set(fl.get("hosts", []))
        probs += [f"flow '{fl.get('id', '?')}' does not say {k}" for k in ("what", "when", "to", "protection", "model") if len(str(fl.get(k, "")).strip()) < 8]
    used = code_hosts()
    probs += [f"the code calls {h}, which no flow declares" for h in sorted(used - declared)]
    probs += [f"flow host {h} is no longer in the code" for h in sorted(declared - used)]
    return not probs, "; ".join(probs[:3]) if probs else f"{len(reg.get('flows', []))} flows declared; every outside address in the code belongs to one"


def _page(name: str, parts: tuple[str, ...], links: tuple[str, ...]) -> tuple[bool, str]:
    text = read(name).lower()
    if not text:
        return False, f"{name} does not exist"
    missing = [p for p in parts if p not in text] + [f"a link from {f}" for f in links if name not in read(f)]
    return not missing, f"{name} lacks: " + "; ".join(missing) if missing else f"{name} has every part and is linked"


def privacy_notice(reg: dict) -> tuple[bool, str]:
    return _page("PRIVACY.md", PRIVACY_PARTS, ("README.md", "website/index.html"))


def disclaimer(reg: dict) -> tuple[bool, str]:
    return _page("DISCLAIMER.md", DISCLAIMER_PARTS, ("README.md", "website/index.html"))


def paid_terms(reg: dict) -> tuple[bool, str]:
    return _page("TERMS.md", TERMS_PARTS, ("website/index.html",))


def export_and_erase(reg: dict) -> tuple[bool, str]:
    app, pkg = read("guiding-map/index.html"), read("guiding-map/package.json")
    ok = "function gmExportBackup(" in app and "function resetAll(" in app and bool(re.search(r"\btest46\b", pkg))
    return ok, "export and a typed-confirmation erase, held by guiding-map/tests/test46.js" if ok else "export, erase or their test (test46) is missing"


def dpdp_map_verified(reg: dict) -> tuple[bool, str]:
    try:
        d = json.loads(read("governance/regulators/dpdp.json"))
    except ValueError:
        d = {}
    ok = d.get("verified") is True and bool(d.get("verified_on"))
    return ok, f"verified on {d.get('verified_on')}" if ok else "governance/regulators/dpdp.json is not verified, and covers the breach clock only"


def advice_hits() -> list[tuple[str, str, str]]:
    """(file, kind, the words) for every advice-shaped phrase in the copy a person reads; translations are checked through their English source."""
    hits = []
    for f in money_copy():
        text = read(f)
        for kind, pat in ADVICE.items():
            for m in re.finditer(pat, text, re.I):
                ctx = text[max(0, m.start() - 60):m.end() + 40].replace("\n", " ")
                if latin_only(ctx):
                    hits.append((f, kind, ctx))
    return hits


def no_recommendation(reg: dict) -> tuple[bool, str]:
    reviewed = [r["phrase"] for r in reg.get("advice_wording_reviewed", [])]
    hits = advice_hits()
    new = [(f, k, c) for f, k, c in hits if not any(p in c for p in reviewed)]
    stale = [p for p in reviewed if not any(p in c for _, _, c in hits)]
    if new:
        return False, f"{new[0][0]} {new[0][1]}: …{new[0][2][40:120]}…" + (f" (+{len(new) - 1} more)" if len(new) > 1 else "")
    if stale:
        return False, "a reviewed phrase is no longer in the copy; remove it from advice_wording_reviewed: " + stale[0]
    return True, f"no advice-shaped wording; {len(reviewed)} phrase(s) reviewed with a reason"


def no_live_prices(reg: dict) -> tuple[bool, str]:
    bad = sorted({f"{f}: {h}" for f in shipped_pages() for h in PRICE_FEEDS if h in read(f)})
    return not bad, "; ".join(bad[:3]) if bad else "no app reads a market price feed"


def no_referral_links(reg: dict) -> tuple[bool, str]:
    pat = re.compile(r"https?://[^\s\"'<>)]+[?&](ref|referral|referrer|aff|affiliate|aff_id|partner|utm_[a-z]+|clickid|irclickid)=", re.I)
    bad = sorted({f"{f}: {m.group(0)[:70]}" for f in money_copy() for m in pat.finditer(read(f))})
    return not bad, "; ".join(bad[:3]) if bad else "no link carries a referral or campaign tag"


def education_line(reg: dict) -> tuple[bool, str]:
    surfaces = {"the Life OS": "guiding-map/index.html", "Vantage": "guiding-map/kit/editions/vantage.json", "the site": "website/index.html"}
    line = re.compile(r"education[^.]{0,80}not[^.]{0,40}advice[^<\"]{0,200}registered investment advis[eo]r", re.I | re.S)
    missing = [n for n, f in surfaces.items() if not line.search(read(f))]
    return not missing, "the line is not shown in: " + ", ".join(missing) if missing else "the education line is in every money surface"


def ai_personas_bounded(reg: dict) -> tuple[bool, str]:
    app = read("guiding-map/index.html")
    roles = re.findall(r'\{ k: "(finance|insurance|tax|legal|realestate|estate|eldercare)", n: "[^"]*", role: "([^"]*)"', app)
    named = sorted({k for k, role in roles if re.search(r"advis[eo]r", role, re.I)})
    missing = ([f"still called advisers: {', '.join(named)}"] if named else []) + ([] if "name no specific" in app else ["no rule against naming a product"])
    if not roles:
        missing.append("the personas were not found (the probe needs updating)")
    return not missing, "; ".join(missing) if missing else "the regulated personas are guides and name no product"


def licence_wording(reg: dict) -> tuple[bool, str]:
    pages = [f for f in tracked() if f in ("README.md", "docs/index.md", "GETTING-STARTED.md", "features.json", "products.json")
             or (f.startswith("website/") and f.endswith(".html") and not f.startswith("website/docs/"))]
    bad = [f"{f}: '{m.group(0)}'" for f in pages for m in re.finditer(NOT_OPEN_SOURCE, read(f), re.I)]
    return not bad, "; ".join(bad[:3]) if bad else "no storefront page calls the current version open source"


def fake_copy_route(reg: dict) -> tuple[bool, str]:
    sec = read("SECURITY.md").lower()
    missing = [w for w in ("fake cop", "misuse", "attestation") if w not in sec]
    return not missing, "SECURITY.md does not cover: " + ", ".join(missing) if missing else "SECURITY.md says where the real copy lives, how to check one and how to report a fake"


def coercive_setup_modelled(reg: dict) -> tuple[bool, str]:
    models = _models().get("models", {})
    missing = [m for m in ("estate-sms-inbox", "life-os-bank-mail")
               if not any(re.search(COERCION, str(t.get("threat", "")), re.I) for t in models.get(m, {}).get("threats", []))]
    return not missing, "no such threat in: " + ", ".join(missing) if missing else "both message-reading features consider a set-up on someone else"


def gateway_abuse_rails(reg: dict) -> tuple[bool, str]:
    missing = [f for f in ("test_spend.py", "test_cross_site.py", "test_human_in_command.py") if not (ROOT / "apps" / "llm-gateway" / "tests" / f).exists()]
    return not missing, "missing gateway tests: " + ", ".join(missing) if missing else "allowance, foreign-origin refusal and human-in-command are tested"


PROBES = {f.__name__: f for f in (
    secrets_scanned, no_secret_files, release_signed, actions_pinned, workflows_safe, third_party_notices, dependencies_watched,
    verify_documented, contributions_signed_off, threat_models_hold, hosted_origin_own, launch_surfaces_modelled, paid_surfaces_modelled,
    guest_sends_nothing, no_trackers, flows_declared, privacy_notice, disclaimer, paid_terms, export_and_erase, dpdp_map_verified,
    no_recommendation, no_live_prices, no_referral_links, education_line, ai_personas_bounded, licence_wording, fake_copy_route, coercive_setup_modelled,
    gateway_abuse_rails)}


# ─────────────────────────────────────────────── the verdict ───────────────────────────────────────────────
def judge(reg: dict | None = None) -> list[dict]:
    """Every gate with its live state: go, no-go (a failing probe) or waiting-owner (an attest not yet given)."""
    reg = reg or load()
    out = []
    for g in reg.get("gates", []):
        row = {k: g.get(k) for k in ("id", "area", "blocks", "title", "why", "fix", "how", "queue", "due", "open_since")}
        if "probe" in g:
            fn = PROBES.get(g["probe"])
            ok, detail = fn(reg) if fn else (False, f"unknown probe '{g['probe']}'")
            row.update(kind="probe", state="go" if ok else "no-go", detail=detail)
        else:
            a = g.get("attest") or {}
            ok = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(a.get("on", ""))) and len(str(a.get("evidence", "")).strip()) >= 8)
            row.update(kind="attest", state="go" if ok else "waiting-owner", detail=f"confirmed {a.get('on')}: {a.get('evidence')}" if ok else "the owner has not confirmed this yet")
        out.append(row)
    return out


def verdict(rows: list[dict], launch: str) -> bool:
    return all(r["state"] == "go" for r in rows if launch in (r.get("blocks") or []))


def problems(reg: dict | None = None, rows: list[dict] | None = None, queue: dict | None = None) -> list[str]:
    """What fitness `release-gates` holds: the registry is well formed, and no gate is failing without a record or green with a stale one."""
    reg = reg or load()
    rows = rows if rows is not None else judge(reg)
    if queue is None:
        try:
            queue = json.loads(read("governance/queue.json"))
        except ValueError:
            queue = {}
    states = {i.get("id"): i.get("state") for i in queue.get("items", [])}
    probs, seen = [], set()
    by_id = {g.get("id"): g for g in reg.get("gates", [])}
    for r in rows:
        gid, g = r["id"], by_id.get(r["id"], {})
        if not gid or gid in seen:
            probs.append(f"'{gid}': gate ids must be present and unique")
        seen.add(gid)
        if not r.get("blocks") or set(r["blocks"]) - set(reg.get("launches", {})):
            probs.append(f"'{gid}': blocks must name open, paid or both")
        if len(str(r.get("title", ""))) < 20 or len(str(r.get("why", ""))) < 20:
            probs.append(f"'{gid}': say what the gate is and why it matters, in a sentence each")
        if ("probe" in g) == ("attest" in g):
            probs.append(f"'{gid}': a gate is a probe or an attest, exactly one")
        if r["kind"] == "probe" and g.get("probe") not in PROBES:
            probs.append(f"'{gid}': probe '{g.get('probe')}' does not exist in governance/release_gates.py")
        dated = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(r.get("due") or "")))
        queued = r.get("queue") in states and states.get(r.get("queue")) != "done"
        if r["state"] == "no-go":
            if not (r.get("open_since") and r.get("fix") and dated):
                probs.append(f"'{gid}': the probe fails ({r['detail'][:90]}). Fix it, or record it on purpose: open_since, fix, queue and due")
            elif not queued:
                probs.append(f"'{gid}': its queue item '{r.get('queue')}' is missing or done while the gate still fails")
        elif r["state"] == "go" and r["kind"] == "probe" and r.get("open_since"):
            probs.append(f"'{gid}': the probe passes now; remove open_since, fix, queue and due from the gate")
        elif r["state"] == "waiting-owner" and not (r.get("how") and dated and queued):
            probs.append(f"'{gid}': an attest that is waiting needs how, a live queue item and a due date")
    return probs


def tag_needs_launch(tag: str) -> bool:
    m = re.fullmatch(r"v?(\d+)\.\d+\.\d+", tag.strip())
    return bool(m) and int(m.group(1)) >= 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--all", action="store_true", help="also list the gates that pass")
    ap.add_argument("--launch", choices=("open", "paid"), default="open", help="which launch decides the exit code")
    ap.add_argument("--for-tag", metavar="vX.Y.Z", help="exit 1 only if this tag is 1.0.0 or later and the public launch is NO-GO")
    a = ap.parse_args(argv)
    reg = load()
    rows = judge(reg)
    go = {name: verdict(rows, name) for name in reg["launches"]}
    if a.json:
        print(json.dumps({"verdict": {k: "GO" if v else "NO-GO" for k, v in go.items()}, "gates": rows, "problems": problems(reg, rows)}, indent=1))
    else:
        for name, what in reg["launches"].items():
            mine = [r for r in rows if name in r["blocks"]]
            left = [r for r in mine if r["state"] != "go"]
            print(f"{'GO   ' if go[name] else 'NO-GO'}  {what}: {len(mine) - len(left)} of {len(mine)} gates pass")
        left = [r for r in rows if r["state"] != "go"]
        for area in dict.fromkeys(r["area"] for r in left):
            print(f"\n  {area}")
            for r in (r for r in left if r["area"] == area):
                mark = "owner" if r["state"] == "waiting-owner" else "no-go"
                print(f"    [{mark}] {r['id']}  (blocks {' and '.join(r['blocks'])}; due {r.get('due') or 'not dated'})")
                print(f"            {r['title']}.")
                print(f"            Now: {r['detail']}.")
                print(f"            Next: {r.get('fix') or r.get('how')}.")
        passing = [r for r in rows if r["state"] == "go"]
        if a.all:
            print("\n  passing")
            for r in passing:
                print(f"    [go]    {r['id']}: {r['detail']}")
        elif passing:
            print(f"\n  {len(passing)} gate(s) pass (./securax release ready --all lists them). The reasoning is in docs/securax/release-readiness.md.")
    if a.for_tag:
        if tag_needs_launch(a.for_tag) and not go["open"]:
            print(f"\n{a.for_tag} is a public launch (1.0.0 or later) and the public-launch gates are NO-GO: this tag cannot be released yet.", file=sys.stderr)
            return 1
        return 0
    return 0 if go[a.launch] else 1


if __name__ == "__main__":
    sys.exit(main())
