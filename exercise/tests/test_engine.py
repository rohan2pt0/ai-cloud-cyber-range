"""The exercise core: scenario templates, real service checks against local servers, and the game rules end to end.

Everything here is offline and uses the fictional sample scenario; no container is started."""
import json
import pathlib
import socket
import socketserver
import struct
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from exercise import checks, engine, scenario  # noqa: E402

T0 = 1_800_000_000.0


def test_one_scenario_serves_every_team_number():
    a, b = scenario.load(team=7), scenario.load(team=61)
    assert scenario.host(a, "dns1")["ip"] == "10.7.1.2" and scenario.host(b, "www")["ip"] == "10.188.61.55"
    assert a["domain"] == "ex7.range.test" and scenario.reserved(a, "dmz", 252) == "10.7.1.252"
    assert scenario.fill("10.188.33.{X*4-2}", 25) == "10.188.33.98"           # the uplink style from a real exercise plan
    with pytest.raises(ValueError):
        scenario.fill("{__import__('os').system('true')}", 1)                 # templates are arithmetic, never code


def test_a_broken_scenario_is_refused_with_every_problem(tmp_path):
    raw = json.loads(scenario.SAMPLE.read_text())
    raw["hosts"][3]["ip"] = "10.{X}.9.2"                                     # outside its zone
    raw["hosts"][4]["services"][0]["check"] = "telnet"
    raw["hosts"].append(dict(raw["hosts"][5]))                               # a duplicate
    raw["hosts"][6]["ip"] = "10.{X}.1.252"                                   # the scoring bot's address
    f = tmp_path / "bad.json"
    f.write_text(json.dumps(raw))
    with pytest.raises(ValueError) as e:
        scenario.load(f, 3)
    msg = str(e.value)
    assert "outside zone dmz" in msg and "check must be" in msg and "listed twice" in msg and "kept for the scoring bot" in msg


class _Web(BaseHTTPRequestHandler):
    body = b"<h1>Example Corp</h1>"

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, *a):
        pass


