"""./securax exercise: run a live-fire cyber defence exercise (doc 79).

    ./securax exercise plan   [--scenario FILE] [--team N]   check a scenario and show what the lite range would run
    ./securax exercise new    [--scenario FILE] [--team N] [--name NAME]   create an exercise; prints the sign-in tokens ONCE
    ./securax exercise lite up [GAME]                         start the lite range (containers, isolated networks, scoring, bots)
    ./securax exercise serve  [GAME] [--host 127.0.0.1] [--port 8097]   the portal for blue, white and red
    ./securax exercise start  [GAME]                          start the exercise clock (white team; also a button in the portal)
    ./securax exercise round  [GAME] [--lite]                 one scoring round from this machine (a full range reached over VPN)
    ./securax exercise attack [GAME] TARGET "objective" [--evidence TEXT]   a human red teamer's report from the terminal
    ./securax exercise revert [GAME] HOST                     rebuild one lite host from its image (costs the team points)
    ./securax exercise lite stop|down|status [GAME]           pause (state kept) / remove / show the lite range
    ./securax exercise report [GAME]                          after-action report (Markdown) in the exercise folder
    ./securax exercise verify [GAME]                          the score log has not been edited
    ./securax exercise list

GAME is an exercise name in vault/exercise/; it can be left out when there is only one.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import os
import pathlib
import re
import sys
import time

from . import checks, engine, lite, people
from . import scenario as scn

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOME = pathlib.Path(os.environ.get("SECURAX_EXERCISE_HOME") or ROOT / "vault" / "exercise")


def resolve(name: str | None) -> pathlib.Path:
    if name and pathlib.Path(name).is_dir() and (pathlib.Path(name) / "game.db").exists():
        return pathlib.Path(name)
    games = sorted(p.parent for p in HOME.glob("*/game.db")) if HOME.exists() else []
    if name:
        for g in games:
            if g.name == name:
                return g
        raise KeyError(f"No exercise called {name}. See them with:  ./securax exercise list")
    if len(games) == 1:
        return games[0]
    if not games:
        raise KeyError("No exercise yet. Create one with:  ./securax exercise new")
    raise KeyError("More than one exercise: name it. See them with:  ./securax exercise list")


def score_round(g: engine.Game, team: int, lite_only: bool, run_ssh=people.ssh_run) -> dict:
    sc = g.scenario(team)
    rows = lite.scored_rows(sc) if lite_only else scn.checks(sc)
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        results = list(ex.map(lambda r: (r, *checks.run(r)), rows))
    names = {h["name"] for h in (lite.deployed(sc) if lite_only else sc["hosts"])}
    key = g.dir / "lite" / "greenteam_ed25519"
    rules = people.rule_checks(g, team, names, str(key) if key.exists() else None)
    return g.record_round(team, results, people.usersim(g, team, names, run=run_ssh), rules=rules)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="./securax exercise", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    for name in ("plan", "new"):
        p = sub.add_parser(name)
        p.add_argument("--scenario")
        p.add_argument("--team", type=int)
        if name == "new":
            p.add_argument("--name", default="")
    for name in ("start", "report", "verify"):
        sub.add_parser(name).add_argument("game", nargs="?")
    p = sub.add_parser("serve")
    p.add_argument("game", nargs="?")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8097)
    p = sub.add_parser("round")
    p.add_argument("game", nargs="?")
    p.add_argument("--lite", action="store_true")
    p = sub.add_parser("run")                       # the scoring bot's loop (inside the lite range)
    p.add_argument("--game", required=True)
    p.add_argument("--lite", action="store_true")
    p.add_argument("--rounds", type=int, default=0)
    p = sub.add_parser("redbot")
    p.add_argument("--game", required=True)
    p.add_argument("--rounds", type=int, default=0)
    p.add_argument("--every", type=int, default=300)
    p = sub.add_parser("attack")
    p.add_argument("args", nargs="+")
    p.add_argument("--evidence", default="")
    p = sub.add_parser("revert")
    p.add_argument("args", nargs="+")
    p = sub.add_parser("lite")
    p.add_argument("action", choices=["up", "stop", "down", "status"])
    p.add_argument("game", nargs="?")
    sub.add_parser("list")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "plan":
            sc = scn.load(a.scenario, a.team)
            pl = lite.plan(sc)
            print(f"✔ {sc['name']} (team {sc['team']}): {len(sc['hosts'])} machines, {pl['checks_in_scenario']} scored checks, "
                  f"{len(sc['users'])} staff accounts, {len(sc['tasks'])} tasks, {len(sc['injects'])} news injects")
            print(f"  Lite range on this machine: {pl['containers']} containers (~{pl['ram_mb']} MB RAM), {pl['checks_scored_here']} checks scored here")
            if pl["goad"]:
                print(f"  From the GOAD Active Directory lab (./securax range): {', '.join(pl['goad'])}")
            if pl["full_range_only"]:
                print(f"  Full (cloud) range only, shown as not deployed here: {', '.join(pl['full_range_only'])}")
            for c in lite.clashes(sc):
                print(f"  ✗ {c}: choose another team number with --team")
        elif a.cmd == "new":
            sc = scn.load(a.scenario, a.team)
            slug = re.sub(r"[^a-z0-9]+", "-", (a.name or sc["name"].split(":")[-1]).lower()).strip("-")[:30] or "exercise"
            folder = HOME / f"EX-{dt.date.today():%Y%m%d}-{slug}"
            tokens = engine.Game.create(folder, a.scenario, a.team)
            tf = HOME / f"{folder.name}.tokens.txt"
            tf.write_text("".join(f"{k}: {v}\n" for k, v in tokens.items()))
            os.chmod(tf, 0o600)
            print(f"✔ exercise {folder.name} created for team {sc['team']}.\n  Sign-in tokens (also in {tf}, readable only by you):")
            for k, v in tokens.items():
                print(f"    {k:<8} {v}")
            print(f"  Next:  ./securax exercise lite up {folder.name}     then  ./securax exercise serve {folder.name}")
        elif a.cmd == "list":
            games = sorted(HOME.glob("*/game.db")) if HOME.exists() else []
            if not games:
                print("No exercise yet. Create one with:  ./securax exercise new")
            for f in games:
                g = engine.Game(f.parent)
                print(f"  {f.parent.name:<40} {g.phase()['name']:<12} team(s) {', '.join(map(str, g.teams))}")
        elif a.cmd == "start":
            g = engine.Game(resolve(a.game))
            g.start()
            print(f"✔ the clock is running: {g.phase()['name']} phase")
        elif a.cmd == "serve":
            from . import portal
            g = engine.Game(resolve(a.game))
            srv = portal.serve(g, a.host, a.port)
            if a.host not in ("127.0.0.1", "localhost"):
                print(f"  ! listening on {a.host}: anyone on that network can reach the sign-in page (the tokens still protect it)")
            print(f"✔ portal for {g.meta('name')}: http://{'127.0.0.1' if a.host == '0.0.0.0' else a.host}:{a.port}/  (Ctrl+C to stop)")
            try:
                srv.serve_forever()
            except KeyboardInterrupt:
                pass
        elif a.cmd == "round":
            g = engine.Game(resolve(a.game))
            r = score_round(g, g.teams[0], a.lite)
            print(f"  round {r['round']}: {r['services_up']}/{r['services']} services up, {r['logins_ok']}/{r['logins']} staff logins worked, "
                  f"{r['rules_ok']}/{r['rules']} rule checks kept, +{r['points']:g}")
        elif a.cmd == "run":
            g = engine.Game(pathlib.Path(a.game))
            n = 0
            while not a.rounds or n < a.rounds:
                t0 = time.time()
                if g.phase()["name"] == "Finished":
                    print("exercise finished: scoring stopped", flush=True)
                    return 0
                r = score_round(g, g.teams[0], a.lite)
                print(f"round {r['round']}: {r['services_up']}/{r['services']} up, {r['logins_ok']}/{r['logins']} logins, "
                      f"{r['rules_ok']}/{r['rules']} rules", flush=True)
                n += 1
                if not a.rounds or n < a.rounds:
                    time.sleep(max(1, g.scenario()["scoring"]["round_seconds"] - (time.time() - t0)))
        elif a.cmd == "redbot":
            g = engine.Game(pathlib.Path(a.game))
            sc = g.scenario()
            reach = set(sc.get("red_zones", lite.RED_ZONES))
            n = 0
            while not a.rounds or n < a.rounds:
                ids = people.redbot_round(g, g.teams[0], {h["name"] for h in lite.deployed(sc)}, reach)
                print(f"red-bot pass {n + 1}: {len(ids)} new foothold(s)", flush=True)
                n += 1
                if not a.rounds or n < a.rounds:
                    time.sleep(a.every)
        elif a.cmd == "attack":
            game, target, objective = ([None] + a.args)[-3:] if len(a.args) == 2 else a.args[:3]
            g = engine.Game(resolve(game))
            aid = g.attack(g.teams[0], "red", target, objective, a.evidence)
            print(f"✔ attack report {aid} on {target}: {g.scenario()['scoring']['attack_report']} points to the blue team")
        elif a.cmd == "revert":
            game, host = ([None] + a.args)[-2:] if len(a.args) == 1 else a.args[:2]
            folder = resolve(game)
            g = engine.Game(folder)
            scn.host(g.scenario(), host)
            rc, out = lite.compose(folder, "up", "-d", "--force-recreate", "--no-deps", host)
            if rc:
                print(out)
                return 1
            pen = g.restore(g.teams[0], "blue (revert)", host, "rebuilt from its image with ./securax exercise revert")
            print(f"✔ {host} rebuilt from its image ({pen:g} points, as restoring from backup)")
        elif a.cmd == "lite":
            folder = resolve(a.game)
            g = engine.Game(folder)
            if a.action == "up":
                bad = lite.clashes(g.scenario())
                if bad:
                    print("✗ " + "\n✗ ".join(bad) + "\n  Create the exercise with another --team number so the range cannot break your network.")
                    return 1
                rc, out = lite.build()
                if rc:
                    print("✗ building the range image failed:\n" + out)
                    return 1
                if g.scenario().get("green_team"):
                    lite.green_key(folder)
                lite.write(g.scenario(), folder, ROOT)
                rc, out = lite.compose(folder, "up", "-d")
                if rc:
                    print("✗ " + out)
                    return 1
                pl = lite.plan(g.scenario())
                print(f"✔ lite range up: {pl['containers']} containers on isolated networks.\n"
                      f"  Blue team:  ssh -p 2222 {g.scenario()['admin']['username']}@127.0.0.1   (the scenario's admin password; change it!)\n"
                      f"  Portal:     ./securax exercise serve {folder.name}")
            elif a.action == "stop":
                rc, out = lite.compose(folder, "stop")
                print("✔ range paused: containers stopped, their state kept. Resume with: ./securax exercise lite up" if not rc else out)
            elif a.action == "down":
                rc, out = lite.compose(folder, "down", "--remove-orphans")
                print("✔ range removed (the score, reports and logs stay in the exercise folder)" if not rc else out)
            else:
                rc, out = lite.compose(folder, "ps", "--format", "table {{.Name}}\t{{.Status}}")
                print(out)
            return rc
        elif a.cmd == "report":
            folder = resolve(a.game)
            g = engine.Game(folder)
            out = folder / f"after-action-{dt.datetime.now():%Y%m%d-%H%M}.md"
            out.write_text(g.after_action(g.teams[0]))
            print(f"✔ {out}")
        elif a.cmd == "verify":
            probs = engine.Game(resolve(a.game)).verify()
            print("✔ the score log verifies: no event was edited or removed" if not probs else "\n".join("✗ " + p for p in probs))
            return 1 if probs else 0
        else:
            print(__doc__)
        return 0
    except (KeyError, ValueError, FileExistsError, FileNotFoundError) as e:
        print(str(e).strip("'\""))
        return 1


if __name__ == "__main__":
    sys.exit(main())
