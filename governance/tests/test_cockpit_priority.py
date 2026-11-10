"""The cockpit's advice order: the most severe item comes first, so the one thing to do next is the real next thing."""
import re
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
    # One master lamp, one Do-next action (the rest under Later), instruments up front, and every detail folded away.
    import urllib.request

    def offline(*a, **k):
        raise OSError("offline in tests")
    monkeypatch.setattr(urllib.request, "urlopen", offline)
    html, _d, _c = cockpit.build(fast=True)
    head = html.split("class='inst'", 1)[0]
    assert head.count("class='master") == 1
    assert re.sub(r"<details class='later'>.*?</details>", "", head, flags=re.S).count("<li") <= 1
    assert "<details class='card panel' id='govern'>" in html and "<details class='card panel' id='systems'>" in html
    assert "<details open class='card panel'" not in html and "<script" not in html
    bare = html.lower().replace("http://www.w3.org", "")
    assert "http://" not in bare and "https://" not in bare          # the cockpit names no external URL (sandbox cockpit_page)
    assert "gap backlog" not in head and "Implement" not in head     # builders' backlog stays in Mission planning, never in "do next"


def test_one_do_next_action_and_the_rest_under_later(monkeypatch):
    # One open action: with three red vital signs, exactly one "Do next" item, and "Later (2)" folds the other two.
    import urllib.request

    def offline(*a, **k):
        raise OSError("offline in tests")
    monkeypatch.setattr(urllib.request, "urlopen", offline)

    def three_red(self):
        for i, lbl in enumerate(["Disk full", "Backup too old", "Unpatched software"]):
            self.add(f"red{i}", lbl, "KRI", "Protect", "critical", "red", "why", f"Fix {lbl}", f"./securax fix {i}", urgent=True, importance=3)
    monkeypatch.setattr(cockpit.Collector, "run", three_red)
    html, _d, _c = cockpit.build(fast=True)
    head = html.split("class='inst'", 1)[0]
    assert "<ol class='do'>" in head and "Later (2)" in head
    assert re.sub(r"<details class='later'>.*?</details>", "", head, flags=re.S).count("<li") == 1


def _quiet_lamps(monkeypatch):
    # The lamp helpers read files and the network; stub them so the lamp logic itself is what a test asserts.
    monkeypatch.setattr(cockpit, "_late_risks", lambda: 0)
    monkeypatch.setattr(cockpit, "_stopped_ai", lambda: [])
    monkeypatch.setattr(cockpit, "_allowance_near", lambda: [])
    monkeypatch.setattr(cockpit, "_share_light", lambda now: None)
    monkeypatch.setattr(cockpit, "_prune_items", lambda: [])
    monkeypatch.setattr(cockpit, "_jewels_and_continuity", lambda: ([], []))


def test_headline_amber_is_singular_for_one_thing():
    assert "1 thing to schedule" in cockpit._headline("amber", [], [_m("a", "amber", 2)])


def test_lamps_nominal_count_is_the_number_of_green_metrics(monkeypatch):
    _quiet_lamps(monkeypatch)
    ms = [{"id": "a", "status": "green"}, {"id": "b", "status": "green"}]
    nominal = [l for l in cockpit._lamps(0.0, [], [], ms) if l[2] == "Nominal"][0]
    assert nominal[1] == 2


def test_allowance_near_the_line_is_a_caution_not_a_warning(monkeypatch):
    _quiet_lamps(monkeypatch)
    monkeypatch.setattr(cockpit, "_allowance_near", lambda: [0.9])
    lamp = [l for l in cockpit._lamps(0.0, [], [], []) if "AI allowance" in l[2]][0]
    assert lamp[0] == "caut"


def test_allowance_fully_used_is_a_warning(monkeypatch):
    _quiet_lamps(monkeypatch)
    monkeypatch.setattr(cockpit, "_allowance_near", lambda: [1.5])
    lamp = [l for l in cockpit._lamps(0.0, [], [], []) if "AI allowance" in l[2]][0]
    assert lamp[0] == "warn"


def test_crown_jewel_lamp_names_the_first_jewel(monkeypatch):
    _quiet_lamps(monkeypatch)
    monkeypatch.setattr(cockpit, "_jewels_and_continuity", lambda: ([{"priority": "DO NOW", "name": "Key vault", "command": "./securax jewels"}], []))
    assert any("Crown jewels exposed" in l[2] and "Key vault" in l[2] for l in cockpit._lamps(0.0, [], [], []))


def test_later_folds_extra_actions_to_at_most_twelve():
    nxt = [{"title": f"t{i}", "cmd": "", "action": "a"} for i in range(14)]
    assert "Later (12)" in cockpit._head_card("red", "headline", "stamp", nxt)


def test_govern_gauge_is_red_at_maturity_one():
    assert "gauge red" in cockpit._instruments([], ("<div id='govern'></div>", 1))


def test_systems_summary_counts_nominal_metrics():
    m = {**_m("a", "green", 2), "kind": "KPI", "area": "Protect"}
    out = cockpit._systems_card([m], [], [])
    assert "1 nominal" in out


def test_ai_brief_renders_a_folded_panel():
    assert "<details" in cockpit._ai_brief_card("hello")


