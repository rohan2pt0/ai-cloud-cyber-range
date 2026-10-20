"""The game: one SQLite file per exercise that holds checks, scores, tasks, reports, judging, attacks and password changes.

Score categories follow the ones live-fire exercise platforms show on a team timeline: availability (service checks and
simulated staff logging in), solve task, abandon task, use hint, attack reports (red-team successes, negative), incident
reports, situation reports, restore from backup (negative) and special (a manual adjustment by exercise control).

Every scoring event is hash-chained: `verify()` finds an edited, deleted or reordered event. Judging is done by people
(the white team); the engine only applies the limits the scenario sets, so no grade can exceed its maximum.

Roles and tokens: `create()` makes one token per role (white = exercise control and judges, red, blue-<team>). Only their
SHA-256 is stored. The game folder is private (0700) and lives under vault/exercise/.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import secrets
import sqlite3
import threading
import time

from . import frameworks as fw
from . import scenario as scn

CATEGORIES = ("availability", "solve_task", "abandon_task", "use_hint", "attack_reports", "incident_reports",
              "situation_reports", "restore_from_backup", "rule_breaches", "special")
INCIDENT_FIELDS = ("target", "compromised", "chronology", "impact", "source", "action_plan", "additional")
LIST_FIELDS = ("techniques", "defences")          # ATT&CK/ATLAS techniques seen, D3FEND/ATLAS defences used
SITREP_SECTIONS = ("event_overview", "adversary_assessment", "impact_on_operations", "actions_taken", "status", "other_business")
SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tokens (hash TEXT PRIMARY KEY, role TEXT NOT NULL, team INTEGER, label TEXT);
CREATE TABLE IF NOT EXISTS checks (id INTEGER PRIMARY KEY, round INTEGER, ts REAL, team INTEGER, host TEXT, zone TEXT,
    service TEXT, kind TEXT, ok INTEGER, detail TEXT);
CREATE INDEX IF NOT EXISTS checks_by_round ON checks (team, round);
CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, ts REAL, team INTEGER, category TEXT, points REAL, detail TEXT,
    actor TEXT, prev TEXT, hash TEXT);
CREATE TABLE IF NOT EXISTS submissions (id INTEGER PRIMARY KEY, kind TEXT, team INTEGER, actor TEXT, ts REAL, ref TEXT,
    body TEXT, status TEXT, points REAL, verdict TEXT, feedback TEXT, judge TEXT, judged_ts REAL);
CREATE TABLE IF NOT EXISTS attacks (id INTEGER PRIMARY KEY, ts REAL, team INTEGER, target TEXT, objective TEXT, evidence TEXT,
    actor TEXT, source TEXT, techniques TEXT);
CREATE TABLE IF NOT EXISTS creds (id INTEGER PRIMARY KEY, ts REAL, team INTEGER, username TEXT, system TEXT, password TEXT,
    reason TEXT, actor TEXT);
CREATE TABLE IF NOT EXISTS hints (team INTEGER, task TEXT, ts REAL, PRIMARY KEY (team, task));
CREATE TABLE IF NOT EXISTS plan (team INTEGER, item TEXT, status TEXT, note TEXT, ts REAL, actor TEXT, PRIMARY KEY (team, item));
CREATE TABLE IF NOT EXISTS check_summary (team INTEGER, host TEXT, service TEXT, kind TEXT, ok INTEGER, total INTEGER,
    PRIMARY KEY (team, host, service, kind));
"""


