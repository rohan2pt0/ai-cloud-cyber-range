"""`./securax ai spend`: the month's AI spend per provider, in rupees, in plain words."""
import importlib.util
import io
import json
import pathlib

_s = importlib.util.spec_from_file_location("aicontrol", pathlib.Path(__file__).resolve().parent.parent / "aicontrol.py")
ac = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ac)


def _run(monkeypatch, capsys, payload):
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    rc = ac.main(["spend"])
    return rc, capsys.readouterr().out


def test_spend_shows_each_provider_with_the_watch_and_cap_markers(monkeypatch, capsys):
    payload = json.dumps({"month": "2026-11", "inr_per_usd": 95.0, "providers": {
        "gemini": {"inr": 800, "cap_inr": 1000, "share": 0.8},
        "openai": {"inr": 1200, "cap_inr": 1000, "share": 1.2},
        "anthropic": {"inr": 240, "cap_inr": 1000, "share": 0.24},
        "edge": {"inr": 1000, "cap_inr": 1000, "share": 1.0},
        "quiet": {"cap_inr": 1000},
    }})
    rc, out = _run(monkeypatch, capsys, payload)
    assert rc == 0
    assert "AI spend in 2026-11 (rupees, at Rs 95 a dollar)" in out
    assert "gemini  Rs 800  of Rs 1,000  (80%)" in out and out.count("<- 80%: watch it") == 1
    assert "openai  Rs 1,200  of Rs 1,000  (120%)" in out and out.count("<- cap reached: the local model answers") == 2
    assert "anthropic  Rs 240  of Rs 1,000  (24%)" in out
    assert "edge  Rs 1,000  of Rs 1,000  (100%)" in out
    assert "quiet  Rs 0  of Rs 1,000  (0%)" in out


def test_no_paid_ai_used_this_month(monkeypatch, capsys):
    rc, out = _run(monkeypatch, capsys, json.dumps({"month": "2026-11", "inr_per_usd": 95, "providers": {}}))
    assert rc == 0 and "No paid AI used this month." in out


def test_empty_or_bad_stdin_says_the_gateway_is_not_running(monkeypatch, capsys):
    for payload in ("", "not json"):
        rc, out = _run(monkeypatch, capsys, payload)
        assert rc == 1
        assert "The gateway is not running: start it with ./securax up" in out
