"""Ship (doc 98): the pull-request loop without Claude Code. Red, pending and green are told apart (no checks is never
green); the failure brief carries the telling log lines and the never-weaken rule, privately; a green, mergeable PR is
merged and a conflicted or red one is not; the PR body follows the repository's template without its instructions."""
import importlib.util
import os
import pathlib
import stat

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("ship", ROOT / "lifecycle" / "ship.py")
sh = importlib.util.module_from_spec(_s)
_s.loader.exec_module(sh)


def run(name, status="completed", conclusion="success", i=1):
    return {"name": name, "status": status, "conclusion": conclusion, "id": i, "html_url": f"https://example.invalid/{i}"}


def test_red_pending_and_green_are_told_apart():
    assert sh.classify([])["state"] == "pending"                       # nothing reported yet is never green
    assert sh.classify([run("lint"), run("sandbox", "in_progress", None)])["state"] == "pending"
    r = sh.classify([run("lint"), run("app-tests", conclusion="failure", i=7), run("publish", conclusion="skipped")])
    assert r["state"] == "red" and r["red"][0]["name"] == "app-tests"
    assert sh.classify([run("lint"), run("publish", conclusion="skipped"), run("x", conclusion="neutral")])["state"] == "green"


def _st(state="red", mergeable="clean", red=None):
    red = red if red is not None else ([{"name": "app-tests", "id": 7, "url": "u"}] if state == "red" else [])
    return {"pr": {"title": "A change"}, "checks": {"state": state, "pending": [], "red": red, "total": 3}, "sha": "abc1234def",
            "mergeable": mergeable, "merged": False, "open": True, "branch": "feature", "base": "main"}


def test_the_brief_is_private_and_carries_the_rule(monkeypatch, tmp_path):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    log = "\n".join(["2026-10-21T10:00:00.0Z setup ok"] * 50 + ["2026-10-21T10:00:01.0Z FAILED tests/test_x.py::test_y - AssertionError: 2 != 3"])
    p = sh.brief(12, _st(), {"app-tests": log}, 1)
    text = p.read_text()
    assert "FAILED tests/test_x.py::test_y" in text and "Never skip, disable or weaken a test" in text
    assert "2026-10-21T10" not in text                                  # timestamps stripped
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o600 and str(tmp_path) in str(p)


def test_green_and_mergeable_is_merged_red_and_conflicted_are_not(monkeypatch, tmp_path):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    merged = []
    monkeypatch.setattr(sh, "merge", lambda n, st: merged.append(n))
    monkeypatch.setattr(sh, "failing_logs", lambda st: {})
    monkeypatch.setattr(sh, "tell", lambda m: None)
    monkeypatch.setattr(sh, "pr_state", lambda n: _st("green"))
    assert sh.watch(5, 0, True, True, 15, 1) == 0 and merged == [5]
    monkeypatch.setattr(sh, "pr_state", lambda n: _st("green", "blocked"))
    assert sh.watch(6, 0, True, True, 15, 1) == 0 and merged == [5]      # waits on people: never pushed or merged
    monkeypatch.setattr(sh, "pr_state", lambda n: _st("red"))
    assert sh.watch(7, 0, True, True, 15, 1) == 1 and merged == [5]
    assert (tmp_path / "ship" / "pr7-round1.md").exists()
    monkeypatch.setattr(sh, "pr_state", lambda n: _st("green", "dirty"))
    assert sh.watch(8, 0, True, True, 15, 1) == 1 and merged == [5]


def test_a_red_pr_gets_bounded_fix_rounds(monkeypatch, tmp_path):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    calls = []
    monkeypatch.setattr(sh, "pr_state", lambda n: _st("red"))
    monkeypatch.setattr(sh, "failing_logs", lambda st: {})
    monkeypatch.setattr(sh, "tell", lambda m: None)
    monkeypatch.setattr(sh, "fix_round", lambda n, st, a: calls.append(a) or True)
    assert sh.watch(9, 2, False, True, 15, 1) == 0 and calls == [1]     # once: one round, then the next pass sees CI
    assert sh.watch(9, 2, False, True, 15, 1) == 0 and calls == [1, 2]
    assert sh.watch(9, 2, False, True, 15, 1) == 1 and calls == [1, 2]  # the limit holds: a brief for a person instead


def test_the_body_follows_the_template_without_its_instructions(monkeypatch):
    monkeypatch.setattr(sh, "git", lambda *a, check=True: "- one change" if a[0] == "log" else "base")
    body = sh.body_from_template("A change")
    assert "## What & why" in body and "- one change" in body and "<!--" not in body
    assert body.rstrip().endswith("Assisted-by: SecuRAX open models")


def test_no_token_is_a_clear_setup_step(monkeypatch, tmp_path):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    out = []
    assert sh.check(say=out.append) == 1
    assert any("ship login" in o for o in out)
    try:
        sh.api("GET", "/user")
        raise AssertionError("expected a setup error")
    except sh.ShipError as e:
        assert "ship login" in str(e)


def test_after_a_merge_the_branch_starts_from_the_base_and_tracks_itself(monkeypatch, tmp_path):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    calls = []

    def fake_git(*a, check=True):
        calls.append(a)
        return "feature" if a[:2] == ("rev-parse", "--abbrev-ref") else ""
    monkeypatch.setattr(sh, "git", fake_git)
    monkeypatch.setattr(sh, "api", lambda *a, **k: {})
    monkeypatch.setattr(sh, "tell", lambda m: None)
    sh.merge(4, _st("green"))
    assert ("checkout", "-q", "-B", "feature", "origin/main") in calls
    push = [c for c in calls if c[0] == "push"][0]
    assert "-u" in push and "--force-with-lease" in push and push[-1] == "feature"
