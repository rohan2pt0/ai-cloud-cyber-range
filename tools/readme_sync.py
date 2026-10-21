#!/usr/bin/env python3
"""Keep README.md current without anyone remembering to: the version badge, "What's new" and the documentation index are
written from their sources of truth (VERSION, CHANGELOG.md, docs/securax/*.md + docs/status.yml).

    python3 tools/readme_sync.py           rewrite the generated parts of README.md
    python3 tools/readme_sync.py --check   exit 1 when README.md is behind (the readme-current fitness check runs this in CI)

Only the parts between <!-- readme:NAME:start --> and <!-- readme:NAME:end --> are generated; the rest is written by people.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
LIGHT = {"green": "🟢", "amber": "🟡", "red": "🔴"}


def _titles(section: str, limit: int) -> list[str]:
    """Top-level changelog bullets as one line each: the bold title, plus its doc link when it names one."""
    out = []
    for line in section.splitlines():
        m = re.match(r"- \*\*(.+?)\*\*(.*)", line)
        if not m:
            continue
        title = m.group(1).rstrip(":").rstrip(".")
        doc = re.search(r"\(doc (\d+)", m.group(1) + m.group(2))
        if doc:
            hit = next(iter(sorted((ROOT / "docs" / "securax").glob(f"{int(doc.group(1)):02d}-*.md"))), None)
            if hit:
                title = f"[{title}](docs/securax/{hit.name})"
        out.append(f"- {title}")
        if len(out) >= limit:
            break
    return out


def whats_new() -> str:
    log = (ROOT / "CHANGELOG.md").read_text("utf-8")
    parts = re.split(r"^## ", log, flags=re.M)
    unreleased = next((p for p in parts if p.startswith("[Unreleased]")), "")
    release = next((p for p in parts if re.match(r"\[\d+\.\d+\.\d+\]", p)), "")
    name = release.split("\n", 1)[0].strip() if release else ""
    lines = ["## What's new", ""]
    nxt = _titles(unreleased, 8)
    if nxt:
        lines += ["**On main, in the next release:**", ""] + nxt + [""]
    if release:
        lines += [f"**{name.replace('[', 'Release ').replace(']', '')}:**", ""] + _titles(release, 10) + [""]
    lines.append("Everything, with details: [`CHANGELOG.md`](CHANGELOG.md).")
    return "\n".join(lines)


def docs_index() -> str:
    import yaml

    status = yaml.safe_load((ROOT / "docs" / "status.yml").read_text("utf-8")) or {}
    rows = []
    for p in sorted((ROOT / "docs" / "securax").glob("[0-9][0-9]-*.md")):
        head = next((ln[2:].strip() for ln in p.read_text("utf-8").splitlines() if ln.startswith("# ")), p.stem)
        head = re.sub(r"^\d+\s*[·—-]\s*", "", head)
        light = LIGHT.get((status.get(f"securax/{p.name}") or [""])[0], "")
        rows.append(f"[{head}](docs/securax/{p.name}){(' ' + light) if light else ''}")
    return ("## All documentation\n\n" + " · ".join(rows) + "\n\n🟢 built · 🟡 partly built · 🔴 not built yet "
            "([what the lights mean](docs/index.md#the-status-lights))")


def badge() -> str:
    v = (ROOT / "VERSION").read_text("utf-8").strip()
    return f"[![Version](https://img.shields.io/badge/version-{v.replace('-', '--')}-blue)](CHANGELOG.md)"


def proofs() -> str:
    n = len(re.findall(r"^@journey\(", (ROOT / "sandbox" / "run.py").read_text("utf-8"), re.M))
    return (f"> **Proof, not claims:** {n} end-to-end journeys run the real estate (real containers, a real browser) on every merge "
            "and every night; pull requests run the ones their change can affect ([doc 68](docs/securax/68-CI-AT-AGENT-SCALE.md)).")


def site() -> str:
    """The site and docs links, from the one site address (doc 99): your domain once live, GitHub Pages until then."""
    sys.path.insert(0, str(ROOT / "governance"))
    import config
    url = config.values()["SITE_URL"]
    if not url:
        return "> 📘 **Documentation:** in [`docs/`](docs/index.md). Every page is listed under [All documentation](#all-documentation) below."
    shown = url.split("://", 1)[1].rstrip("/")
    return (f"> 🌐 **Product site:** [{shown}]({url}) · 📘 **Documentation:** [{shown}/docs]({url}docs/) (source in `docs/`, "
            "built by `mkdocs.yml`). Every page is listed under [All documentation](#all-documentation) below.")


PARTS = {"badge": badge, "site": site, "whats-new": whats_new, "docs": docs_index, "proofs": proofs}


def render(text: str) -> str:
    for name, fn in PARTS.items():
        rx = re.compile(rf"(<!-- readme:{name}:start -->\n)(?:.*?\n)?(<!-- readme:{name}:end -->)", re.S)
        if not rx.search(text):
            raise SystemExit(f"README.md has no <!-- readme:{name}:start --> ... <!-- readme:{name}:end --> block")
        text = rx.sub(lambda m: m.group(1) + fn() + "\n" + m.group(2), text)
    return text


def main(argv: list[str]) -> int:
    cur = README.read_text("utf-8")
    new = render(cur)
    if "--check" in argv:
        if new != cur:
            print("README.md is behind VERSION / CHANGELOG.md / docs: run  python3 tools/readme_sync.py")
            return 1
        return 0
    README.write_text(new, "utf-8")
    print("README.md: generated parts are current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