def _h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _iso(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat(timespec="seconds")


class Game:
    def __init__(self, folder: pathlib.Path | str):
        self.dir = pathlib.Path(folder)
        if not (self.dir / "game.db").exists():
            raise KeyError(f"No exercise in {self.dir}. Create one with:  ./securax exercise new")
        self.db = sqlite3.connect(self.dir / "game.db", check_same_thread=False, timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)                      # an exercise created by an older version gains any new table
        for table, col in (("tokens", "label"), ("attacks", "techniques")):  # ... and any new column
            if col not in {r["name"] for r in self.db.execute(f"PRAGMA table_info({table})")}:
                self.db.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
        self.lock = threading.RLock()
        self._sc: dict[int, dict] = {}

    # ─────────────────────────────── creation, identity, time ───────────────────────────────
    @staticmethod
    def create(folder: pathlib.Path | str, scenario_path: pathlib.Path | str | None = None, team: int | None = None) -> dict:
        folder = pathlib.Path(folder)
        if (folder / "game.db").exists():
            raise FileExistsError(f"{folder} already holds an exercise")
        raw = pathlib.Path(scenario_path or scn.SAMPLE).read_text("utf-8")
        sc = scn.load(scenario_path, team)                 # refuses a broken scenario before anything is written
        folder.mkdir(parents=True, exist_ok=True)
        os.chmod(folder, 0o700)
        db = sqlite3.connect(folder / "game.db")
        db.executescript(SCHEMA)
        tokens = {"white": secrets.token_urlsafe(18), "red": secrets.token_urlsafe(18), f"blue-{sc['team']}": secrets.token_urlsafe(18)}
        for role, tok in tokens.items():
            db.execute("INSERT INTO tokens VALUES (?,?,?,?)", (_h(tok), role.split("-")[0], sc["team"] if role.startswith("blue") else None, None))
        for k, v in {"scenario": raw, "teams": json.dumps([sc["team"]]), "name": sc["name"], "created": str(time.time()), "round": "0"}.items():
            db.execute("INSERT INTO meta VALUES (?,?)", (k, v))
        db.commit()
        db.close()
        os.chmod(folder / "game.db", 0o600)
        return tokens

    def meta(self, key: str, default: str | None = None) -> str | None:
        r = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return r["value"] if r else default

    def set_meta(self, key: str, value: str) -> None:
        with self.lock:
            self.db.execute("INSERT INTO meta VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    @property
    def teams(self) -> list[int]:
        return json.loads(self.meta("teams", "[]"))

    def scenario(self, team: int | None = None) -> dict:
        t = team if team is not None else self.teams[0]
        if t not in self._sc:
            tmp = self.dir / ".scenario.json"
            tmp.write_text(self.meta("scenario"))
            os.chmod(tmp, 0o600)
            self._sc[t] = scn.load(tmp, t)
        return self._sc[t]

    def auth(self, token: str) -> dict | None:
        if not token:
            return None
        r = self.db.execute("SELECT role, team, label FROM tokens WHERE hash=?", (_h(token),)).fetchone()
        if not r:
            return None
        return {"role": r["role"], "team": r["team"], **({"player": r["label"]} if r["label"] else {})}

    def add_player(self, team: int, name: str) -> str:
        """A personal blue-team token, so the portal can credit each person (XP, level, badges) as well as the team."""
        name = name.strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 ._-]{0,39}", name):
            raise ValueError("a player name is 1-40 letters, digits, spaces, dots, dashes or underscores, starting with a letter")
        if team not in self.teams:
            raise KeyError(f"no team {team} in this exercise")
        if self.db.execute("SELECT 1 FROM tokens WHERE team=? AND label=?", (team, name)).fetchone():
            raise ValueError(f"{name} is already a player in team {team}")
        tok = secrets.token_urlsafe(18)
        with self.lock:
            self.db.execute("INSERT INTO tokens VALUES (?,?,?,?)", (_h(tok), "blue", team, name))
        return tok

    def players(self, team: int) -> list[str]:
        return [r["label"] for r in self.db.execute("SELECT label FROM tokens WHERE team=? AND label IS NOT NULL ORDER BY label", (team,))]

    def start(self, at: float | None = None) -> float:
        if self.meta("started"):
            raise ValueError("this exercise has already started")
        t = at if at is not None else time.time()
        self.set_meta("started", str(t))
        return t

    def minute(self, now: float | None = None) -> float | None:
        s = self.meta("started")
        return None if s is None else ((now if now is not None else time.time()) - float(s)) / 60

    def phase(self, now: float | None = None) -> dict:
        m = self.minute(now)
        sc = self.scenario()
        if m is None:
            return {"name": "Not started", "about": "Exercise control has not started the clock yet.", "minute": None}
        for p in sc["phases"]:
            if m < p["until_minute"]:
                return {**p, "minute": round(m, 1)}
        return {"name": "Finished", "about": "The exercise is over.", "minute": round(m, 1)}

    # ─────────────────────────────── the hash-chained score log ───────────────────────────────
    def event(self, team: int, category: str, points: float, detail: dict, actor: str, ts: float | None = None) -> int:
        if category not in CATEGORIES:
            raise ValueError(f"unknown score category {category}")
        with self.lock:
            last = self.db.execute("SELECT hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
            prev = last["hash"] if last else "0" * 64
            t = float(ts if ts is not None else time.time())
            points = float(round(points, 2))                  # stored as REAL: hash exactly what reads back
            body = json.dumps([t, team, category, points, detail, actor], sort_keys=True)
            cur = self.db.execute("INSERT INTO events (ts, team, category, points, detail, actor, prev, hash) VALUES (?,?,?,?,?,?,?,?)",
                                  (t, team, category, points, json.dumps(detail, sort_keys=True), actor, prev, _h(prev + body)))
            return cur.lastrowid

    def verify(self) -> list[str]:
        out, prev, want = [], "0" * 64, None
        for r in self.db.execute("SELECT * FROM events ORDER BY seq"):
            if want is not None and r["seq"] != want:
                out.append(f"event {want} is missing (next is {r['seq']})")
            want = r["seq"] + 1
            body = json.dumps([r["ts"], r["team"], r["category"], r["points"], json.loads(r["detail"]), r["actor"]], sort_keys=True)
            if r["prev"] != prev or r["hash"] != _h(prev + body):
                out.append(f"event {r['seq']} was changed or does not follow the one before it")
            prev = r["hash"]
        last = self.db.execute("SELECT MAX(seq) m, COUNT(*) n FROM events").fetchone()
        if last["n"] and last["m"] != last["n"]:
            out.append("events were deleted from the score log")
        return out

    def totals(self, team: int) -> dict:
        t = {c: 0.0 for c in CATEGORIES}
        for r in self.db.execute("SELECT category, SUM(points) s FROM events WHERE team=? GROUP BY category", (team,)):
            t[r["category"]] = round(r["s"], 2)
        t["total"] = round(sum(t.values()), 2)
        return t

    def scorelog(self, team: int, limit: int = 200) -> list[dict]:
        return [{"seq": r["seq"], "time": _iso(r["ts"]), "category": r["category"], "points": r["points"], "detail": json.loads(r["detail"]),
                 "by": r["actor"]} for r in self.db.execute("SELECT * FROM events WHERE team=? ORDER BY seq DESC LIMIT ?", (team, limit))]

    def timeline(self, team: int, buckets: int = 120) -> dict:
        rows = self.db.execute("SELECT ts, category, points FROM events WHERE team=? ORDER BY seq", (team,)).fetchall()
        if not rows:
            return {"times": [], "series": {}}
        t0, t1 = rows[0]["ts"], max(rows[-1]["ts"], rows[0]["ts"] + 60)
        step = (t1 - t0) / buckets
        times = [t0 + step * (i + 1) for i in range(buckets)]
        run = {c: 0.0 for c in CATEGORIES}
        series = {c: [] for c in (*CATEGORIES, "total")}
        i = 0
        for t in times:
            while i < len(rows) and rows[i]["ts"] <= t + 1e-6:
                run[rows[i]["category"]] += rows[i]["points"]
                i += 1
            for c in CATEGORIES:
                series[c].append(round(run[c], 1))
            series["total"].append(round(sum(run.values()), 1))
        return {"times": [_iso(t) for t in times], "series": {c: v for c, v in series.items() if any(v) or c == "total"}}

    # ─────────────────────────────── checks and situational awareness ───────────────────────────────
    def record_round(self, team: int, results: list[tuple[dict, bool, str]], usersim: list[tuple[str, str, bool, str]] = (),
                     ts: float | None = None, rules: list[tuple[str, str, bool, str]] = ()) -> dict:
        """results: (check row, ok, detail); usersim: (username, host, ok, detail); rules: (host, rule, ok, detail).
        Scores one availability event per round, and one rule-breach event when any rule check failed."""
        sc = self.scenario(team)
        with self.lock:
            rnd = int(self.meta("round", "0")) + 1
            self.set_meta("round", str(rnd))
            t = ts if ts is not None else time.time()
            for row, ok, det in results:
                self.db.execute("INSERT INTO checks (round, ts, team, host, zone, service, kind, ok, detail) VALUES (?,?,?,?,?,?,?,?,?)",
                                (rnd, t, team, row["host"], row["zone"], row["service"], "service", int(ok), det))
            for user, hostname, ok, det in usersim:
                z = scn.host(sc, hostname)["zone"]
                self.db.execute("INSERT INTO checks (round, ts, team, host, zone, service, kind, ok, detail) VALUES (?,?,?,?,?,?,?,?,?)",
                                (rnd, t, team, hostname, z, f"user {user}", "usersim", int(ok), det))
            for hostname, rule, ok, det in rules:
                z = scn.host(sc, hostname)["zone"]
                self.db.execute("INSERT INTO checks (round, ts, team, host, zone, service, kind, ok, detail) VALUES (?,?,?,?,?,?,?,?,?)",
                                (rnd, t, team, hostname, z, rule, "rule", int(ok), det))
            broken = [(h, r) for h, r, ok, _ in rules if not ok]
            ok_s = sum(1 for _, ok, _ in results if ok)
            ok_u = sum(1 for *_, ok, _ in usersim if ok)
            pts = ok_s * sc["scoring"]["availability_per_check"] + ok_u * sc["scoring"]["usersim_per_login"]
            if self.minute(t) is not None:                       # nothing is scored before exercise control starts the clock
                self.event(team, "availability", pts, {"round": rnd, "services_up": ok_s, "services": len(results),
                                                       "user_logins_ok": ok_u, "user_logins": len(usersim)}, "scoring-bot", ts=t)
                if broken:
                    self.event(team, "rule_breaches", sc["scoring"]["rule_breach_per_round"] * len(broken),
                               {"round": rnd, "breaches": [f"{h}: {r}" for h, r in broken][:20]}, "rules-bot", ts=t)
        return {"round": rnd, "services_up": ok_s, "services": len(results), "logins_ok": ok_u, "logins": len(usersim), "points": pts,
                "rules_ok": len(rules) - len(broken), "rules": len(rules)}

    def compromised(self, team: int, now: float | None = None) -> set[str]:
        """Hosts with a red-team success in the last N minutes that no accepted incident report has answered since."""
        now = now if now is not None else time.time()
        win = self.scenario(team)["scoring"]["compromised_minutes"] * 60
        out = set()
        for a in self.db.execute("SELECT target, ts FROM attacks WHERE team=? AND ts>=?", (team, now - win)):
            ans = self.db.execute("SELECT 1 FROM submissions WHERE kind='incident' AND team=? AND ref=? AND ts>=? AND verdict='accepted'",
                                  (team, a["target"], a["ts"])).fetchone()
            if not ans:
                out.add(a["target"])
        return out

    def targets(self, team: int) -> list[dict]:
        sc = self.scenario(team)
        rnd = self.db.execute("SELECT MAX(round) r FROM checks WHERE team=?", (team,)).fetchone()["r"]
        latest = {}
        if rnd:
            for r in self.db.execute("SELECT * FROM checks WHERE team=? AND round=?", (team, rnd)):
                latest.setdefault(r["host"], []).append({"service": r["service"], "kind": r["kind"], "ok": bool(r["ok"]), "detail": r["detail"]})
        bad = self.compromised(team)
        return [{"host": h["name"], "fqdn": f"{h['name']}.{sc.get('domain', '')}".rstrip("."), "zone": h["zone"], "ip": h["ip"], "about": h.get("about", ""),
                 "deployed": h["name"] in latest or not h.get("services"), "compromised": h["name"] in bad, "checks": latest.get(h["name"], []),
                 "round": rnd} for h in sc["hosts"]]

    def awareness(self, team: int) -> list[dict]:
        sc = self.scenario(team)
        zones = {z: {"zone": z, "label": d["label"], "good": 0, "compromised": 0, "not_available": 0} for z, d in sc["zones"].items()}
        for t in self.targets(team):
            for c in t["checks"]:
                if c["kind"] == "rule":
                    continue
                k = "not_available" if not c["ok"] else "compromised" if t["compromised"] else "good"
                zones[t["zone"]][k] += 1
        for z in zones.values():
            n = z["good"] + z["compromised"] + z["not_available"]
            z.update({k + "_pct": round(100 * z[k] / n, 1) if n else 0 for k in ("good", "compromised", "not_available")})
        return [z for z in zones.values() if z["good"] + z["compromised"] + z["not_available"]]

    def news(self, now: float | None = None) -> list[dict]:
        m = self.minute(now)
        if m is None:
            return []
        start = float(self.meta("started"))
        return [{"title": i["title"], "body": i["body"], "time": _iso(start + i["at_minute"] * 60)}
                for i in sorted(self.scenario()["injects"], key=lambda i: -i["at_minute"]) if i["at_minute"] <= m]

    # ─────────────────────────────── the mission board ───────────────────────────────
    def _task(self, team: int, task_id: str) -> dict:
        for t in self.scenario(team)["tasks"]:
            if t["id"] == task_id:
                return t
        raise KeyError(f"no task {task_id}")

    def tasks(self, team: int, now: float | None = None) -> list[dict]:
        m = self.minute(now)
        hints = {r["task"] for r in self.db.execute("SELECT task FROM hints WHERE team=?", (team,))}
        out = []
        for t in self.scenario(team)["tasks"]:
            subs = [dict(r) for r in self.db.execute("SELECT id, ts, actor, status, points, verdict, feedback FROM submissions WHERE kind='task' AND team=? AND ref=? ORDER BY id",
                                                      (team, t["id"]))]
            is_open = m is not None and m >= t.get("opens_at_minute", 0)
            status = ("abandoned" if any(s["status"] == "abandoned" for s in subs) else "solved" if any(s["status"] == "graded" for s in subs)
                      else "validating" if any(s["status"] == "pending" for s in subs) else "open" if is_open else "locked")
            row = {"id": t["id"], "phase": t["phase"], "title": t["title"] if is_open else "Locked task", "points": t["points"] if is_open else None,
                   "status": status, "opens_at_minute": t.get("opens_at_minute", 0)}
            if is_open:
                row.update({"description": t["description"], "question": t["question"], "has_hint": bool(t.get("hint")),
                            "hint": t.get("hint") if t["id"] in hints else None, "submissions": [{**s, "time": _iso(s.pop("ts"))} for s in subs]})
            out.append(row)
        return out

    def _open_or_raise(self, team: int, task_id: str) -> dict:
        t = self._task(team, task_id)
        st = next(x for x in self.tasks(team) if x["id"] == task_id)["status"]
        if st == "locked":
            raise ValueError("that task is not open yet")
        if st in ("abandoned", "solved"):
            raise ValueError(f"that task is already {st}")
        return t

    def submit_task(self, team: int, actor: str, task_id: str, answer: str) -> int:
        self._open_or_raise(team, task_id)
        if not answer.strip():
            raise ValueError("write an answer first")
        with self.lock:
            return self.db.execute("INSERT INTO submissions (kind, team, actor, ts, ref, body, status) VALUES ('task',?,?,?,?,?,'pending')",
                                   (team, actor, time.time(), task_id, json.dumps({"answer": answer[:20000]}))).lastrowid

    def use_hint(self, team: int, actor: str, task_id: str) -> str:
        t = self._open_or_raise(team, task_id)
        if not t.get("hint"):
            raise ValueError("this task has no hint")
        with self.lock:
            if not self.db.execute("SELECT 1 FROM hints WHERE team=? AND task=?", (team, task_id)).fetchone():
                self.db.execute("INSERT INTO hints VALUES (?,?,?)", (team, task_id, time.time()))
                self.event(team, "use_hint", -t["points"] * self.scenario(team)["scoring"]["hint_fraction"], {"task": task_id}, actor)
        return t["hint"]

    def abandon_task(self, team: int, actor: str, task_id: str) -> float:
        t = self._open_or_raise(team, task_id)
        pen = -t["points"] * self.scenario(team)["scoring"]["abandon_fraction"]
        with self.lock:
            self.db.execute("INSERT INTO submissions (kind, team, actor, ts, ref, body, status, points) VALUES ('task',?,?,?,?,?,'abandoned',?)",
                            (team, actor, time.time(), task_id, "{}", pen))
            self.event(team, "abandon_task", pen, {"task": task_id}, actor)
        return pen

    # ─────────────────────────────── reports, attacks, judging ───────────────────────────────
    def file_incident(self, team: int, actor: str, body: dict) -> int:
        sc = self.scenario(team)
        scn.host(sc, body.get("target", ""))                 # KeyError for an unknown target
        clean = {k: str(body.get(k, ""))[:8000] for k in INCIDENT_FIELDS}
        clean["compromised"] = bool(body.get("compromised"))
        for k in LIST_FIELDS:
            vals = [str(x) for x in (body.get(k) or [])][:30]
            bad = fw.unknown(vals)
            if bad:
                raise ValueError(f"{', '.join(bad)}: not in the framework catalogue")
            clean[k] = vals
        if not clean["chronology"].strip():
            raise ValueError("say what happened and when (chronology)")
        with self.lock:
            return self.db.execute("INSERT INTO submissions (kind, team, actor, ts, ref, body, status) VALUES ('incident',?,?,?,?,?,'pending')",
                                   (team, actor, time.time(), clean["target"], json.dumps(clean))).lastrowid

    def file_sitrep(self, team: int, actor: str, sections: dict) -> int:
        clean = {k: str(sections.get(k, ""))[:8000] for k in SITREP_SECTIONS}
        if not any(v.strip() for v in clean.values()):
            raise ValueError("a situation report needs at least one section filled in")
        with self.lock:
            return self.db.execute("INSERT INTO submissions (kind, team, actor, ts, ref, body, status) VALUES ('sitrep',?,?,?,'',?,'pending')",
                                   (team, actor, time.time(), json.dumps(clean))).lastrowid

    def submissions(self, team: int | None = None, kind: str | None = None, pending_only: bool = False) -> list[dict]:
        q, a = "SELECT * FROM submissions WHERE status!='abandoned'", []
        if team is not None:
            q, a = q + " AND team=?", a + [team]
        if kind:
            q, a = q + " AND kind=?", a + [kind]
        if pending_only:
            q += " AND status='pending'"
        out = []
        for r in self.db.execute(q + " ORDER BY id DESC", a):
            d = dict(r)
            d["body"] = json.loads(d["body"])
            d["time"] = _iso(d.pop("ts"))
            d["judged_time"] = _iso(d.pop("judged_ts")) if r["judged_ts"] else None
            if d["kind"] == "incident":               # what the red team actually reported on that target, for the judge
                d["red_reports"] = [dict(x, time=_iso(x["ts"])) for x in self.db.execute(
                    "SELECT id, ts, objective, source FROM attacks WHERE team=? AND target=? ORDER BY id DESC LIMIT 5", (r["team"], r["ref"]))]
            out.append(d)
        return out

    def judge(self, sub_id: int, judge: str, points: float, verdict: str, feedback: str = "") -> float:
        with self.lock:
            r = self.db.execute("SELECT * FROM submissions WHERE id=?", (sub_id,)).fetchone()
            if not r:
                raise KeyError(f"no submission {sub_id}")
            if r["status"] != "pending":
                raise ValueError("that submission has already been judged")
            if verdict not in ("accepted", "rejected"):
                raise ValueError("verdict must be accepted or rejected")
            sc = self.scenario(r["team"])["scoring"]
            if r["kind"] == "task":
                cap, cat = self._task(r["team"], r["ref"])["points"], "solve_task"
            elif r["kind"] == "incident":
                cap, cat = sc["incident_report_max"], "incident_reports"
            else:
                if points != int(points) or not 0 <= points <= sc["situation_report_max_grade"]:
                    raise ValueError(f"a situation report is graded 0 to {sc['situation_report_max_grade']}")
                cap, cat, points = sc["situation_report_max_grade"] * sc["situation_report_per_grade"], "situation_reports", points * sc["situation_report_per_grade"]
            if verdict == "rejected":
                points = 0
            if not 0 <= points <= cap:
                raise ValueError(f"points must be 0 to {cap} for this submission")
            status = "rejected" if r["kind"] == "task" and verdict == "rejected" else "graded"     # a rejected task answer may be tried again
            self.db.execute("UPDATE submissions SET status=?, points=?, verdict=?, feedback=?, judge=?, judged_ts=? WHERE id=?",
                            (status, points, verdict, feedback[:4000], judge, time.time(), sub_id))
            if points:
                self.event(r["team"], cat, points, {"submission": sub_id, "kind": r["kind"], "ref": r["ref"], "verdict": verdict}, judge)
        return points

    def attack(self, team: int, actor: str, target: str, objective: str, evidence: str = "", source: str = "human",
               techniques: list[str] | None = None) -> int:
        ph = self.phase()
        if not ph.get("attacks_allowed"):
            raise ValueError(f"no attacks are scored in the {ph['name'].lower()} phase")
        scn.host(self.scenario(team), target)
        if not objective.strip():
            raise ValueError("say what the attack achieved (objective)")
        techniques = [str(x) for x in (techniques or [])][:10]
        bad = fw.unknown(techniques) + [x for x in techniques if fw.kind_of(x) == "d3fend"]
        if bad:
            raise ValueError(f"{', '.join(bad)}: name ATT&CK or ATLAS techniques from the catalogue")
        with self.lock:
            aid = self.db.execute("INSERT INTO attacks (ts, team, target, objective, evidence, actor, source, techniques) VALUES (?,?,?,?,?,?,?,?)",
                                  (time.time(), team, target, objective[:2000], evidence[:8000], actor, source, json.dumps(techniques))).lastrowid
            self.event(team, "attack_reports", self.scenario(team)["scoring"]["attack_report"], {"attack": aid, "target": target, "objective": objective[:200]}, actor)
        return aid

    def attacks(self, team: int) -> list[dict]:
        return [dict(r, time=_iso(r["ts"]), technique_list=json.loads(r["techniques"] or "[]"))
                for r in self.db.execute("SELECT * FROM attacks WHERE team=? ORDER BY id DESC", (team,))]

    def restore(self, team: int, actor: str, host: str, reason: str) -> float:
        scn.host(self.scenario(team), host)
        pen = self.scenario(team)["scoring"]["restore_from_backup"]
        self.event(team, "restore_from_backup", pen, {"host": host, "reason": reason[:500]}, actor)
        return pen

    def special(self, team: int, actor: str, points: float, reason: str) -> None:
        if not reason.strip():
            raise ValueError("a special adjustment needs a reason")
        self.event(team, "special", points, {"reason": reason[:500]}, actor)

    # ─────────────────────────────── documented password changes ───────────────────────────────
    def cred_change(self, team: int, actor: str, username: str, system: str, password: str, reason: str) -> int:
        if username not in {u["username"] for u in self.scenario(team)["users"]}:
            raise KeyError(f"{username} is not one of the staff accounts in this scenario")
        if not password or not reason.strip():
            raise ValueError("give the new password and a short reason")
        with self.lock:
            return self.db.execute("INSERT INTO creds (ts, team, username, system, password, reason, actor) VALUES (?,?,?,?,?,?,?)",
                                   (time.time(), team, username, system[:200], password[:200], reason[:500], actor)).lastrowid

    def creds(self, team: int) -> list[dict]:
        return [dict(r, time=_iso(r["ts"])) for r in self.db.execute("SELECT * FROM creds WHERE team=? ORDER BY id DESC", (team,))]

    def password(self, team: int, username: str, system: str = "") -> str:
        """The password the simulated user will try on a system: the latest change documented for that system (or for "all",
        as for a domain account), otherwise the scenario's original one."""
        r = self.db.execute("SELECT password FROM creds WHERE team=? AND username=? AND (system=? OR lower(system) IN ('all', '*', '')) ORDER BY id DESC LIMIT 1",
                            (team, username, system)).fetchone()
        if r:
            return r["password"]
        return next(u["password"] for u in self.scenario(team)["users"] if u["username"] == username)

    # ─────────────────────────────── rules and the team plan ───────────────────────────────
    def rules(self, team: int) -> dict:
        sc = self.scenario(team)
        rnd = self.db.execute("SELECT MAX(round) r FROM checks WHERE team=? AND kind='rule'", (team,)).fetchone()["r"]
        latest = [dict(r) for r in self.db.execute("SELECT host, service AS rule, ok, detail FROM checks WHERE team=? AND kind='rule' AND round=?",
                                                     (team, rnd))] if rnd else []
        return {"rules": sc["rules"], "green_team": sc.get("green_team"), "checks": latest,
                "breach_points_per_round": sc["scoring"]["rule_breach_per_round"]}

    def plan(self, team: int, now: float | None = None) -> dict:
        sc = self.scenario(team)
        m = self.minute(now)
        st = {r["item"]: dict(r) for r in self.db.execute("SELECT * FROM plan WHERE team=?", (team,))}
        items = []
        for i in sorted(sc["playbook"], key=lambda i: (i["from_minute"], i["to_minute"])):
            s = st.get(i["id"], {})
            done = s.get("status") == "done"
            state = ("done" if done else "blocked" if s.get("status") == "blocked" else "not started" if m is None
                     else "overdue" if m > i["to_minute"] else "now" if m >= i["from_minute"] else "later")
            items.append({**i, "state": state, "note": s.get("note") or "", "by": s.get("actor"), "time": _iso(s["ts"]) if s.get("ts") else None})
        every = sc.get("checkins_every_minutes")
        nxt = last_sitrep = None
        if every and m is not None:
            nxt = (int(m // every) + 1) * every
            r = self.db.execute("SELECT MAX(ts) t FROM submissions WHERE kind='sitrep' AND team=?", (team,)).fetchone()["t"]
            last_sitrep = round((r - float(self.meta("started"))) / 60, 1) if r else None
        return {"items": items, "minute": None if m is None else round(m, 1), "checkins_every_minutes": every,
                "next_checkin_minute": nxt, "last_situation_report_minute": last_sitrep,
                "checkin_due": bool(every and m is not None and m >= every and (last_sitrep is None or m - last_sitrep > every))}

    def plan_mark(self, team: int, actor: str, item: str, status: str, note: str = "") -> None:
        if item not in {i["id"] for i in self.scenario(team)["playbook"]}:
            raise KeyError(f"no plan item {item}")
        if status not in ("done", "blocked", "todo"):
            raise ValueError("status must be done, blocked or todo")
        with self.lock:
            self.db.execute("INSERT INTO plan VALUES (?,?,?,?,?,?) ON CONFLICT(team, item) DO UPDATE SET status=excluded.status, "
                            "note=excluded.note, ts=excluded.ts, actor=excluded.actor", (team, item, status, note[:1000], time.time(), actor))

    # ─────────────────────────────── keeping the file small ───────────────────────────────
    def compact(self, keep_rounds: int = 1440) -> int:
        """Fold all but the newest `keep_rounds` scoring rounds into per-check totals. The score log, reports and the
        after-action report are unchanged; only the per-round detail of old rounds goes. Returns the rows removed."""
        with self.lock:
            last = self.db.execute("SELECT MAX(round) r FROM checks").fetchone()["r"] or 0
            cut = last - keep_rounds
            if cut <= 0:
                return 0
            for r in self.db.execute("SELECT team, host, service, kind, SUM(ok) ok, COUNT(*) n FROM checks WHERE round<=? GROUP BY team, host, service, kind",
                                     (cut,)).fetchall():
                self.db.execute("INSERT INTO check_summary VALUES (?,?,?,?,?,?) ON CONFLICT(team, host, service, kind) DO UPDATE SET "
                                "ok=ok+excluded.ok, total=total+excluded.total", (r["team"], r["host"], r["service"], r["kind"], r["ok"], r["n"]))
            n = self.db.execute("DELETE FROM checks WHERE round<=?", (cut,)).rowcount
        self.db.execute("VACUUM")
        return n

    def _check_totals(self, team: int, kind: str) -> list[dict]:
        """Per host and service: failed and total checks, over the kept rounds plus the folded summary."""
        rows = {}
        for r in self.db.execute("SELECT host, service, SUM(ok) ok, COUNT(*) n FROM checks WHERE team=? AND kind=? GROUP BY host, service", (team, kind)):
            rows[(r["host"], r["service"])] = [r["ok"], r["n"]]
        for r in self.db.execute("SELECT host, service, ok, total FROM check_summary WHERE team=? AND kind=?", (team, kind)):
            v = rows.setdefault((r["host"], r["service"]), [0, 0])
            v[0] += r["ok"]
            v[1] += r["total"]
        return [{"host": h, "service": s, "ok": ok, "total": n, "failed": n - ok} for (h, s), (ok, n) in rows.items()]

    # ─────────────────────────────── after-action report ───────────────────────────────
    def after_action(self, team: int) -> str:
        sc = self.scenario(team)
        tot = self.totals(team)
        probs = self.verify()
        svc = self._check_totals(team, "service")
        rounds = {"n": self.meta("round"), "ok": sum(x["ok"] for x in svc), "c": sum(x["total"] for x in svc)}
        L = [f"# After-action report: {sc['name']} (team {team})", "",
             f"Integrity: {'the score log verifies' if not probs else 'PROBLEMS: ' + '; '.join(probs)}.", "",
             "## Score", "", "| category | points |", "|---|---|"]
        L += [f"| {c.replace('_', ' ')} | {tot[c]:g} |" for c in CATEGORIES if tot[c]] + [f"| **total** | **{tot['total']:g}** |", ""]
        if rounds["c"]:
            L += [f"Service availability: {100 * rounds['ok'] / rounds['c']:.1f}% of {rounds['c']} checks over {rounds['n']} rounds.", ""]
        L += ["## Services that were down most", "", "| host | service | failed checks |", "|---|---|---|"]
        for r in sorted((x for x in svc + self._check_totals(team, "usersim") if x["failed"]), key=lambda x: -x["failed"])[:10]:
            L.append(f"| {r['host']} | {r['service']} | {r['failed']} |")
        breaches = [x for x in self._check_totals(team, "rule") if x["failed"]]
        if breaches:
            L += ["", "## Rule breaches", "", "| host | rule | rounds in breach |", "|---|---|---|"]
            L += [f"| {r['host']} | {r['service']} | {r['failed']} |" for r in breaches]
        L += ["", "## Red-team successes", ""]
        atk = self.attacks(team)
        L += [f"- {a['time']} **{a['target']}**: {a['objective']} ({a['source']})" for a in atk] or ["None recorded."]
        cov = fw.coverage(self, team)
        L += ["", "## Framework coverage (MITRE ATT&CK, D3FEND, ATLAS)", "",
              f"Met {cov['counts']['met']} techniques, detected {cov['counts']['detected']}, applied {cov['counts']['applied']} defences.", "",
              "| id | name | met | detected | applied |", "|---|---|---|---|---|"]
        L += [f"| [{r['id']}]({r['url']}) | {r['name']} | {'yes' if r['met'] else ''} | {'yes' if r['detected'] else ''} | {'yes' if r['applied'] else ''} |" for r in cov["rows"]]
        L += ["", "## Tasks", "", "| task | status |", "|---|---|"]
        L += [f"| {t['title']} | {t['status']} |" for t in self.tasks(team)]
        L += ["", "## Reports and judging", ""]
        for s in self.submissions(team):
            if s["kind"] != "task":
                L.append(f"- {s['time']} {s['kind']} {s['ref']}: {s['status']}" + (f", {s['points']:g} points, {s['verdict']}: {s['feedback']}" if s["status"] == "graded" else ""))
        L += ["", "_Generated by `./securax exercise report`. Judging is by people; the scores are what they awarded within the scenario's limits._"]
        return "\n".join(L) + "\n"
