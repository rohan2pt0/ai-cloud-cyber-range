"""Write each page's status light (from docs/status.yml) into a banner under its title.

    python3 docs/sync_status.py           # update the pages
    python3 docs/sync_status.py --check   # exit 1 if any page disagrees with status.yml (CI)
"""
import os
import pathlib
import re
import sys

import yaml

DOCS = pathlib.Path(__file__).resolve().parent
LIGHT = {"green": ("🟢", "Built"), "amber": ("🟡", "Partly built"), "red": ("🔴", "Not built yet")}
START, END = "<!-- status:start", "<!-- status:end -->"
RX = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)


def banner(status: str, note: str, legend: str) -> str:
    dot, word = LIGHT[status]
    return (f"{START} (from docs/status.yml; edit that file, then run docs/sync_status.py) -->\n"
            f"> **Status: {dot} {word}.** {note} [What the lights mean]({legend})\n"
            f"{END}\n")


def render(text: str, status: str, note: str, legend: str = "index.md#the-status-lights") -> str:
    text = RX.sub("", text)
    lines = text.split("\n")
    i = next((n for n, ln in enumerate(lines) if ln.startswith("# ")), -1)
    if i < 0:
        return banner(status, note, legend) + "\n" + text
    return "\n".join(lines[: i + 1]) + "\n\n" + banner(status, note, legend) + "\n" + "\n".join(lines[i + 1:]).lstrip("\n")


END_STATE = DOCS / "securax/59-END-STATE-ARCHITECTURE.md"


def glance_problems() -> list[str]:
    """The 'At a glance' totals on doc 59 must equal the lights counted in its layer tables."""
    text = END_STATE.read_text()
    glance = re.search(r"## At a glance\n(.*?)\n## ", text, re.S).group(1)
    want = {}
    for row in glance.splitlines():
        if not row.startswith("| ") or row.startswith("| Layer"):
            continue
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) == 4:
            want[cells[0].split(" ")[0]] = tuple(int(c) for c in cells[1:])
    got = {}
    for sec in re.split(r"\n## ", text):
        title = sec.split("\n", 1)[0]
        lights = [r.split("|")[2].strip() for r in sec.splitlines() if r.startswith("| ") and not r.startswith(("| Box", "|---"))]
        lights = [x for x in lights if x in ("🟢", "🟡", "🔴")]
        if lights:
            got[title.split(" ")[0]] = tuple(lights.count(k) for k in ("🟢", "🟡", "🔴"))
    return [f"doc 59 'At a glance' row {k!r}: says {v}, the table counts {got.get(k)}" for k, v in want.items() if got.get(k) != v]


def main(check: bool) -> int:
    table = yaml.safe_load((DOCS / "status.yml").read_text())
    bad = []
    for rel, (status, note) in table.items():
        if status not in LIGHT:
            bad.append(f"{rel}: unknown status {status!r}")
            continue
        page = DOCS / rel
        if not page.exists():
            bad.append(f"{rel}: listed in status.yml but missing")
            continue
        old = page.read_text()
        legend = os.path.relpath(DOCS / "index.md", page.parent).replace(os.sep, "/") + "#the-status-lights"
        new = render(old, status, note, legend)
        if new != old:
            if check:
                bad.append(f"{rel}: banner out of date (run python3 docs/sync_status.py)")
            else:
                page.write_text(new)
    bad += glance_problems()
    for b in bad:
        print(b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
