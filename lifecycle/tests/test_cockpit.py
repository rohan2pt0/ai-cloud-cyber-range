"""The cockpit: honest thresholds, honest radar, an Eisenhower matrix that is not decoration, a page with no script and no external request, and
collectors that fail soft (one broken check never blanks the page)."""
import importlib.util
import json
import pathlib
import re
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("cockpit", REPO / "governance" / "cockpit.py")
ck = importlib.util.module_from_spec(spec)
sys.modules["cockpit"] = ck
spec.loader.exec_module(ck)


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(ck, "HOME", tmp_path / "home")
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path / "home"))
    monkeypatch.setenv("SECURAX_INCIDENT_DIR", str(tmp_path / "inc"))


def item(id_, status, ev=(), prio="medium", nxt="do the thing", title="t"):
    return {"id": id_, "title": title, "applies": "all", "status": status, "note": "", "evidence": list(ev), "next": nxt if status in ("gap", "partial") else "", "priority": prio if status in ("gap", "partial") else ""}


def test_thresholds_in_both_directions():
    spec_ = {"amber": 2, "red": 7}
    assert [ck.rag(v, spec_) for v in (1, 2, 6.9, 7, 30)] == ["green", "amber", "amber", "red", "red"]
    spec2 = {"amber": 20, "red": 10}
    assert [ck.rag(v, spec2, True) for v in (50, 20, 19, 10, 9)] == ["green", "green", "amber", "amber", "red"]
    assert ck.rag(None, spec_) == "unknown"


def test_thresholds_file_is_complete_and_sane():
    c = ck.cfg()
    assert c["profile"] in ("personal", "regulated") and 0 < c["target_maturity"] <= 5
    for k, v in c["thresholds"].items():
        assert set(v) == {"amber", "red"}, k
    assert c["thresholds"]["backup_age_days"]["amber"] < c["thresholds"]["backup_age_days"]["red"]
    assert c["thresholds"]["disk_free_pct"]["amber"] > c["thresholds"]["disk_free_pct"]["red"]


def test_radar_scores_are_honest():
    m = {"items": [item("PR.AA.S1", "supported", ["journey:x"]), item("PR.AA.S2", "gap"), item("PR.AA.S3", "partial", ["file:a"]),
                   item("PR.AA.S4", "partial", ["journey:y"]), item("GV.RR.S3", "entity"), item("RS.CO.S1", "gap"), item("DE.CM.S1", "partial", ["file:a"])]}
    rows = {r["code"]: r for r in ck.radar_scores(m, 3.0)}
    assert "GV.RR" not in rows                                  # organisational duties only: not drawn, not scored
    aa = rows["PR.AA"]
    assert aa["designed"] == round(5 * (1 + 0 + 0.7 + 0.7) / 4, 2) and aa["demonstrated"] == round(5 * (1 + 0 + 0.2 + 0.5) / 4, 2)
    assert rows["RS.CO"]["designed"] == 0 and rows["RS.CO"]["demonstrated"] == 0                 # a gap scores zero on both
    assert rows["DE.CM"]["demonstrated"] < rows["DE.CM"]["designed"]                              # documented-only is below designed
    assert all(r["demonstrated"] <= r["designed"] for r in rows.values())


def test_the_real_cscrf_map_yields_a_radar_with_no_axis_above_designed():
    rm = ck._load("regmap_t", "governance/regmap.py")
    rows = ck.radar_scores(rm.load("cscrf"), 3.0)
    assert len(rows) >= 15 and all(0 <= r["demonstrated"] <= r["designed"] <= 5 for r in rows)


def test_category_extraction():
    assert ck.category_of("PR.AA.S1-S3,S7,S9 (access)") == "PR.AA" and ck.category_of("Annexure-J (cloud)") == "GV.SC" and ck.category_of("weird") is None


