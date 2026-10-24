"""Visible progress (doc 93): the Life OS rhythm is read from the real synced data shape, a slipped rhythm gets one gentle
two-minute nudge, only what really ran is counted, and there is always one next step. No network."""
import datetime as dt
import importlib.util
import json
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("progress", ROOT / "governance" / "progress.py")
pg = importlib.util.module_from_spec(_s)
_s.loader.exec_module(pg)
NOW = time.time()


def day(n: int) -> str:
    return (dt.date.today() - dt.timedelta(days=n)).isoformat()


def state(checkin_days, review_ago=None, quarter_ago=None):
    """The shape the Life OS syncs: localStorage keys, values as JSON text, meta as per-key milliseconds."""
    payload = {"gm_energy": json.dumps({day(n): 4 for n in checkin_days}), "gm_notes": "{}"}
    meta = {"gm_energy": (NOW - min(checkin_days or [99]) * 86400) * 1000}
    if review_ago is not None:
        payload["gm_week_review"] = "{}"
        meta["gm_week_review"] = (NOW - review_ago * 86400) * 1000
    if quarter_ago is not None:
        payload["gm_quarter_done"] = "1"
        meta["gm_quarter_done"] = (NOW - quarter_ago * 86400) * 1000
    return {"payload": payload, "meta": meta}


def test_the_rhythm_is_read_from_the_real_synced_shape():
    r = pg.rhythm(state([0, 1, 2, 10, 40], review_ago=3, quarter_ago=20), NOW)
    assert r["checkins_7d"] == 3 and r["checkins_30d"] == 4
    assert round(r["last_week_review_days"]) == 3 and round(r["last_quarter_days"]) == 20
    assert pg.nudges(r) == [], "a healthy rhythm gets no nagging"


def test_a_slipped_rhythm_gets_gentle_specific_nudges():
    r = pg.rhythm(state([12], review_ago=20, quarter_ago=120), NOW)
    n = " ".join(pg.nudges(r))
    assert "two minutes" in n and "weekly review" in n and "quarterly check-in" in n
    assert pg.nudges(pg.rhythm(None, NOW))[0].startswith("Open the Life OS")


def test_only_what_really_ran_is_counted(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    (tmp_path / "continuity").mkdir()
    (tmp_path / "autopilot").mkdir()
    recent = dt.datetime.now().isoformat(timespec="seconds")
    old = (dt.datetime.now() - dt.timedelta(days=45)).isoformat(timespec="seconds")
    (tmp_path / "continuity" / "drills.jsonl").write_text("\n".join(json.dumps(x) for x in (
        {"id": "data-lost", "when": recent, "ok": True}, {"id": "github-down", "when": old, "ok": True},
        {"id": "bad-change", "when": recent, "ok": False})) + "\n")
    (tmp_path / "autopilot" / "learned.json").write_text(json.dumps({"a": {"open": False}, "b": {"open": True}}))
    (tmp_path / "drills.log").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) + " drill ok securax-x.tar.gz.gpg\n")
    s = pg.stronger(NOW)
    assert s["drills_passed"] == 1 and s["drills_failed"] == 1, "a drill older than 30 days is not counted"
    assert s["restores_proven"] == 1 and s["failures_recovered"] == 1 and s["failures_open"] == 1


def test_the_report_and_the_phone_message_always_name_one_next_step(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    p = pg.build(NOW, life=lambda: state([0], review_ago=2, quarter_ago=10))
    lines = []
    pg.report(p, say=lines.append)
    text = "\n".join(lines)
    assert "Your rhythm" in text and "Stronger than before" in text and "The one next step" in text
    msg = pg.short(p)
    assert msg.startswith(("Your estate had your back", "Your week with SecuRAX")) and len(msg) < 400
    if p["next"]:
        assert f"./securax finish {p['next']['id']}" in msg
