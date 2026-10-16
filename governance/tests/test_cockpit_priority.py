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