def test_pareto_orders_by_weight_and_marks_the_vital_few():
    bl = [{"theme": "A", "weight": 6}, {"theme": "B", "weight": 3}, {"theme": "C", "weight": 1}]
    p = ck.pareto(bl)
    assert [x["theme"] for x in p] == ["A", "B", "C"] and [x["vital"] for x in p] == [True, True, False]
    assert abs(p[-1]["cum"] - 1.0) < 1e-9 and abs(p[0]["share"] - 0.6) < 1e-9


def test_theme_classifier():
    assert ck.theme_of("Encrypt backups and add WAL archiving") == "Backup & recovery" or ck.theme_of("Encrypt backups") in ("Backup & recovery", "Data protection & residency")
    assert ck.theme_of("add OIDC and MFA") == "Identity & access" and ck.theme_of("zzz") == "Other"


def test_backlog_weights_gaps_above_partials():
    maps = {"x": {"items": [item("1", "gap", prio="high"), item("2", "partial", ["file:a"], prio="high"), item("3", "entity")]}}
    bl = ck.backlog(maps)
    assert [b["id"] for b in bl] == ["1", "2"] and bl[0]["weight"] == 4.5 and bl[1]["weight"] == 3.0


def metric(status, urgent, imp, action="fix"):
    return {"id": "m", "label": "L", "kind": "KRI", "area": "Run", "value": "v", "status": status, "why": "w", "action": action, "cmd": "./securax x", "urgent": urgent, "importance": imp, "trend": ""}


def test_eisenhower_quadrants():
    q = ck.eisenhower([metric("red", True, 3), metric("amber", True, 1), metric("amber", False, 3), metric("amber", False, 1), metric("green", True, 3), metric("red", True, 3, action="")], [])
    assert (len(q["do"]), len(q["automate"]), len(q["schedule"]), len(q["park"])) == (1, 1, 1, 1)         # green and action-less tiles are never listed
    q = ck.eisenhower([], [{"theme": "t", "priority": "high", "title": "H", "next": "n", "src": "x", "id": "1"}, {"theme": "t", "priority": "low", "title": "L", "next": "n", "src": "x", "id": "2"}])
    assert [i["title"] for i in q["schedule"]] == ["H"] and [i["title"] for i in q["park"]] == ["L"]


def test_short_titles():
    assert ck.short("A very long requirement; with a second clause") == "A very long requirement"
    assert len(ck.short("x" * 300)) == 96 and ck.short("x" * 300).endswith("…")


def test_sparkline_needs_three_points():
    assert "collecting" in ck.spark([1, 2]) and "<polyline" in ck.spark([1, 2, 3])


class FakeC:
    def __init__(self, metrics):
        self.metrics, self.profile, self.facts = metrics, "personal", {}


def test_page_has_no_script_no_external_request_and_escapes_everything():
    rm = ck._load("regmap_t2", "governance/regmap.py")
    maps = {k: rm.load(k) for k in rm.MAPS}
    evil = metric("red", True, 3)
    evil["label"], evil["value"] = "<script>alert(1)</script>", "\"><img src=x onerror=alert(1)>"
    page, data = ck.render(FakeC([evil, metric("green", False, 1)]), maps, [], "line one\n<b>x</b>", 1_800_000_000, 3.0)
    assert "<script" not in page.lower().replace("&lt;script", "") and "onerror=alert" not in page.replace("&lt;img src=x onerror", "")
    assert not re.findall(r"""(?:src|href)=["']https?://""", page) and "@import" not in page and "url(http" not in page
    assert "&lt;script&gt;alert(1)" in page and "AI briefing" in page and "<svg" in page
    assert data["overall"] == "red" and set(data["eisenhower"]) == {"do", "schedule", "automate", "park"}


def test_headline_reflects_the_worst_status():
    rm = ck._load("regmap_t3", "governance/regmap.py")
    maps = {k: rm.load(k) for k in rm.MAPS}
    for ms, want in (([metric("amber", False, 1)], "amber"), ([metric("green", False, 1)], "green"), ([], "unknown")):
        assert ck.render(FakeC(ms), maps, [], "", 1_800_000_000, 3.0)[1]["overall"] == want


