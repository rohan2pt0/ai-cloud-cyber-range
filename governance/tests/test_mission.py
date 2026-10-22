"""Mission control (doc 102): the Go/No-Go poll holds an update on any NO-GO and never on an unreachable GitHub alone;
flight rules fire on the cockpit's vital signs and the backup console; the autopilot acts only on its own rules, never on
the owner's; every command the crew and the rules name exists; and the nightly update asks the poll first."""
import importlib.util
import io
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("securax_mission_t", ROOT / "governance" / "mission.py")
mi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mi)
CLI = (ROOT / "securax").read_text("utf-8")


def state(age=3.0, suspect=False, ci=True, disk="green", incidents="green", **more):
    m = {"disk": {"status": disk, "value": "40% free"}, "incidents": {"status": incidents, "value": "none"}}
    m.update({k: {"status": v, "value": v} for k, v in more.items()})
    return {"backups": {"clean_age_h": age, "newest_suspect": suspect}, "ci_main": ci, "cockpit": m}


def test_all_go_and_each_console_can_hold_the_update():
    assert mi.poll("update", state())["go"]
    for s, console in ((state(suspect=True), "ransomware"), (state(age=None), "backup"), (state(age=40), "backup"),
                       (state(disk="red"), "disk"), (state(incidents="red"), "incidents"), (state(ci=False), "main build")):
        res = mi.poll("update", s)
        assert not res["go"] and [c["console"] for c in res["consoles"] if not c["go"]] == [console], console


def test_an_unreachable_github_is_not_a_no_go():
    res = mi.poll("update", state(ci=None))
    assert res["go"] and "could not be asked" in next(c["why"] for c in res["consoles"] if c["console"] == "main build")


def test_main_is_green_reads_the_last_finished_run_and_survives_errors():
    class R(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    ok = mi.main_is_green("o/r", opener=lambda req, timeout=0: R(json.dumps({"workflow_runs": [{"conclusion": "success"}]}).encode()))
    bad = mi.main_is_green("o/r", opener=lambda req, timeout=0: R(json.dumps({"workflow_runs": [{"conclusion": "failure"}]}).encode()))
    assert ok is True and bad is False
    assert mi.main_is_green("o/r", opener=lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))) is None
    assert mi.main_is_green("not a slug") is None


def test_rules_fire_on_their_signs_and_the_autopilot_acts_only_on_its_own():
    fired = {r["id"] for r in mi.rules(state(age=None, disk="red", anomalies="red")) if r["fires"]}
    assert {"backup-stale", "disk-red", "stolen-key-signs"} <= fired and "ransomware-suspected" not in fired
    ran = []
    done = mi.act(mi.rules(state(age=None, disk="red", anomalies="red")),
                  run=lambda argv, **k: ran.append(argv[2:]) or type("P", (), {"returncode": 0})())
    assert ["backup"] in ran and ["storage", "--auto"] in ran and all(d["ok"] for d in done)
    assert not any("gateway-auth" in " ".join(a) for a in ran)          # revoking a key is the owner's decision


def test_every_command_the_crew_and_the_rules_name_exists():
    spec = json.loads((ROOT / "governance" / "mission.json").read_text())
    names = {c for crew in spec["crew"] for c in crew["commands"]} | {r["cmd"][0] for r in spec["flight_rules"] if r["cmd"]}
    for n in names:
        assert f"\n  {n})" in CLI or f"|{n})" in CLI or f"  {n}|" in CLI, f"./securax {n} does not exist"
    assert len(spec["disciplines"]) == 12 and all(r["who"] in ("autopilot", "owner") for r in spec["flight_rules"])


def test_the_nightly_update_asks_the_poll_and_skips_a_second_backup():
    upd = CLI[CLI.index("\n  update)"):CLI.index("\n  update)") + 9000]
    assert 'governance/mission.py" poll update' in upd and "auto-update held" in upd
    assert "-mmin -120" in upd and "is the safety copy" in upd
