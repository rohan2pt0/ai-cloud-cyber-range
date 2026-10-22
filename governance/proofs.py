#!/usr/bin/env python3
"""Proof gaps: the claims in the docs that no journey proves yet, and which journey could (doc 28, doc 55).

    ./securax proofs              the 5 claims that a journey could prove next
    ./securax proofs --top 10     more of them
    ./securax proofs --all        every unproven or dated claim on an amber or red page
    ./securax proofs --json       the same, for the cockpit or a script

Where it looks:
- docs/status.yml: every amber and red light, and its text.
- sandbox/run.py: every @journey(name, description), read without running anything.
- lifecycle/impact.json: which components each journey guards.
- git log: when each page was last touched.

For each amber or red page it takes the clauses that say "not yet proven / run / verified", "not built", "dated" or "next",
and names the existing journey whose name and description share the most distinctive words with the claim, or says that
none does (then a new journey is the proof).

Ranking: claims that say "not yet proven / verified / run" first (a journey can prove those), then red pages, then pages
touched most recently.
Standard library only. Exit codes: 0 always (it is a report); 2 when a source file is missing.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

STATUS_LINE = re.compile(r"""^\s*([^#\s][^:]*?):\s*\[\s*(green|amber|red)\s*,\s*(".*"|'.*'|[^\]]*)\s*\]\s*$""")
UNPROVEN = re.compile(r"\bnot yet (?:proven|run|verified|seen|scored|exercised|tested)\b|\bnot (?:verified|proven|exercised)\b"
                      r"|\bverified only\b|\bpartly proven\b|\bnot all are proven\b|\bparse-checked\b", re.I)
DATED = re.compile(r"\bdated\b|\bare next\b|\bis next\b|\bwaits?\b|\bplanned\b|\bqueued\b|\bnot built\b|\ba plan\b|\bon paper\b"
                   r"|\bnot started\b|\bhas not been started\b|\bno \w+ (?:has|have) been started\b|\bare still proposed\b", re.I)
NOT_A_GAP = re.compile(r"\bdated (?:January|February|March|April|May|June|July|August|September|October|November|December)\b", re.I)
DATE_ONLY = re.compile(r"^\s*(?:dated|targets?|dates?)(?: in the doc)?\s*$", re.I)
STOP = set("""a an and are as at be been but by can doc docs each every for from has have in into is it its itself no not of on
one or our own so still than that the their them then there these this those to up was were when which while with without you
your yet run runs proven proof verified tested built build test tests dated next real here only now more most until after before
same new also all any very just get gets set like via per whole about over under used use uses later steps step part partly
plan planned queued wait waits first estate securax need needs page live mode check""".split())
TOP = 5


def _words(text: str) -> set[str]:
    out = set()
    for w in re.findall(r"[a-z][a-z0-9]+", text.lower().replace("_", " ").replace("-", " ")):
        w = w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w
        if len(w) >= 3 and w not in STOP:
            out.add(w)
    return out


# ── sources ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def read_status(path: pathlib.Path) -> list[dict]:
    """docs/status.yml as [{doc, light, text}], in file order. A tiny reader for its one-line `page: [light, "text"]` rows."""
    rows = []
    for line in path.read_text("utf-8").splitlines():
        m = STATUS_LINE.match(line)
        if not m:
            continue
        raw = m.group(3).strip()
        if raw.startswith('"'):
            try:
                text = json.loads(raw)
            except ValueError:
                text = raw[1:-1]
        elif raw.startswith("'"):
            text = raw[1:-1].replace("''", "'")
        else:
            text = raw
        rows.append({"doc": m.group(1).strip(), "light": m.group(2), "text": text})
    return rows


def read_journeys(path: pathlib.Path) -> dict[str, str]:
    """{name: description} for every @journey(...) in sandbox/run.py, parsed (never imported or run)."""
    tree = ast.parse(path.read_text("utf-8"))
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        for dec in getattr(node, "decorator_list", []):
            if isinstance(dec, ast.Call) and getattr(dec.func, "id", "") == "journey" and dec.args:
                vals = [a.value if isinstance(a, ast.Constant) and isinstance(a.value, str) else "" for a in dec.args[:2]]
                if vals[0]:
                    out[vals[0]] = vals[1] if len(vals) > 1 else ""
    return out


def read_guards(path: pathlib.Path) -> dict[str, list[str]]:
    """{journey: [components it guards]} from lifecycle/impact.json."""
    try:
        comps = json.loads(path.read_text("utf-8")).get("components", {})
    except (OSError, ValueError):
        return {}
    out: dict[str, list[str]] = {}
    for name, c in comps.items():
        for j in c.get("guarded_by", []):
            out.setdefault(j, []).append(name)
    return out


def touched(root: pathlib.Path, docs_dir: str = "docs") -> dict[str, int]:
    """{page relative to docs/: unix time it was last committed}, from ONE git log. Empty when there is no git history."""
    try:
        r = subprocess.run(["git", "-C", str(root), "log", "--format=@%ct", "--name-only", "--", docs_dir],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return {}
    if r.returncode != 0:
        return {}
    out: dict[str, int] = {}
    when = 0
    prefix = docs_dir.rstrip("/") + "/"
    for line in r.stdout.splitlines():
        if line.startswith("@"):
            when = int(line[1:] or 0)
        elif line.startswith(prefix):
            out.setdefault(line[len(prefix):], when)
    return out


# ── claims ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _top_level(text: str) -> list[str]:
    """Split at sentence ends and semicolons that are not inside brackets."""
    out, cur, depth = [], [], 0
    for i, ch in enumerate(text):
        depth += (ch == "(") - (ch == ")")
        end = depth <= 0 and (ch == ";" or (ch == "." and (i + 1 == len(text) or text[i + 1].isspace())))
        if end:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return [s.strip(" ,:") for s in out if s.strip(" ,:")]


def _kind(text: str) -> str:
    return "unproven" if UNPROVEN.search(text) else "dated" if DATED.search(text) and not NOT_A_GAP.search(text) else ""


def _segments(text: str) -> list[str]:
    """The clauses that name a gap. A sentence that names one outside its brackets is kept whole, brackets and all; when only
    a bracket names it ('... the USB kit (the Linux one run in tests; the Windows one not yet run) ...'), that part is taken."""
    out = []
    for seg in _top_level(text):
        if _kind(re.sub(r"\([^()]*\)", "", seg)):
            out.append(seg)
            continue
        for inner in re.findall(r"\(([^()]*)\)", seg):
            out += [p.strip(" ,:") for p in inner.split(";") if _kind(p) and not DATE_ONLY.match(p)]
    return out


def claims(row: dict) -> list[dict]:
    """The unproven or dated clauses of one amber page. A red page (not built) is one claim: its whole text."""
    if row["light"] == "green":
        return []
    if row["light"] == "red":
        return [{"doc": row["doc"], "light": "red", "kind": _kind(row["text"]) or "dated", "claim": row["text"].strip()}]
    return [{"doc": row["doc"], "light": row["light"], "kind": _kind(seg), "claim": seg} for seg in _segments(row["text"])]


def suggest(claim: str, journeys: dict[str, str], guards: dict[str, list[str]]) -> dict:
    """The journey sharing the most distinctive words with the claim (rare words weigh more), or none when the overlap is thin."""
    if not journeys:
        return {"journey": None, "shares": [], "guards": []}
    words = {j: _words(j + " " + d) for j, d in journeys.items()}
    df: dict[str, int] = {}
    for ws in words.values():
        for w in ws:
            df[w] = df.get(w, 0) + 1
    n = len(journeys)
    want = _words(claim)
    best, best_score, best_shared = None, 0.0, []
    for j, ws in words.items():
        shared = sorted(want & ws)
        score = sum(math.log(1 + n / df[w]) for w in shared)
        if score > best_score or (score == best_score and best and j < best):
            best, best_score, best_shared = j, score, shared
    if len(best_shared) < 2 or best_score < 2.5:
        return {"journey": None, "shares": best_shared, "guards": []}
    return {"journey": best, "shares": best_shared, "guards": guards.get(best, [])}


def gaps(status: list[dict], journeys: dict[str, str], guards: dict[str, list[str]], when: dict[str, int]) -> list[dict]:
    """Every claim with its suggestion, ranked: 'not yet proven/verified/run' first, then red, then the newest-touched page."""
    out = []
    for row in status:
        for c in claims(row):
            c.update(suggest(c["claim"], journeys, guards))
            c["touched"] = when.get(row["doc"], 0)
            out.append(c)
    # What a journey can prove comes first: an unproven claim before a plan on paper (a business model or a certification
    # is not proved by a test), then red before amber, then the page touched most recently.
    out.sort(key=lambda c: (c["kind"] != "unproven", c["light"] != "red", -c["touched"], c["doc"]))
    return out


def report(root: pathlib.Path = ROOT) -> list[dict]:
    status = read_status(root / "docs" / "status.yml")
    return gaps(status, read_journeys(root / "sandbox" / "run.py"), read_guards(root / "lifecycle" / "impact.json"), touched(root))


def render(items: list[dict], top: int | None, total: int) -> str:
    shown = items if top is None else items[:top]
    head = f"The {len(shown)} claims that a journey could prove next" if top is not None else f"All {total} claims not yet proven"
    lines = [f"{head} ({total} in all, from docs/status.yml):", ""]
    for i, c in enumerate(shown, 1):
        claim = c["claim"] if len(c["claim"]) <= 150 else c["claim"][:147] + "..."
        lines.append(f"{i}. [{c['light']}] {c['doc']}")
        lines.append(f"   {claim}")
        if c["journey"]:
            extra = f"; it guards {', '.join(c['guards'])}" if c["guards"] else ""
            lines.append(f"   closest journey: {c['journey']} (shares: {', '.join(c['shares'][:4])}{extra})")
        else:
            lines.append("   no journey covers it yet: a new one in sandbox/run.py is the proof")
    if not shown:
        lines.append("Nothing to prove: every amber and red page names no unproven or dated claim.")
    elif top is not None and total > len(shown):
        lines += ["", "Every claim: ./securax proofs --all"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax proofs", description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--all", action="store_true", help="every claim, not only the top ones")
    ap.add_argument("--top", type=int, default=TOP, help=f"how many to show (default {TOP})")
    ap.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    root = pathlib.Path(a.root)
    for need in ("docs/status.yml", "sandbox/run.py"):
        if not (root / need).exists():
            print(f"proofs: {need} not found under {root}", file=sys.stderr)
            return 2
    items = report(root)
    top = None if a.all else max(a.top, 0)
    if a.json:
        print(json.dumps({"total": len(items), "claims": items if top is None else items[:top]}, indent=1))
    else:
        print(render(items, top, len(items)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
