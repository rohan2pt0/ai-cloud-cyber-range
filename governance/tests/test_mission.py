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


def test_the_after_action_review_counts_the_week_and_never_says_quiet_when_nothing_ran(tmp_path, monkeypatch):
    import time as _t
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    now = _t.time()
    hist = {"daily-backup": [{"t": _t.strftime("%Y-%m-%dT%H:%M", _t.localtime(now - 3600)), "code": 1, "tail": "disk full"},
                             {"t": _t.strftime("%Y-%m-%dT%H:%M", _t.localtime(now - 30 * 86400)), "code": 1, "tail": "old"}]}
    real_read = pathlib.Path.read_text

    def read(self, *a, **k):
        if self.name == ".history.json":
            return json.dumps(hist)
        if self.name == "watch.log":
            return _t.strftime("%Y-%m-%d %H:%M:%S", _t.localtime(now - 7200)) + " NOT READY — healing with ./securax up\n"
        return real_read(self, *a, **k)
    monkeypatch.setattr(pathlib.Path, "read_text", read)
    mi.log_event({"kind": "poll", "op": "update", "go": False, "no_go": ["backup"]})
    r = mi.aar(now)
    assert r["happened"]["routine runs"] == 1 and r["happened"]["routine failures"] == 1     # last month's run is not this week's
    assert r["happened"]["outages the watchdog healed"] == 1 and r["happened"]["updates held by Go/No-Go"] == 1
    assert any("daily-backup" in d for d in r["differed"]) and any("NO-GO from backup" in d for d in r["differed"])
    assert not any("quiet week" in k for k in r["keep"])
    hist.clear()
    r = mi.aar(now)
    assert any("no routine ran" in c for c in r["change"]) and not any("quiet week" in k for k in r["keep"])
    md = mi.aar_markdown(r, "2026-W43")
    assert md.startswith("# After-action review, week 2026-W43") and "## Change" in md


def test_the_cost_view_adds_only_what_the_owner_listed_and_measures_the_rest(tmp_path):
    subs = tmp_path / "subs.json"
    subs.write_text(json.dumps([{"name": "OpenCode Go", "per_month": 10, "currency": "USD"}, {"name": "VPS", "per_month": 500, "currency": "INR"},
                                {"name": "Domain", "per_month": 75, "currency": "INR"}]))
    fake = lambda: {"estate_bytes": 12_500_000_000, "backups": {"bytes": 2_000_000_000}, "disk": {"free_pct": 31.0}}
    c = mi.costs(measure=fake, budget=lambda: {"callers": [{"month_used": 1200}, {"month_used": 300}]}, subs_path=subs)
    assert c["money"] == {"USD": 10.0, "INR": 575.0} and c["machine"] == {"estate_gb": 12.5, "backups_gb": 2.0, "disk_free_pct": 31.0}
    assert c["tokens"] == {"this_month": 1500, "callers": 2}
    none = mi.costs(measure=fake, budget=lambda: (_ for _ in ()).throw(OSError("off")), subs_path=tmp_path / "missing.json")
    assert none["money"] == {} and "subscriptions.json" in none["money_note"] and "did not answer" in none["tokens"]["note"]


def test_the_command_center_line_says_go_or_why_not_and_what_needs_you():
    fresh = {"clean_age_h": 3.0, "newest_suspect": False}
    ok = mi.html_card([{"id": "disk", "status": "green", "value": "40% free"}], fresh)
    assert ok.startswith("<details") and "GO for the nightly update" in ok and "nothing needs you" in ok and "NO-GO" not in ok
    bad = mi.html_card([{"id": "disk", "status": "red", "value": "3% free"}, {"id": "anomalies", "status": "red", "value": "1"}],
                       {"clean_age_h": None, "newest_suspect": False})
    assert "NO-GO for the nightly update: backup, disk" in bad and "needs you: a key behaves unusually" in bad
    assert "the autopilot acts" in bad and "main build" not in bad          # the cockpit asks nothing over the network
    assert "https://" not in ok + bad and "<script" not in ok + bad
