"""The exercise portal: the scoring and situational-awareness screens a live-fire exercise gives its teams, in one small web app.

Who sees what:
    blue   its own team only: overview, the rules, the team plan, scoring log, timeline, target checks, team awareness, news,
           the mission board, incident and situation reports, documented password changes, and "we restored a host from backup"
    white  exercise control and judges: every team, the judging queues, special adjustments, the red team's reports, the clock
    red    the target list and its own attack reports; never the blue team's reports

Each person signs in with the token for their role (`./securax exercise new` prints them once). Requests carry it as a
Bearer header, so there are no cookies to steal and no cross-site form posts. Standard library only; it listens on
127.0.0.1 unless you choose otherwise.
"""
from __future__ import annotations

import json
import pathlib
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import engine

WEB = pathlib.Path(__file__).resolve().parent / "web"
STATIC = {"/": ("app.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/app.css": ("app.css", "text/css; charset=utf-8")}
HEADERS = {"Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'",
           "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY", "Cache-Control": "no-store"}
MAX_BODY = 256 * 1024
FAIL_LIMIT = 20                       # wrong tokens per address per minute before that address is refused for a minute


class Forbidden(Exception):
    pass


def make_handler(game: engine.Game):
    fails: dict[str, list[float]] = {}
    lock = threading.Lock()

    class H(BaseHTTPRequestHandler):
        server_version = "securax-exercise"
        sys_version = ""

        def log_message(self, *a):
            pass

        def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8"):
            self.send_response(code)
            for k, v in {**HEADERS, "Content-Type": ctype, "Content-Length": str(len(body))}.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj):
            self._send(code, json.dumps(obj, default=str).encode())

        def _who(self) -> dict | None:
            ip = self.client_address[0]
            now = time.time()
            with lock:
                recent = [t for t in fails.get(ip, []) if now - t < 60]
                fails[ip] = recent
                if len(recent) >= FAIL_LIMIT:
                    raise Forbidden("too many wrong tokens from your address; wait a minute")
            tok = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            who = game.auth(tok)
            if not who:
                with lock:
                    fails[ip].append(now)
            return who

        def _team(self, who: dict, q: dict) -> int:
            if who["role"] == "blue":
                return who["team"]
            t = q.get("team", [None])[0]
            return int(t) if t else game.teams[0]

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                raise ValueError("request too large")
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                raise ValueError("send JSON")
            data = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(data, dict):
                raise ValueError("send a JSON object")
            return data

        def _need(self, who: dict, *roles: str):
            if who["role"] not in roles:
                raise Forbidden(f"your role ({who['role']}) cannot do that")

        def do_GET(self):
            u = urlparse(self.path)
            if u.path in STATIC:
                name, ctype = STATIC[u.path]
                return self._send(200, (WEB / name).read_bytes(), ctype)
            if not u.path.startswith("/api/"):
                return self._json(404, {"error": "not found"})
            self._api("GET", u.path, parse_qs(u.query))

        def do_POST(self):
            u = urlparse(self.path)
            self._api("POST", u.path, parse_qs(u.query))

        def _api(self, method: str, path: str, q: dict):
            try:
                who = self._who()
                if not who:
                    return self._json(401, {"error": "sign in with your exercise token"})
                self._json(200, self.route(method, path, q, who))
            except Forbidden as e:
                self._json(403, {"error": str(e)})
            except KeyError as e:
                self._json(404, {"error": str(e).strip("'\"")})
            except (ValueError, json.JSONDecodeError) as e:
                self._json(400, {"error": str(e)})

        def route(self, method: str, path: str, q: dict, who: dict):
            team = self._team(who, q)
            actor = who["role"] if who["role"] != "blue" else f"blue-{who['team']}"
            if method == "GET":
                if path == "/api/me":
                    return {**who, "name": game.meta("name"), "teams": game.teams}
                if path == "/api/overview":
                    return {"name": game.meta("name"), "phase": game.phase(), "team": team, "teams": game.teams,
                            "totals": game.totals(team) if who["role"] != "red" else None}
                if path == "/api/targets":
                    t = game.targets(team)
                    return t if who["role"] != "red" else [{k: x[k] for k in ("host", "fqdn", "zone", "ip", "about")} for x in t]
                if path == "/api/news":
                    return game.news()
                if path == "/api/rules":
                    r = game.rules(team)
                    return r if who["role"] != "red" else {"rules": r["rules"]}
                if who["role"] == "red":
                    if path == "/api/attacks":
                        return [a for a in game.attacks(team) if a["actor"] == "red" or a["source"] == "bot"]
                    raise Forbidden("the red team sees targets and its own reports only")
                if path == "/api/scorelog":
                    return game.scorelog(team)
                if path == "/api/timeline":
                    return game.timeline(team)
                if path == "/api/awareness":
                    return game.awareness(team)
                if path == "/api/tasks":
                    return game.tasks(team)
                if path == "/api/reports":
                    kind = q.get("kind", [None])[0]
                    pending = q.get("pending", ["0"])[0] == "1"
                    subs = game.submissions(None if who["role"] == "white" and q.get("all") else team, kind, pending)
                    if who["role"] == "blue":
                        for s in subs:
                            s.pop("red_reports", None)           # blue never sees the red team's claims
                    return subs
                if path == "/api/creds":
                    return game.creds(team)
                if path == "/api/plan":
                    return game.plan(team)
                if path == "/api/attacks":
                    self._need(who, "white")
                    return game.attacks(team)
                if path == "/api/verify":
                    self._need(who, "white")
                    return {"problems": game.verify()}
                raise KeyError("no such page")
            b = self._body()
            m = re.fullmatch(r"/api/tasks/([\w.-]+)/(submit|hint|abandon)", path)
            if m:
                self._need(who, "blue")
                tid, act = m.groups()
                if act == "submit":
                    return {"id": game.submit_task(team, actor, tid, str(b.get("answer", "")))}
                if act == "hint":
                    return {"hint": game.use_hint(team, actor, tid)}
                return {"points": game.abandon_task(team, actor, tid)}
            m = re.fullmatch(r"/api/plan/([\w.-]+)", path)
            if m:
                self._need(who, "blue")
                game.plan_mark(team, actor, m.group(1), str(b.get("status", "")), str(b.get("note", "")))
                return {"ok": True}
            if path == "/api/incident":
                self._need(who, "blue")
                return {"id": game.file_incident(team, actor, b)}
            if path == "/api/sitrep":
                self._need(who, "blue")
                return {"id": game.file_sitrep(team, actor, b)}
            if path == "/api/creds":
                self._need(who, "blue")
                return {"id": game.cred_change(team, actor, str(b.get("username", "")), str(b.get("system", "")), str(b.get("password", "")),
                                               str(b.get("reason", "")))}
            if path == "/api/restore":
                self._need(who, "blue")
                return {"points": game.restore(team, actor, str(b.get("host", "")), str(b.get("reason", "")))}
            if path == "/api/attack":
                self._need(who, "red", "white")
                return {"id": game.attack(team, actor, str(b.get("target", "")), str(b.get("objective", "")), str(b.get("evidence", "")))}
            m = re.fullmatch(r"/api/judge/(\d+)", path)
            if m:
                self._need(who, "white")
                return {"points": game.judge(int(m.group(1)), actor, float(b.get("points", 0)), str(b.get("verdict", "")), str(b.get("feedback", "")))}
            if path == "/api/special":
                self._need(who, "white")
                game.special(team, actor, float(b.get("points", 0)), str(b.get("reason", "")))
                return {"ok": True}
            if path == "/api/start":
                self._need(who, "white")
                return {"started": game.start()}
            raise KeyError("no such action")

    return H


def serve(game: engine.Game, host: str = "127.0.0.1", port: int = 8097) -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer((host, port), make_handler(game))
    srv.daemon_threads = True
    return srv
