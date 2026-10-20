"""The lite range's safety rails and the people in it, without starting a container: the generated compose file is
isolated, mounts no private data, and the simulated staff and red-team bot follow the exercise's rules."""
import json
import pathlib
import random
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from exercise import engine, lite, people, scenario  # noqa: E402


def test_the_lite_range_is_isolated_and_mounts_no_private_data(tmp_path):
    sc = scenario.load(team=9)
    f = lite.write(sc, tmp_path / "EX-1", ROOT)
    c = json.loads(f.read_text())
    zones = {k: v for k, v in c["networks"].items() if k.startswith("z-")}
    assert zones and all(v["internal"] is True for v in zones.values())          # no zone can reach the internet or the LAN
    published = {n: s["ports"] for n, s in c["services"].items() if s.get("ports")}
    assert published == {"terminal": ["127.0.0.1:2222:22"]}                       # one door, on this machine only
    assert "access" in c["services"]["terminal"]["networks"] and all("access" not in s["networks"] for n, s in c["services"].items() if n != "terminal")
    for name in ("scoring-bot", "red-bot"):
        vols = c["services"][name]["volumes"]
        assert any(v.endswith(":/securax/exercise:ro") for v in vols) and not any(v.startswith(f"{ROOT}:") for v in vols)   # never the whole repo or vault
    assert {n["ipv4_address"] for n in c["services"]["scoring-bot"]["networks"].values()} >= {"10.9.1.252", "10.9.3.252"}
    assert set(c["services"]["red-bot"]["networks"]) == {"z-dmz", "z-cloud", "z-wifi"}   # an outsider's view: public zones and guest Wi-Fi
    assert "dc1" not in c["services"] and "fw" not in c["services"]               # Windows and network gear are not containers
    users = (tmp_path / "EX-1" / "lite" / "hosts" / "ws3-1" / "users").read_text()
    assert "rangeadmin:Sample-Admin-1!" in users and "alex.sample:" in users and "cam.fiction" not in users
    assert lite.plan(sc)["checks_scored_here"] == len(lite.scored_rows(sc)) < len(scenario.checks(sc))


def test_a_subnet_that_clashes_with_this_machine_is_refused():
    sc = scenario.load(team=9)
    routes = "default via 192.168.1.1 dev wlan0\n10.9.0.0/16 dev tun0 scope link\n10.188.0.0/16 dev br-abc123 scope link\n"
    bad = lite.clashes(sc, routes)
    assert bad and all("tun0" in b for b in bad) and not any("br-abc123" in b for b in bad)   # a VPN route clashes; Docker's own does not
    assert lite.clashes(sc, "default via 192.168.1.1 dev wlan0\n") == []


def _game(tmp_path, minutes_in: float):
    engine.Game.create(tmp_path / "g", team=9)
    g = engine.Game(tmp_path / "g")
    g.start(time.time() - minutes_in * 60)
    return g


def test_simulated_staff_use_the_documented_password_for_that_machine(tmp_path):
    g = _game(tmp_path, 10)
    real = {("10.9.3.31", "alex.sample"): "Blue-Changed-1!", ("10.9.2.6", "alex.sample"): "Sample-Pass-11!"}   # blue changed it on ws3-1 only

    def fake_ssh(ip, user, pw, cmd):
        want = real.get((ip, user))
        return (want == pw, "logged in" if want == pw else "wrong password") if want else (True, "logged in")

    deployed = {h["name"] for h in lite.deployed(g.scenario())}
    rng = random.Random(1)
    fails = [r for _ in range(10) for r in people.usersim(g, 9, deployed, run=fake_ssh, rng=rng) if not r[2]]
    assert fails and all(f[0] == "alex.sample" and f[1] == "ws3-1" for f in fails)    # the undocumented change breaks only that login
    g.cred_change(9, "blue-9", "alex.sample", "ws3-1", "Blue-Changed-1!", "reset after a phishing reply")
    assert not [r for _ in range(10) for r in people.usersim(g, 9, deployed, run=fake_ssh, rng=rng) if not r[2]]


def test_the_red_bot_only_scores_in_the_attack_phase_and_only_on_open_doors(tmp_path):
    g = _game(tmp_path, 10)                                                        # hardening phase
    deployed = {h["name"] for h in lite.deployed(g.scenario())}
    tries = []

    def fake_ssh(ip, user, pw, cmd):
        tries.append((ip, user))
        return (ip == "10.188.9.55" and user == "rangeadmin"), "x"                  # only www still has the original admin password

    assert people.redbot_round(g, 9, deployed, {"dmz", "cloud"}, run=fake_ssh) == [] and tries == []
    g.set_meta("started", str(time.time() - 130 * 60))
    ids = people.redbot_round(g, 9, deployed, {"dmz", "cloud"}, run=fake_ssh)
    assert len(ids) == 1 and g.attacks(9)[0]["target"] == "www" and g.attacks(9)[0]["source"] == "bot"
    assert all(ip.startswith(("10.9.1.", "10.188.9.")) for ip, _ in tries)           # never a zone it cannot reach
    assert people.redbot_round(g, 9, deployed, {"dmz", "cloud"}, run=fake_ssh) == []   # no repeat while still compromised
    assert g.totals(9)["attack_reports"] == -40


def test_the_green_team_account_is_installed_and_checked_by_key(tmp_path):
    sc = scenario.load(team=9)
    (tmp_path / "EX-2" / "lite").mkdir(parents=True)
    (tmp_path / "EX-2" / "lite" / "greenteam_ed25519.pub").write_text("ssh-ed25519 AAAAexample exercise-green-team\n")
    lite.write(sc, tmp_path / "EX-2", ROOT)
    h = tmp_path / "EX-2" / "lite" / "hosts" / "www"
    assert (h / "green_user").read_text().strip() == "greenteam" and "AAAAexample" in (h / "green_key.pub").read_text()
    g = _game(tmp_path, 10)
    deployed = {x["name"] for x in lite.deployed(g.scenario())}
    answers = {"10.188.9.55": (True, "greenteam wheel"), "10.9.1.2": (True, "greenteam"), "10.9.1.3": (False, "Permission denied")}
    res = {h: (ok, why) for h, _, ok, why in people.rule_checks(g, 9, deployed, "/k", run=lambda ip, *_: answers.get(ip, (True, "greenteam wheel")))}
    assert res["www"][0] and res["dns1"] == (False, "the green-team account is no longer an administrator") and res["dns2"] == (False, "Permission denied")
    assert "terminal" not in res and people.rule_checks(g, 9, deployed, None) == []              # no key yet: nothing is claimed
