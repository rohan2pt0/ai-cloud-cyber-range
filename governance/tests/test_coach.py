"""The one-next-step coach: the single command a non-technical owner must remember tells them exactly what to do now."""
import importlib.util
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("coach", REPO / "governance" / "coach.py")
coach = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coach)


def test_not_running_is_the_first_thing_and_points_at_go():
    c = coach.coach(up=False)
    assert c["stage"] == "not-running" and c["cmd"] == "./securax go"
    assert "./securax next" in coach.render(c)          # always teaches the one command to remember


def test_running_but_no_data_asks_for_the_life_import(monkeypatch):
    monkeypatch.setattr(coach, "life_data_in", lambda: False)
    c = coach.coach(up=True)
    assert c["stage"] == "no-data" and "lifeos import workbook" in c["cmd"]


def test_running_with_data_sends_you_to_the_app_and_names_an_optional_step(monkeypatch):
    monkeypatch.setattr(coach, "life_data_in", lambda: True)
    monkeypatch.setattr(coach, "next_finish_item", lambda: {"id": "offsite-backup", "title": "Copy backups off the laptop", "gives": "a copy that survives a lost laptop"})
    c = coach.coach(up=True)
    assert c["stage"] == "ready" and c["app_url"] in c["step"]
    assert c["optional"] and "./securax finish offsite-backup" in c["optional"]


def test_ready_with_everything_done_has_no_optional_nag(monkeypatch):
    monkeypatch.setattr(coach, "life_data_in", lambda: True)
    monkeypatch.setattr(coach, "next_finish_item", lambda: None)
    c = coach.coach(up=True)
    assert c["stage"] == "ready" and c["optional"] is None


def test_the_plain_output_names_no_raw_localhost_when_names_are_on(monkeypatch):
    # With names on, the app address is a name, not localhost:PORT (fitness no-raw-addresses).
    monkeypatch.setattr(coach, "app_url", lambda: "https://hub.securax.localhost/")
    monkeypatch.setattr(coach, "life_data_in", lambda: True)
    monkeypatch.setattr(coach, "next_finish_item", lambda: None)
    assert "localhost:8088" not in coach.render(coach.coach(up=True))
