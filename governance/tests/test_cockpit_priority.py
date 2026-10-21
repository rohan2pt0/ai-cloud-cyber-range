"""The cockpit's advice order: the most severe item comes first, so "next 3" is the real next 3."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cockpit  # noqa: E402


def _m(label, status, importance, urgent=True):
    return {"label": label, "value": "x", "status": status, "why": "", "action": "do it", "cmd": "", "urgent": urgent, "importance": importance}


def test_red_beats_amber_and_importance_breaks_ties():
    metrics = [_m("amber-low", "amber", 3), _m("red-mid", "red", 2), _m("red-high", "red", 3)]
    q = cockpit.eisenhower(metrics, [])
    assert [i["title"].split(":")[0] for i in q["do"]] == ["red-high", "red-mid", "amber-low"]


def test_vital_signs_lead_schedule_and_high_backlog_beats_medium():
    bl = [{"title": "medium gap", "theme": "t", "src": "s", "id": "1", "next": "n", "priority": "medium"},
          {"title": "high gap", "theme": "t", "src": "s", "id": "2", "next": "n", "priority": "high"}]
    q = cockpit.eisenhower([_m("live", "amber", 3, urgent=False)], bl)
    assert [i["title"].split(":")[0] for i in q["schedule"]] == ["live", "high gap", "medium gap"]


def test_same_gap_from_two_maps_is_listed_once_and_no_internal_keys_leak():
    bl = [{"title": "same gap", "theme": "a", "src": "rbi", "id": "1", "next": "n", "priority": "high"},
          {"title": "same gap", "theme": "b", "src": "sebi", "id": "9", "next": "n", "priority": "high"}]
    q = cockpit.eisenhower([], bl)
    assert len(q["schedule"]) == 1
    assert all("_rank" not in it for v in q.values() for it in v)


def test_the_page_renders_when_the_gateway_reports_allowance_callers(monkeypatch):
    # Regression: the allowance lamp's loop variable once shadowed render()'s config object, so the cockpit crashed
    # exactly when the gateway was up and had callers (CI caught it on a real estate; a laptop without callers never did).
    import io
    import json as _json
    import urllib.request

    real = urllib.request.urlopen

    def fake(url, *a, **k):
        u = url if isinstance(url, str) else url.full_url
        if u.endswith("/v1/budget"):
            body = {"warn_at": 0.8, "callers": [{"caller": "abc123def456", "day_used": 9, "day_limit": 10, "month_used": 9, "month_limit": 100}]}
            return io.BytesIO(_json.dumps(body).encode())
        raise OSError("offline in tests")
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    html, data, _c = cockpit.build(fast=True)
    assert "AI allowance used up or near it" in html and data["profile"] is not None
    monkeypatch.setattr(urllib.request, "urlopen", real)


def test_the_page_is_a_dark_cockpit(monkeypatch):
    # One master lamp, at most three actions, instruments up front, and every detail folded away.
    import urllib.request

    def offline(*a, **k):
        raise OSError("offline in tests")
    monkeypatch.setattr(urllib.request, "urlopen", offline)
    html, _d, _c = cockpit.build(fast=True)
    head = html.split("class='inst'", 1)[0]
    assert head.count("class='master") == 1 and head.count("<li") <= 3
    assert "<details class='card panel' id='govern'>" in html and "<details class='card panel' id='systems'>" in html
    assert "<details open class='card panel'" not in html and "<script" not in html