def test_an_instrument_shows_its_reading_whole_and_its_detail_small():
    m = {"id": "disk", "label": "Disk", "value": "2.7% free (7.2 GB)", "status": "red", "why": "w"}
    out = cockpit.instrument(m)
    assert "<b>2.7% free</b>" in out and "<span class='note'>7.2 GB</span>" in out and "…" not in out
    assert "<span class='note'>" not in cockpit.instrument({**m, "value": "none yet"})


def _served_metric(monkeypatch, body):
    # The "Which model answered" metric (doc 83): unknown when the gateway is off, amber when over 20% fell to a weak rung.
    import io
    import json as _json
    import urllib.request

    def fake(url, *a, **k):
        u = url if isinstance(url, str) else url.full_url
        if body is not None and u.endswith("/v1/served"):
            return io.BytesIO(_json.dumps(body).encode())
        raise OSError("offline in tests")
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    col = cockpit.Collector({}, 0.0, "personal", {})
    col.c_served()
    (m,) = [x for x in col.metrics if x["id"] == "served"]
    assert m["label"] == "Which model answered" and not m["urgent"] and m["importance"] == 2
    return m


def test_served_metric_is_unknown_when_the_gateway_is_off(monkeypatch):
    m = _served_metric(monkeypatch, None)
    assert m["status"] == "unknown" and m["value"] == "gateway off"


def test_served_metric_is_amber_when_a_weak_fallback_answered_too_often(monkeypatch):
    m = _served_metric(monkeypatch, {"window_h": 24, "calls": 20, "weak_share": 0.35, "by_served": [
        {"served": "gemini/gemini-2.5-flash", "calls": 13, "weak": False}, {"served": "ollama/qwen2.5:0.5b", "calls": 7, "weak": True}]})
    assert m["status"] == "amber" and m["value"] == "35% on a weaker fallback (top: qwen2.5:0.5b)"
    assert m["action"] == "See why the strong model was skipped" and m["cmd"] == "./securax providers list"


def test_served_metric_is_green_when_the_strong_model_answered(monkeypatch):
    m = _served_metric(monkeypatch, {"window_h": 24, "calls": 10, "weak_share": 0.1, "by_served": [
        {"served": "gemini/gemini-2.5-flash", "calls": 9, "weak": False}, {"served": "ollama/qwen2.5:0.5b", "calls": 1, "weak": True}]})
    assert m["status"] == "green" and m["value"] == "strong model on 9 calls"


def _anomaly_metric(monkeypatch, body, now=1_800_000_000.0):
    # "Unusual AI key use" (doc 92): unknown when the gateway is off, red when a caller behaved unlike itself in the last day.
    import io
    import json as _json
    import urllib.request

    def fake(url, *a, **k):
        u = url if isinstance(url, str) else url.full_url
        if body is not None and u.endswith("/v1/anomalies"):
            assert k.get("timeout") == 3
            return io.BytesIO(_json.dumps(body).encode())
        raise OSError("offline in tests")
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    col = cockpit.Collector({}, 0.0, "personal", {})
    col.c_anomalies(now=now)
    (m,) = [x for x in col.metrics if x["id"] == "anomalies"]
    assert m["label"] == "Unusual AI key use" and m["importance"] == 3
    assert "://" not in " ".join(str(v) for v in m.values()), "the cockpit names no external URL"
    return m


def _ts(t):
    import time as _t
    return _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime(t))


def test_anomaly_metric_is_unknown_when_the_gateway_is_off(monkeypatch):
    m = _anomaly_metric(monkeypatch, None)
    assert m["status"] == "unknown" and m["value"] == "gateway off" and not m["urgent"]


def test_anomaly_metric_is_green_when_nothing_recent(monkeypatch):
    now = 1_800_000_000.0
    m = _anomaly_metric(monkeypatch, {"anomalies": [{"ts": _ts(now - 30 * 3600), "caller": "key:webui", "kind": "burst", "detail": "old"}]})
    assert m["status"] == "green" and m["value"] == "no unusual use" and not m["urgent"]


def test_a_behavioural_anomaly_is_red_and_urgent(monkeypatch):
    now = 1_800_000_000.0
    m = _anomaly_metric(monkeypatch, {"anomalies": [
        {"ts": _ts(now - 60), "caller": "key:webui", "kind": "new_model", "detail": "asked for opencodego/deepseek, never used before"},   # benign (a new provider): must NOT count
        {"ts": _ts(now - 3600), "caller": "key:webui", "kind": "burst", "detail": "99 requests, seen from https://evil.example"},
        {"ts": _ts(now - 40 * 3600), "caller": "key:old", "kind": "odd_hour", "detail": "old"}]})
    assert m["status"] == "red" and m["urgent"] and m["value"] == "1 in 24 h, latest: key:webui burst"
    assert m["action"] == "Check who used the key; revoke it if it was not you" and m["cmd"] == "./securax gateway-auth key list"
    assert "anomalies" not in cockpit.PRIMARY


def test_a_new_model_alone_is_not_flagged_as_a_stolen_key(monkeypatch):
    now = 1_800_000_000.0
    m = _anomaly_metric(monkeypatch, {"anomalies": [
        {"ts": _ts(now - 60), "caller": "key:webui", "kind": "new_model", "detail": "asked for opencodego/deepseek-v4, never used before"}]})
    assert m["status"] == "green" and not m["urgent"], "adding a provider or the ladder trying a new model is normal, not a stolen key"
