#!/usr/bin/env python3
"""The project's memory across sessions and agents: LESSONS.md, one line per lesson, read by every builder.

    ./securax lessons                         the lessons, newest last
    ./securax lessons add "what happened → what to do instead" [--area AREA]
    ./securax lessons recent [N]              the newest N (default 15), for a brief

The same idea as claude-mem (carry what was learned into the next session), done without a model call: autobuild adds a
line when a red attempt turns green, people add one when a check surprises them, and AGENTS.md tells every agent to read it.
Lines are cleaned before they are stored (one line, no markup, at most 220 characters), because every agent reads this
file as context: a failure message must not become an instruction. Exit codes: 0 ok, 2 bad usage.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILE = ROOT / "LESSONS.md"
START, END = "<!-- lessons:start -->", "<!-- lessons:end -->"
KEEP = 200                                                     # oldest lines drop off: the file stays cheap to read


def clean(text: str, limit: int = 220) -> str:
    """One plain line: no markup, links, code fences or control characters (it is fed to agents as context)."""
    t = re.sub(r"[\x00-\x1f\x7f]+", " ", str(text))
    t = re.sub(r"<[^>]*>|```+|`|\[|\]|\(https?://[^)]*\)", "", t)
    t = re.sub(r"\s+", " ", t).strip(" -*#>")
    return t[:limit].rstrip() + ("…" if len(t) > limit else "")


def read(path: pathlib.Path | None = None) -> list[str]:
    try:
        text = (path or FILE).read_text("utf-8")
    except OSError:
        return []
    body = text.split(START, 1)[1].split(END, 1)[0] if START in text and END in text else ""
    return [ln[2:] for ln in body.splitlines() if ln.startswith("- ")]


def add(lesson: str, area: str = "", path: pathlib.Path | None = None, today: str | None = None) -> bool:
    """Append a lesson; False if it is empty or already there (the same lesson twice teaches nothing)."""
    path = path or FILE
    msg = clean(lesson)
    if not msg:
        return False
    key = re.sub(r"\W+", " ", msg.lower()).strip()
    lines = read(path)
    if any(key in re.sub(r"\W+", " ", ln.lower()) for ln in lines):
        return False
    lines = (lines + [f"{today or dt.date.today().isoformat()} {clean(area, 20) + ': ' if area else ''}{msg}"])[-KEEP:]
    try:
        text = path.read_text("utf-8")
    except OSError:
        text = f"# LESSONS.md: what went wrong before, so it does not again\n\n{START}\n{END}\n"
    head, rest = text.split(START, 1) if START in text else (text.rstrip() + "\n\n", END + "\n")
    tail = rest.split(END, 1)[1] if END in rest else "\n"
    path.write_text(head + START + "\n" + "".join(f"- {ln}\n" for ln in lines) + END + tail, "utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["add"]:
        area, words, it = "", [], iter(argv[1:])
        for a in it:
            if a == "--area":
                area = next(it, "")
            else:
                words.append(a)
        if not words:
            print('usage: ./securax lessons add "what happened → what to do instead" [--area AREA]')
            return 2
        print("✔ lesson added to LESSONS.md" if add(" ".join(words), area) else "(already there, or empty: nothing added)")
        return 0
    lines = read()
    if argv[:1] == ["recent"]:
        n = int(argv[1]) if len(argv) > 1 and argv[1].isdigit() else 15
        lines = lines[-n:]
    elif argv:
        print(__doc__)
        return 2
    print("\n".join(f"- {ln}" for ln in lines) if lines else "No lessons yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