class _Banner(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.sendall(self.server.greeting)


class _Dns(socketserver.BaseRequestHandler):
    def handle(self):
        data, sock = self.request
        qid = struct.unpack(">H", data[:2])[0]
        answers = 0 if b"\x07missing" in data else 1
        sock.sendto(struct.pack(">HHHHHH", qid, 0x8180, 1, answers, 0, 0) + data[12:], self.client_address)


def _serve(server):
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server.server_address[1]


def test_checks_against_real_local_servers():
    web = _serve(ThreadingHTTPServer(("127.0.0.1", 0), _Web))
    ssh = socketserver.ThreadingTCPServer(("127.0.0.1", 0), _Banner)
    ssh.greeting = b"SSH-2.0-OpenSSH_9.9\r\n"
    smtp = socketserver.ThreadingTCPServer(("127.0.0.1", 0), _Banner)
    smtp.greeting = b"554 go away\r\n"
    dns = socketserver.ThreadingUDPServer(("127.0.0.1", 0), _Dns)
    p_ssh, p_smtp, p_dns = _serve(ssh), _serve(smtp), _serve(dns)
    row = lambda check, port, **kw: {"check": check, "ip": "127.0.0.1", "port": port, **kw}  # noqa: E731
    assert checks.run(row("http", web, expect="Example Corp"))[0]
    ok, why = checks.run(row("http", web, expect="Welcome"))
    assert not ok and "lacks" in why                                         # a defaced page fails though the port is open
    assert checks.run(row("ssh", p_ssh))[0] and checks.run(row("tcp", p_ssh))[0]
    assert not checks.run(row("smtp", p_smtp))[0]                            # answers, but not as a working mail server
    assert checks.run(row("dns", p_dns, query="www.ex1.range.test"))[0]
    assert checks.run(row("dns", p_dns, query="missing.ex1.range.test")) == (False, "no answer for missing.ex1.range.test")
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    closed = s.getsockname()[1]
    s.close()
    ok, why = checks.run(row("ssh", closed), timeout=1)
    assert not ok and "Refused" in why


@pytest.fixture
def game(tmp_path):
    tokens = engine.Game.create(tmp_path / "g", team=5)
    g = engine.Game(tmp_path / "g")
    return g, tokens


def test_roles_tokens_and_the_clock(game, tmp_path):
    g, tokens = game
    assert g.auth(tokens["white"]) == {"role": "white", "team": None} and g.auth(tokens["blue-5"]) == {"role": "blue", "team": 5}
    assert g.auth("guess") is None and g.auth("") is None
    assert (tmp_path / "g").stat().st_mode & 0o077 == 0 and tokens["red"] not in (tmp_path / "g" / "game.db").read_bytes().decode("latin-1")
    rows = scenario.checks(g.scenario())
    g.record_round(5, [(r, True, "ok") for r in rows], ts=T0 - 10)
    assert g.totals(5)["total"] == 0                                         # nothing scores before the clock starts
    g.start(T0)
    assert g.phase(T0 + 60)["name"] == "Hardening" and g.phase(T0 + 130 * 60)["attacks_allowed"]
    assert [t["status"] for t in g.tasks(5, T0 + 60)].count("locked") == 4
    assert g.news(T0 + 120 * 60)[0]["title"] == "Attacks expected soon"


def test_the_whole_game_scores_like_the_exercise_and_cannot_be_edited(game):
    g, _ = game
    g.start()
    rows = scenario.checks(g.scenario())
    up = [(r, r["host"] != "www", "x") for r in rows]                        # the website is down this round
    res = g.record_round(5, up, usersim=[("alex.sample", "ws3-1", True, "ok"), ("bea.example", "ws3-2", False, "bad password")])
    www = sum(1 for r in rows if r["host"] == "www")
    assert www == 3 and res["points"] == len(rows) - www + 1 and g.totals(5)["availability"] == res["points"]   # HOST (ping), SSH, HTTP
    tgt = {t["host"]: t for t in g.targets(5)}
    assert not any(c["ok"] for c in tgt["www"]["checks"] if c["kind"] == "service") and tgt["ws3-2"]["checks"][-1]["kind"] == "usersim"
    # mission board: hint, answer, judged within the task's points; give up on another
    assert "default administrator" in g.use_hint(5, "blue", "p1-endpoints")
    sid = g.submit_task(5, "blue", "p1-endpoints", "Change every default password; restrict RDP; send logs to the SIEM.")
    with pytest.raises(ValueError):
        g.judge(sid, "white", 60, "accepted")                                # over the task's 50 points
    assert g.judge(sid, "white", 41, "accepted", "good plan") == 41
    with pytest.raises(ValueError):
        g.submit_task(5, "blue", "p1-endpoints", "again")
    assert g.abandon_task(5, "blue", "p1-network") == -25
    # the red team can only score in the attack phase
    with pytest.raises(ValueError):
        g.attack(5, "red", "www", "defaced the website")
    g.set_meta("started", str(float(g.meta("started")) - 125 * 60))
    aid = g.attack(5, "red", "www", "Defaced the website", "screenshot attached")
    assert "www" in g.compromised(5)
    zones = {z["zone"]: z for z in g.awareness(5)}
    assert zones["cloud"]["good"] == 0 and zones["dmz"]["good_pct"] == 100
    inc = g.file_incident(5, "blue", {"target": "www", "compromised": True, "chronology": "Defaced at 10:02, restored at 10:20",
                                      "impact": "Integrity of the public site", "source": "Malicious", "action_plan": "Rebuilt from image"})
    pending = g.submissions(5, "incident", pending_only=True)
    assert pending[0]["red_reports"][0]["id"] == aid                         # the judge sees what the red team claimed
    g.judge(inc, "white", 15, "accepted", "clear timeline")
    assert "www" not in g.compromised(5)
    sr = g.file_sitrep(5, "blue", {"event_overview": "Website defaced and restored.", "status": "All services up."})
    with pytest.raises(ValueError):
        g.judge(sr, "white", 9, "accepted")                                  # graded 0..5
    assert g.judge(sr, "white", 3, "accepted", "more detail on adversary") == 12
    g.restore(5, "blue", "www", "reverted to snapshot")
    g.special(5, "white", 5, "helped another team")
    tot = g.totals(5)
    assert (tot["solve_task"], tot["abandon_task"], tot["use_hint"], tot["attack_reports"], tot["incident_reports"],
            tot["situation_reports"], tot["restore_from_backup"], tot["special"]) == (41, -25, -10, -40, 15, 12, -25, 5)
    assert g.timeline(5)["series"]["total"][-1] == tot["total"]
    # documented password changes are what the simulated staff use next
    with pytest.raises(KeyError):
        g.cred_change(5, "blue", "nobody", "ws3-1", "x", "y")
    assert g.password(5, "alex.sample", "ws3-1") == "Sample-Pass-11!"
    g.cred_change(5, "blue", "alex.sample", "ws3-1", "New-Sample-21!", "used in a phishing reply")
    assert g.password(5, "alex.sample", "ws3-1") == "New-Sample-21!"
    assert g.password(5, "alex.sample", "intranet") == "Sample-Pass-11!"           # changed on one machine only
    g.cred_change(5, "blue", "alex.sample", "all", "New-Sample-31!", "domain-wide reset")
    assert g.password(5, "alex.sample", "intranet") == g.password(5, "alex.sample", "ws3-1") == "New-Sample-31!"
    rep = g.after_action(5)
    assert "the score log verifies" in rep and "Defaced the website" in rep and "| **total** |" in rep
    # tampering with the score log is caught
    assert g.verify() == []
    g.db.execute("UPDATE events SET points=999 WHERE category='attack_reports'")
    assert any("changed" in p for p in g.verify())
    g.db.execute("UPDATE events SET points=-40 WHERE category='attack_reports'")
    assert g.verify() == []
    g.db.execute("DELETE FROM events WHERE category='restore_from_backup'")
    assert g.verify()


def test_every_machine_has_a_ping_check_and_rule_breaches_cost_points_each_round(game):
    g, _ = game
    sc = g.scenario()
    assert all(any(s["check"] == "ping" for s in h["services"]) for h in sc["hosts"])            # the "HOST" check, as exercises show it
    assert sc["green_team"]["username"] == "greenteam" and len(sc["rules"]) >= 5
    g.start()
    rows = scenario.checks(sc)
    bad = [("www", "Green-team account works", False, "key login refused"), ("dns1", "Green-team account works", True, "ok")]
    r = g.record_round(5, [(x, True, "ok") for x in rows], rules=bad)
    assert (r["rules_ok"], r["rules"]) == (1, 2) and g.totals(5)["rule_breaches"] == -5
    g.record_round(5, [(x, True, "ok") for x in rows], rules=bad)
    assert g.totals(5)["rule_breaches"] == -10                                                   # every round until it is fixed
    assert {c["host"]: c["ok"] for c in g.rules(5)["checks"]} == {"www": False, "dns1": True}
    assert all(z["good_pct"] == 100 for z in g.awareness(5))                                     # rules are not service availability


def test_the_team_plan_tracks_windows_check_ins_and_owners(game):
    g, _ = game
    with pytest.raises(KeyError):
        g.plan_mark(5, "blue-5", "nope", "done")
    with pytest.raises(ValueError):
        g.plan_mark(5, "blue-5", "t0-inventory", "finished")
    assert {i["state"] for i in g.plan(5)["items"]} == {"not started"}
    g.start(T0)
    g.plan_mark(5, "blue-5", "t0-inventory", "done")
    g.plan_mark(5, "blue-5", "t0-baseline", "blocked", "no access yet")
    p = g.plan(5, now=T0 + 25 * 60)
    st = {i["id"]: i["state"] for i in p["items"]}
    assert st["t0-inventory"] == "done" and st["t0-passwords"] == "overdue" and st["t0-baseline"] == "blocked" and st["t0-logging"] == "now" and st["t3-report"] == "later"
    assert p["next_checkin_minute"] == 60 and not p["checkin_due"]
    assert g.plan(5, now=T0 + 70 * 60)["checkin_due"]                                           # an hour in, no situation report yet


def test_compaction_keeps_the_file_small_and_the_report_unchanged(game):
    g, _ = game
    g.start()
    rows = scenario.checks(g.scenario())
    for i in range(30):
        g.record_round(5, [(r, not (r["host"] == "www" and i % 3 == 0), "x") for r in rows], usersim=[("alex.sample", "ws3-1", True, "ok")])
    before = g.after_action(5)
    n = g.db.execute("SELECT COUNT(*) FROM checks").fetchone()[0]
    assert g.compact(keep_rounds=5) == n - 5 * (len(rows) + 1)
    assert g.after_action(5) == before and g.verify() == [] and g.compact(keep_rounds=5) == 0