def test_a_broken_collector_becomes_a_grey_tile_not_a_crash(monkeypatch):
    c = ck.Collector({}, 1_800_000_000, "personal", ck.cfg()["thresholds"])

    def c_boom():
        raise RuntimeError("boom")
    c.safe(c_boom)
    assert c.metrics[0]["status"] == "unknown" and "RuntimeError" in c.metrics[0]["why"]


def test_full_build_works_with_nothing_running(monkeypatch):
    monkeypatch.setattr(ck, "sh", lambda *a, **k: None)                    # no docker at all
    page, data, c = ck.build(now=1_800_000_000, root_env={}, fast=True)
    ids = {m["id"] for m in data["metrics"]}
    assert {"services", "backup", "disk", "incidents"} <= ids and page.startswith("<!doctype html>")
    assert next(m for m in data["metrics"] if m["id"] == "services")["status"] == "unknown"           # not running is "no data", never "OK"


def test_regulated_profile_makes_open_auth_and_residency_red(monkeypatch):
    monkeypatch.setattr(ck, "sh", lambda *a, **k: None)
    _, data, _ = ck.build(now=1_800_000_000, root_env={"SECURAX_PROFILE": "regulated"}, fast=True)
    st = {m["id"]: m["status"] for m in data["metrics"]}
    assert st["auth"] == "red" and st["residency"] == "red"
    _, data, _ = ck.build(now=1_800_000_000, root_env={}, fast=True)
    st = {m["id"]: m["status"] for m in data["metrics"]}
    assert st["auth"] == "unknown" and st["residency"] == "unknown"
    _, data, _ = ck.build(now=1_800_000_000, root_env={"AUTH_MODE": "required", "RESIDENCY_MODE": "enforce"}, fast=True)
    st = {m["id"]: m["status"] for m in data["metrics"]}
    assert st["auth"] == "green" and st["residency"] == "green"


def test_history_is_throttled_and_feeds_the_trends(tmp_path):
    c = FakeC([metric("red", True, 3)])
    data = {"ts": 1000, "metrics": c.metrics}
    ck.save_hist(data, c)
    ck.save_hist({"ts": 1000 + 60, "metrics": c.metrics}, c)                 # too soon: not recorded
    ck.save_hist({"ts": 1000 + 7 * 3600, "metrics": c.metrics}, c)
    assert len(ck.load_hist()) == 2 and ck.load_hist()[0]["reds"] == 1


def test_expiring_keys_raise_the_key_risk(monkeypatch):
    import base64
    keys = [{"id": "a", "sha256": "x", "roles": ["service"], "expires": "2027-01-05"}, {"id": "b", "sha256": "y", "roles": ["service"]}]
    env = {"GATEWAY_API_KEYS_B64": base64.b64encode(json.dumps(keys).encode()).decode()}
    c = ck.Collector(env, 1_798_761_600, "personal", ck.cfg()["thresholds"])         # 2027-01-01
    c.c_keys()
    m = c.metrics[0]
    assert m["status"] == "red" and "never expire" in m["value"] and "expiring" in m["value"]


def _coding_env(**kv):
    return {"GROQ_API_KEY": "gsk_x", "GEMINI_API_KEY": "AIza_x", **kv}


