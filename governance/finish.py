#!/usr/bin/env python3
"""Finish setting up, one step at a time: every optional part of SecuRAX with what it gives you, whether it is done,
and the exact steps. The Command Center shows the same list, so nothing optional is forgotten or needs a doc hunt.

    ./securax finish                 what is done, what is left, and the next one to do
    ./securax finish ITEM            the step-by-step for one item
    ./securax finish done ITEM       mark an item you did outside the estate (GitHub, Cloudflare, Azure, a phone)
    ./securax finish undo ITEM       un-mark it

Items the estate can check (a file, a setting in .env) tick themselves; the others are ticked by you, once, in
vault/finish.json (private). Domain, repository and brand come from brand.env, so the steps follow a new domain by themselves.
Exit codes: 0 ok, 2 bad usage.
"""
from __future__ import annotations

import datetime as dt
import html
import importlib.util
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARKS = ROOT / "vault" / "finish.json"
ENVF = ROOT / "local" / "compose" / ".env"


def _brand() -> dict[str, str]:
    spec = importlib.util.spec_from_file_location("config", pathlib.Path(__file__).resolve().parent / "config.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.values()


def env(name: str) -> str:
    """The process environment wins, then local/compose/.env (the same order as the securax wrapper's ev)."""
    if os.environ.get(name):
        return os.environ[name]
    try:
        m = re.search(rf"^{re.escape(name)}=(.*)$", ENVF.read_text("utf-8"), re.M)
        return m.group(1).strip() if m else ""
    except OSError:
        return ""


def items(b: dict[str, str] | None = None) -> list[dict]:
    """Ordered by value for effort. `check` returns True when done (None: only you can tell, so it is ticked by hand)."""
    b = b or _brand()
    dom = b.get("SITE_DOMAIN") or "your-domain.example"
    owner, _, repo = (b.get("REPO_SLUG") or "owner/repo").partition("/")
    pages = f"https://{owner}.github.io/{repo}/"
    return [
        {"id": "control-library", "title": "See the BFSI control matrix", "gives": "the control navigator, the heat map and the vital-few list",
         "check": lambda: (ROOT / "portal" / "navigator.html").exists(),
         "steps": ["Run  ./securax go  : it builds the matrix from the built-in starter library. No file needed.",
                   "Open the Command Center → BFSI controls.",
                   "Optional: if your organisation has its own gap-assessment workbook (.xlsx), save it in Downloads; the next  ./securax go  uses it instead."]},
        {"id": "backup-key", "title": "Encrypt every backup", "gives": "backups that are safe to copy off the laptop",
         "check": lambda: bool(env("SECURAX_BACKUP_KEYFILE")),
         "steps": ["Plug in a USB stick if you have one (or have your password manager open).",
                   "Run  ./securax protect  : it makes the key, saves a second copy where you say, switches encryption on and proves a backup opens.",
                   "Keep that second copy away from the laptop: without the key nobody, including you, can open the backups."]},
        {"id": "offsite-backup", "title": "Copy backups off the laptop (OneDrive)", "gives": "a copy that survives a lost or broken laptop, with a quarterly restore drill",
         "check": lambda: bool(env("SECURAX_OFFSITE_DIR")),
         "steps": ["Do 'Encrypt every backup' first: only encrypted backups leave the machine.",
                   "Run  ./securax backup offsite  and pick your OneDrive folder from the list.",
                   "Nothing else: every backup is copied and checked, and  ./securax backup drill  runs each quarter."]},
        {"id": "phone-alerts", "title": "Phone alerts", "gives": "a nudge on your phone when something needs you",
         "check": lambda: bool(env("SECURAX_NOTIFY_NTFY") or env("SECURAX_NOTIFY_WEBHOOK")),
         "steps": ["Install the ntfy app on your phone.", "Run  ./securax notify setup  and follow the two prompts.",
                   "Run  ./securax notify test  : your phone should buzz."]},
        {"id": "risk-register", "title": "Import your risk register", "gives": "the navigator ranks the controls that treat your biggest open risks",
         "check": lambda: (ROOT / "vault" / "risks" / "register.json").exists(),
         "steps": ["Save the risk register workbook(s) in Downloads.", "Run  ./securax risks import  and answer Y."]},
        {"id": "product-site", "title": "Publish the product site (free, GitHub Pages)", "gives": f"the public site and docs at {pages}",
         "check": None,
         "steps": [f"On GitHub open {owner}/{repo} → Settings → Pages → Build and deployment → Source: GitHub Actions.",
                   "Settings → Secrets and variables → Actions → Variables → New repository variable: name SITE_PAGES, value true.",
                   "Actions → docs → Run workflow (branch main). About 3 minutes.",
                   f"Open {pages}  then mark it:  ./securax finish done product-site"]},
        {"id": "own-domain", "title": f"Put the site on {dom}", "gives": "your own address; changing it later is one value, not a rebuild",
         "check": None,
         "steps": [f"GitHub → Settings → Pages → Custom domain: {dom} → Save.",
                   f"Cloudflare → {dom} → DNS: four A records for @ pointing to 185.199.108.153, 185.199.109.153, 185.199.110.153 and "
                   f"185.199.111.153, plus CNAME www → {owner}.github.io; proxy OFF (grey cloud) on all five. (GitHub's current list: docs.github.com → Pages → custom domain.)",
                   f"GitHub → your profile Settings → Pages → Add a verified domain → {dom} (one TXT record; stops anyone else claiming it).",
                   "Wait for GitHub to show 'DNS check successful' (minutes to an hour), then tick Enforce HTTPS.",
                   "To move to another domain later: change SITE_DOMAIN in brand.env (or the repository variable SITE_DOMAIN) and repeat these 3 steps.",
                   "Mark it:  ./securax finish done own-domain"]},
        {"id": "life-os-hosting", "title": "Host the Life OS off the laptop (Cloudflare Pages + Access)", "gives": "install and update the app on any device with the laptop off",
         "check": None,
         "steps": ["Cloudflare → Workers & Pages → Create → Pages → Connect to Git → this repository.",
                   "Production branch main, framework None, build command empty, output directory guiding-map.",
                   f"Custom domains → add life.{dom}",
                   f"Zero Trust → Access → Applications → Add → Self-hosted → life.{dom}; policy: allow your e-mail only. Also protect preview deployments.",
                   "Do the Azure item next, then:  ./securax finish done life-os-hosting"]},
        {"id": "azure-redirects", "title": "Let Microsoft sign-in return to every app address", "gives": "Microsoft 365 and OneDrive sync work wherever you open the Life OS",
         "check": None,
         "steps": ["Azure portal → App registrations → your Life OS app → Authentication → Single-page application.",
                   "Add each address you open the app from, twice: with / at the end and with /index.html at the end "
                   f"(for example https://life.{dom}/ and https://life.{dom}/index.html, and the laptop address).",
                   "Save, then:  ./securax finish done azure-redirects"]},
        {"id": "onedrive-sync", "title": "Sync every device through OneDrive (end-to-end encrypted)", "gives": "phone and laptop stay in step with the laptop switched off",
         "check": None,
         "steps": ["On each device open the Life OS → Ops → Connections → Microsoft 365 → Connect.",
                   "Choose 'Turn on OneDrive sync' and enter the SAME passphrase (12+ characters) on every device. Keep it in your password manager.",
                   "Mark it once all devices are on:  ./securax finish done onedrive-sync"]},
    ]


def marks() -> dict:
    try:
        return json.loads(MARKS.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def status(its: list[dict] | None = None) -> list[dict]:
    m, out = marks(), []
    for it in its or items():
        auto = it["check"]() if it["check"] else None
        out.append({**it, "done": bool(auto) or it["id"] in m, "how": "checked" if auto else ("by you " + m[it["id"]] if it["id"] in m else "")})
    return out


def html_card(st: list[dict] | None = None, panel: bool = False) -> str:
    """The Command Center card: what is left first, each with its numbered steps; finished ones folded away."""
    E = html.escape
    st = status() if st is None else st
    left, done = [s for s in st if not s["done"]], [s for s in st if s["done"]]

    def one(s, open_=False):
        steps = "".join(f"<li>{E(x.replace('https://', ''))}</li>" for x in s["steps"])   # the cockpit names no external URL
        return (f"<details{' open' if open_ else ''}><summary><b>{'✔' if s['done'] else '○'} {E(s['title'])}</b> "
                f"<span class='muted'>· {E(s['gives'].replace('https://', ''))}</span></summary><ol>{steps}</ol></details>")
    if panel:   # folded to one line in the cockpit: the steps are there, one click away, never in the pilot's face
        nxt = f" · next: {E(left[0]['title'])}" if left else " · everything is set up"
        h = [f"<details class='card panel' id='finish'><summary><b>Setup</b> <span class='muted'>· {len(done)} of {len(st)} optional steps done{nxt}</span></summary>"]
    else:
        h = [f"<div class='card'><h2>Finish setting up <span class='muted'>· {len(done)} of {len(st)} done · all optional, do one when you have time</span></h2>"]
    if left:
        h.append("<p class='muted'>Next: <b>" + E(left[0]["title"]) + "</b>. Or in the terminal: <code>./securax finish</code></p>")
        h += [one(s, i == 0) for i, s in enumerate(left)]
    else:
        h.append("<p class='big'>Everything is set up.</p>")
    if done:
        h.append(f"<details><summary class='muted'>{len(done)} done</summary>" + "".join(one(s) for s in done) + "</details>")
    return "".join(h) + ("</details>" if panel else "</div>")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    st = status()
    ids = [s["id"] for s in st]
    if argv and argv[0] in ("done", "undo"):
        if len(argv) != 2 or argv[1] not in ids:
            print("items: " + ", ".join(ids))
            return 2
        m = marks()
        if argv[0] == "done":
            m[argv[1]] = dt.date.today().isoformat()
        else:
            m.pop(argv[1], None)
        MARKS.parent.mkdir(parents=True, exist_ok=True)
        MARKS.write_text(json.dumps(m, indent=1), "utf-8")
        print(f"✔ {argv[1]} {'marked done' if argv[0] == 'done' else 'un-marked'}")
        return 0
    if argv:
        s = next((s for s in st if s["id"] == argv[0]), None)
        if not s:
            print("items: " + ", ".join(ids))
            return 2
        print(f"{s['title']}: {s['gives']}" + (f"  (done, {s['how']})" if s["done"] else ""))
        for i, x in enumerate(s["steps"], 1):
            print(f"  {i}. {x}")
        return 0
    left = [s for s in st if not s["done"]]
    print(f"Finish setting up: {len(st) - len(left)} of {len(st)} done (all optional).")
    for s in st:
        print(f"  {'✔' if s['done'] else '○'} {s['id']:<16} {s['title']}")
    if left:
        print(f"\nNext: {left[0]['title']}  ({left[0]['gives']})")
        for i, x in enumerate(left[0]["steps"], 1):
            print(f"  {i}. {x}")
        print("\nAny item's steps:  ./securax finish ITEM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
