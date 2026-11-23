"""The supervised AI investigation view: exercise control sees the whole story; a team does not."""
import json
import pathlib
import threading
import time
import urllib.error
import urllib.request

from exercise import engine, investigation, portal


def _game(tmp: pathlib.Path):
    tokens = engine.Game.create(tmp / "g", team=8)
    g = engine.Game(tmp / "g")
    g.start(time.time() - 600)
    return g, tokens


def test_the_story_holds_together(tmp_path):
    g, _ = _game(tmp_path)
    d = investigation.build(g, 8)
    assert all(c["state"] == "pass" for c in d["controls"]) and len(d["controls"]) == 10
    assert all(p["ok"] for p in d["preflight"])
    blocked = [r for r in d["requests"] if r["kind"] == "blocked"]
    assert blocked and not blocked[0]["in_target_log"] and d["scope"]["target"] not in blocked[0]["path"]
    assert d["requests"][d["requests"].index(blocked[0]) + 1]["kind"] == "pause"      # a reach outside scope pauses the run
    sent = [r for r in d["requests"] if r["kind"] in ("ok", "finding")]
    assert d["reconcile"]["agent_requests"] == len(sent) == d["reconcile"]["target_log_matches"] and d["reconcile"]["gaps"] == 0
    assert d["scope"]["authorised_by"] and d["scope"]["data"] == "synthetic only"


def test_only_exercise_control_sees_it(tmp_path):
    g, tokens = _game(tmp_path)
    srv = portal.serve(g, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/api/investigation"
    def get(tok):
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, None
    try:
        st, body = get(tokens["white"])
        assert st == 200 and body["finding"]["severity"] == "high"
        assert get(tokens["blue-8"])[0] == 403 and get(tokens["red"])[0] == 403
    finally:
        srv.shutdown()
