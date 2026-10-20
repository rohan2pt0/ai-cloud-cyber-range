"""The task brief points a model at the right files, the lessons that apply and the checks for those files, and never at private or
generated files."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("brief", ROOT / "lifecycle" / "brief.py")
br = importlib.util.module_from_spec(_s)
_s.loader.exec_module(br)


def test_the_words_people_use_find_the_file_that_holds_the_part():
    cases = {"add a tab to the Life OS phone navigation": "guiding-map/ops.js",
             "fix the sync token check in estate-sync": "apps/estate-sync/syncsvc/main.py",
             "the continuity mirror refuses a shallow checkout": "governance/continuity.py",
             "a routine that nudges me at 9pm": "routines/scheduler.py",
             "the gateway should mask a new kind of PII": "apps/llm-gateway/app/main.py"}
    for task, want in cases.items():
        got = [f["path"] for f in br.build(task)["files"]][:3]
        assert want in got, (task, got)


def test_checks_follow_the_files_and_lessons_share_the_tasks_words():
    b = br.build("add a tab to the Life OS phone navigation")
    assert any("npm test" in c for c in b["checks"]) and any("ruff check" in c for c in b["checks"])
    assert any("npm test" in x or "tab" in x for x in b["lessons"])
    md = br.markdown(b)
    assert md.startswith("# Task") and "Write or extend the test first" in md and "# Done means" in md


def test_private_and_generated_files_are_never_listed():
    for f in br.tracked():
        assert not f.startswith(("vault/", "local/compose/.env", "website/docs/")) and f != "guiding-map/index.html", f


def test_every_alias_points_at_a_file_that_exists():
    import json
    table = json.loads((ROOT / "lifecycle" / "brief.json").read_text())["aliases"]
    for keys, paths in table.items():
        for p in paths:
            assert (ROOT / p).exists(), (keys, p)
