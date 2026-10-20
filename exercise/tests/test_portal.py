"""The exercise portal over real HTTP: each role sees only what it should, the forms work, and the page is locked down."""
import json
import pathlib
import sys
import threading
import urllib.error
import urllib.request

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from exercise import engine, portal, scenario  # noqa: E402


@pytest.fixture
def site(tmp_path):
    tokens = engine.Game.create(tmp_path / "g", team=3)
    g = engine.Game(tmp_path / "g")
    srv = portal.serve(g, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield g, tokens, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def call(base, path, token=None, body=None, raw=None, ctype="application/json"):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(base + path, data=data, method="POST" if data is not None else "GET")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    if data is not None:
        req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read()), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}"), dict(e.headers)


def test_the_page_is_locked_down_and_needs_a_token(site):
    g, tokens, base = site
    with urllib.request.urlopen(base + "/", timeout=10) as r:
        html = r.read().decode()
        h = dict(r.headers)
    assert "Exercise portal" in html and "script-src 'self'" in h["Content-Security-Policy"] and h["X-Frame-Options"] == "DENY"
    assert call(base, "/api/overview")[0] == 401 and call(base, "/api/overview", "wrong")[0] == 401
    assert call(base, "/api/incident", tokens["blue-3"], raw=b"x" * (portal.MAX_BODY + 10))[0] == 400
    assert call(base, "/api/incident", tokens["blue-3"], raw=b"target=www", ctype="application/x-www-form-urlencoded")[0] == 400
    js = (ROOT / "exercise" / "web" / "app.js").read_text()
    assert "innerHTML" not in js and "eval(" not in js                       # server text only ever becomes textContent


def test_roles_see_only_their_part(site):
    g, tokens, base = site
    blue, red, white = tokens["blue-3"], tokens["red"], tokens["white"]
    assert call(base, "/api/start", blue, {})[0] == 403
    assert call(base, "/api/start", white, {})[0] == 200
    g.set_meta("started", str(float(g.meta("started")) - 130 * 60))         # into the attack phase
    assert call(base, "/api/attack", blue, {"target": "www", "objective": "x"})[0] == 403
    assert call(base, "/api/attack", red, {"target": "www", "objective": "Defaced the website", "evidence": "curl output"})[0] == 200
    assert call(base, "/api/scorelog", red)[0] == 403 and call(base, "/api/reports", red)[0] == 403
    t = call(base, "/api/targets", red)[1]
    assert "checks" not in t[0] and {x["host"] for x in t} >= {"www", "dns1"}
    code, body, _ = call(base, "/api/incident", blue, {"target": "www", "compromised": True, "chronology": "Defaced at 10:02; fixed 10:20"})
    assert code == 200
    mine = call(base, "/api/reports", blue)[1]
    assert mine and "red_reports" not in mine[0]                              # blue never sees the red team's claim
    queue = call(base, "/api/reports?kind=incident&pending=1", white)[1]
    assert queue[0]["red_reports"][0]["objective"] == "Defaced the website"
    assert call(base, f"/api/judge/{queue[0]['id']}", blue, {"points": 20, "verdict": "accepted"})[0] == 403
    assert call(base, f"/api/judge/{queue[0]['id']}", white, {"points": 99, "verdict": "accepted"})[0] == 400
    assert call(base, f"/api/judge/{queue[0]['id']}", white, {"points": 18, "verdict": "accepted", "feedback": "good"})[1] == {"points": 18.0}
    tot = call(base, "/api/overview", blue)[1]["totals"]
    assert tot["attack_reports"] == -40 and tot["incident_reports"] == 18
    assert call(base, "/api/overview?team=99", blue)[1]["team"] == 3          # a blue team cannot ask for another team


def test_blue_team_workflow_through_the_portal(site):
    g, tokens, base = site
    blue, white = tokens["blue-3"], tokens["white"]
    call(base, "/api/start", white, {})
    assert call(base, "/api/tasks/p2-repeat/submit", blue, {"answer": "x"})[0] == 400        # not open yet
    assert "default administrator" in call(base, "/api/tasks/p1-endpoints/hint", blue, {})[1]["hint"]
    assert call(base, "/api/tasks/p1-endpoints/submit", blue, {"answer": "Our plan"})[0] == 200
    assert call(base, "/api/tasks/p1-network/abandon", blue, {})[1] == {"points": -25.0}
    assert call(base, "/api/sitrep", blue, {"event_overview": "Quiet so far", "status": "All green"})[0] == 200
    assert call(base, "/api/creds", blue, {"username": "bea.example", "system": "ws3-2", "password": "New-Sample-22!", "reason": "reset after phishing"})[0] == 200
    assert g.password(3, "bea.example", "ws3-2") == "New-Sample-22!"
    assert call(base, "/api/restore", blue, {"host": "www", "reason": "rebuilt"})[1] == {"points": -25.0}
    rows = scenario.checks(g.scenario())
    g.record_round(3, [(r, True, "ok") for r in rows])
    assert all(z["good_pct"] == 100 for z in call(base, "/api/awareness", blue)[1])
    tl = call(base, "/api/timeline", blue)[1]
    assert tl["series"]["total"][-1] == g.totals(3)["total"]
    assert call(base, "/api/verify", white)[1] == {"problems": []} and call(base, "/api/verify", blue)[0] == 403
    assert call(base, "/api/news", blue)[1][0]["title"] == "Welcome to Example Corp"


def test_guessing_tokens_gets_an_address_refused(site):
    _, tokens, base = site
    for _ in range(portal.FAIL_LIMIT):
        call(base, "/api/me", "guess")
    assert call(base, "/api/me", tokens["white"])[0] == 403                   # even the right token waits out the minute


def test_rules_and_plan_screens(site):
    g, tokens, base = site
    blue, red, white = tokens["blue-3"], tokens["red"], tokens["white"]
    r = call(base, "/api/rules", red)[1]
    assert set(r) == {"rules"} and r["rules"]                                                    # red reads the rules, not the checks
    assert "green_team" in call(base, "/api/rules", blue)[1]
    assert call(base, "/api/plan", red)[0] == 403
    assert call(base, "/api/plan/t0-inventory", white, {"status": "done"})[0] == 403             # the team marks its own plan
    assert call(base, "/api/plan/t0-inventory", blue, {"status": "done"})[1] == {"ok": True}
    assert next(i for i in call(base, "/api/plan", white)[1]["items"] if i["id"] == "t0-inventory")["state"] == "done"
