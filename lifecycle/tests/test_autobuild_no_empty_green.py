"""An autobuild attempt whose only change is the lesson the loop writes itself must never count as green.

2026-11-18: two open-model runs (#346, #351) came back GREEN with nothing but one LESSONS.md line, because the loop
wrote its "went red, then green" lesson before checking whether the attempt changed anything. A test never runs the
script (its success path builds and pushes), so this reads the order in the script text (LESSONS.md, 2026-11-16).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _autobuild_text():
    t = (ROOT / "securax").read_text(encoding="utf-8")
    start = t.index("An attempt that changed nothing proves nothing")
    return t[start - 400 : start + 2500]


def test_the_no_change_check_ignores_lessons():
    block = _autobuild_text()
    check = block[block.index("if git -C \"$ROOT\" diff --cached --quiet"):]
    first_line = check.splitlines()[0]
    assert ":(exclude)LESSONS.md" in first_line, first_line


def test_the_lesson_is_written_only_after_a_real_change():
    block = _autobuild_text()
    assert block.index("made no change: not green") < block.index('lessons.py" add --area autobuild')