def test_coding_line_names_each_provider_and_the_local_fallback(monkeypatch):
    c = ck.Collector(_coding_env(ENABLE_LOCAL_CODER="1", CODER_MODEL="qwen2.5-coder:7b"), 1_000_000.0, "personal", ck.cfg()["thresholds"])
    calls = []

    def probe(p):
        calls.append(p["id"])
        return {"ok": True, "left": {"x-ratelimit-remaining-tokens-day": "180000"}} if p["id"] == "groq" else {"ok": True, "left": {}}
    monkeypatch.setattr(c, "_probe", probe)
    monkeypatch.setattr(ck, "sh", lambda args, timeout=20: "vulnbank-range-ollama-1\n" if args[1] == "ps" else "NAME\nqwen2.5-coder:7b  abc  4.7 GB\n")
    c.c_coding()
    m = next(x for x in c.metrics if x["id"] == "coding")
    assert sorted(calls) == ["gemini", "groq"]                       # only enabled providers are probed; no prompt is ever sent
    assert "Groq ✓ (180K tokens left, whole organisation)" in m["value"] and "Gemini ✓ (Green-tier only)" in m["value"]
    assert "Cerebras (not enabled)" in m["value"] and "DeepSeek (not enabled)" in m["value"]
    assert "Local fallback: qwen2.5-coder:7b ready." in m["value"] and m["status"] == "green"


def test_coding_line_is_cached_and_fast_mode_never_probes(monkeypatch):
    th = ck.cfg()["thresholds"]
    c = ck.Collector(_coding_env(), 1_000_000.0, "personal", th)
    monkeypatch.setattr(c, "_probe", lambda p: {"ok": False, "why": "answered 401 (key refused)"})
    c.c_coding()
    assert "Groq ✗ (answered 401 (key refused))" in c.metrics[-1]["value"] and c.metrics[-1]["status"] == "red"
    for now, fast in ((1_000_100.0, False), (9_999_999.0, True)):     # within 5 minutes: cache; fast: cache only, even when stale
        c2 = ck.Collector(_coding_env(), now, "personal", th, fast=fast)
        monkeypatch.setattr(c2, "_probe", lambda p: (_ for _ in ()).throw(AssertionError("must not probe")))
        c2.c_coding()
        assert "Groq ✗" in c2.metrics[-1]["value"]


def test_concurrent_writers_never_leave_a_mixed_file(tmp_path):
    """The real failure (sandbox, cockpit_page): `up` refreshes the cockpit in the background while another refresh runs; plain
    write_text truncates then writes, so a short write over a long one left the old tail behind ("Extra data"). With atomic_write every
    read, at any moment, is one complete document."""
    import threading
    target = tmp_path / "cockpit.json"
    long_doc, short_doc = json.dumps({"x": "y" * 50000, "n": list(range(2000))}, indent=1), json.dumps({"x": 1})
    stop, bad = threading.Event(), []

    def writer(doc):
        while not stop.is_set():
            ck.atomic_write(target, doc)

    def reader():
        while not stop.is_set():
            try:
                json.loads(target.read_text())
            except FileNotFoundError:
                pass
            except ValueError as e:
                bad.append(str(e)[:80])
    ck.atomic_write(target, short_doc)
    ts = [threading.Thread(target=writer, args=(d,)) for d in (long_doc, short_doc, long_doc)] + [threading.Thread(target=reader) for _ in range(2)]
    [t.start() for t in ts]
    import time as _t
    _t.sleep(1.5)
    stop.set()
    [t.join() for t in ts]
    assert not bad, bad[:3]
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".cockpit.json.")], "no temporary files left behind"


def test_writing_the_cockpit_self_heals_a_locked_portal_dir(tmp_path):
    # If an older life-docs import left portal/ owner-only, the nginx container 403s every page. Writing the cockpit
    # (which `up` does on every start) must restore the traversal bits so the Command Center serves again.
    import os
    import stat as _stat
    portal = tmp_path / "portal"
    portal.mkdir()
    portal.chmod(0o700)
    ck.atomic_write(portal / "cockpit.html", "<!doctype html><title>x</title>")
    assert (portal.stat().st_mode & 0o055) == 0o055, "portal/ is traversable+readable by others after a cockpit write"
    assert _stat.S_IMODE((portal / "cockpit.html").stat().st_mode) == 0o644
    os.chmod(portal, 0o755)
