"""Synthetic people (queue synthetic-people, slice 1): three goals in plain words, a 375 px phone, and a brain that picks the
visible control whose words best match the goal. The browser part skips when Chromium or playwright is not installed."""
import importlib.util
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("synthetic_users", ROOT / "sandbox" / "synthetic_users.py")
su = importlib.util.module_from_spec(_s)
_s.loader.exec_module(su)


def test_brain_ranks_the_control_whose_words_best_match_first():
    controls = [{"role": "button", "name": "Renewed"}, {"role": "button", "name": "Deep Friendships"},
                {"role": "button", "name": "Add this renewal"}, {"role": "button", "name": "Yes"}]
    ranked = su.rank("add the ISC2 annual fee with a date", controls)
    assert ranked[0]["name"] == "Add this renewal"
    assert su.rank("answer the due call: did it happen? yes", controls)[0]["name"] == "Yes"


def test_chromium_path_points_at_a_browser_when_installed(monkeypatch):
    monkeypatch.delenv("PLAYWRIGHT_CHROMIUM", raising=False)
    if not pathlib.Path("/opt/pw-browsers/chromium").exists():
        return
    found = pathlib.Path(su.chromium_path())
    assert found.is_file()


def test_without_chromium_the_command_says_skip(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(su, "chromium_path", lambda: "")
    monkeypatch.setattr("sys.argv", ["synthetic_users.py", str(tmp_path / "out")])
    assert su.main() == 0
    assert "SYNTHETIC USERS: SKIP" in capsys.readouterr().out


def test_without_playwright_the_command_says_skip(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(su, "has_playwright", lambda: False)
    monkeypatch.setattr("sys.argv", ["synthetic_users.py", str(tmp_path / "out")])
    assert su.main() == 0
    out = capsys.readouterr().out
    # Either honest reason may come first (no Playwright package, or no Chromium for it); both name Playwright.
    assert "SYNTHETIC USERS: SKIP" in out and "playwright" in out.lower()


def test_success_is_false_while_the_text_to_avoid_is_still_visible(monkeypatch):
    monkeypatch.setattr(su, "_text_visible", lambda page, text: True)
    assert su.success(object(), {"absent": "did it happen?"}) is False


def test_every_goal_has_words_a_start_tab_a_success_check_and_at_most_15_steps():
    goals = su.load_goals()["goals"]
    assert len(goals) == 3
    for goal in goals:
        assert str(goal.get("words") or "").strip(), goal.get("id")
        assert str(goal.get("start_tab") or "").strip(), goal.get("id")
        assert goal.get("success"), goal.get("id")
        assert 1 <= int(goal.get("max_steps") or 0) <= 15, goal.get("id")


def test_three_goals_reach_on_a_375_px_phone(tmp_path):
    out = tmp_path / "synthetic-users"
    rc = subprocess.run([sys.executable, str(ROOT / "sandbox" / "synthetic_users.py"), str(out)], cwd=ROOT,
                        capture_output=True, text=True, timeout=240)
    assert rc.returncode == 0, rc.stdout + rc.stderr
    if not su.chromium_path() or not su.has_playwright():
        assert "SYNTHETIC USERS: SKIP" in rc.stdout
        return
    report = json.loads((out / "report.json").read_text())
    assert (out / "summary.md").read_text().count("|") >= 6
    assert [g["id"] for g in report["goals"]] == [g["id"] for g in su.load_goals()["goals"]]
    for g in report["goals"]:
        assert g["reached"] is True, (g["id"], g.get("dead_ends"))
        assert isinstance(g["steps"], list) and 1 <= len(g["steps"]) <= 8
        assert g["wrong_taps"] == [] and g["dead_ends"] == []
    by_id = {g["id"]: g for g in report["goals"]}
    assert by_id["due-call"]["steps"][0]["control"] == "Yes"
    assert by_id["isc2-fee"]["steps"][0]["role"] == "combobox"
    assert "ISC2" in by_id["isc2-fee"]["steps"][0]["typed"]
    typed = {s.get("typed") for s in by_id["friend-names"]["steps"]}
    assert {"Asha", "Bela", "Chitra", "Dia", "Esha"} <= typed
