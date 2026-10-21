"""The estate finds its own weak points (doc 91): every combination of machines is checked, a machine that alone provides a
critical feature is named with its fix, accepted risks are shown but not counted, the early warning fires on a sudden drop,
reminders go out from one machine at a time (and from this one when in doubt), and a card holds no secret. No network."""
import importlib.util
import json
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("resilience", ROOT / "governance" / "resilience.py")
rs = importlib.util.module_from_spec(_s)
_s.loader.exec_module(rs)
NOW = 1_800_000_000


def node(name, *checks, at=NOW):
    return {"name": name, "at": at, "checks": ["estate", *checks]}


def test_every_combination_is_counted():
    nodes = [node("a"), node("b"), node("c")]
    assert rs.analyse(nodes)["scenarios"] == 7
    assert rs.analyse(nodes[:1])["scenarios"] == 1


def test_a_machine_that_alone_provides_a_critical_feature_is_named_with_its_fix():
    nodes = [node("laptop", "strong_ai", "vault", "backups"), node("vps", "online", "backups")]
    res = rs.analyse(nodes)
    weak = {(w["id"], w["node"]): w for w in rs.blocking(res)}
    assert ("online", "vps") in weak and weak[("online", "vps")]["now"] == "off" and "online invite" in weak[("online", "vps")]["fix"]
    assert ("gateway", "laptop") in weak and weak[("gateway", "laptop")]["now"] == "slower"
    assert res["alone"]["vps"]["guiding-map"] == "full", "the Life OS works on any machine alone"
    assert res["alone"]["laptop"]["online"] == "off"


def test_fixing_the_gaps_clears_them():
    nodes = [node("laptop", "strong_ai", "vault", "backups", "offsite", "online", "routines"),
             node("vps", "strong_ai", "vault", "backups", "offsite", "online", "routines", "passwords")]
    res = rs.analyse(nodes)
    assert not rs.blocking(res), rs.blocking(res)
    assert res["survivable"] == res["scenarios"] == 3


def test_an_accepted_risk_is_shown_but_does_not_count():
    res = rs.analyse([node("vps", "passwords"), node("laptop")])
    pw = [w for w in res["weak"] if w["id"] == "passwords"]
    assert pw and pw[0]["accepted"] and not [w for w in rs.blocking(res) if w["id"] == "passwords"]


def test_the_reference_estate_has_no_unaccepted_single_point_of_failure():
    m = rs.model()
    nodes = [node(c["name"], *c["checks"]) for c in m["reference"]["cards"]]
    assert not rs.blocking(rs.analyse(nodes, m))


def test_every_feature_is_declared_with_known_checks():
    m = rs.model()
    feats = {f["id"] for f in json.loads((ROOT / "features.json").read_text())["features"]}
    assert feats <= {c["id"] for c in m["capabilities"]}
    for c in m["capabilities"]:
        assert set(c["needs"]) <= set(c["full"]) | set(c["needs"]) and set(c["needs"] + c["full"]) <= set(m["checks"]), c["id"]
        assert c["state"] in ("replicated", "stateless", "per-node", "single-home") and c["fix"] and c["when_off"]


def test_the_early_warning_fires_on_a_sudden_drop_not_on_a_peer_that_is_always_flaky():
    s = []
    for h in range(8 * 24):                                    # a week of hourly samples
        t = NOW - h * 3600
        s.append({"at": t, "peer": "vps", "ok": not (h < 24 and h % 2 == 0)})   # half failed in the last day, fine before
        s.append({"at": t, "peer": "pi", "ok": h % 3 != 0})                       # always a third failing
    w = rs.warnings(now=NOW, samples=s)
    assert len(w) == 1 and w[0].startswith("vps")


def test_reminders_go_out_from_one_machine_and_the_next_takes_over():
    nodes = [node("vps"), node("laptop"), node("cloud", at=NOW - 3600)]      # cloud's card is an hour old: it is off
    assert rs.leader(nodes, "laptop", now=NOW) == "laptop"
    assert rs.leader(nodes, "vps", now=NOW) == "laptop"
    assert rs.leader([node("vps"), node("laptop", at=NOW - 3600)], "vps", now=NOW) == "vps", "laptop off: vps takes over"
    assert rs.is_leader(fetch=lambda *a, **k: (_ for _ in ()).throw(OSError("down"))) is True, "in doubt: run it"


def test_a_card_holds_no_secret(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-secret-value-123")
    monkeypatch.setenv("CF_TUNNEL_TOKEN", "fake-tunnel-token-456")
    monkeypatch.setenv("SECURAX_BACKUP_DIR", str(tmp_path))
    c = rs.card(now=NOW)
    text = json.dumps(c)
    assert "strong_ai" in c["checks"] and "online" in c["checks"]
    assert "fake-secret" not in text and "fake-tunnel" not in text and str(tmp_path) not in text


def test_publish_writes_only_this_nodes_card_and_cards_drop_gone_nodes(monkeypatch, tmp_path):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path))
    monkeypatch.setenv("SYNC_NODE_NAME", "laptop")
    sent = []

    def fetch(method, url, body=None, timeout=5):
        sent.append((method, url, body))
        if url.endswith("/peers"):
            return 200, {"peers": [{"url": "https://vps/sync", "ok": False}]}
        return 200, {"payload": {"node:vps": node("vps", at=time.time()), "node:old": node("old", at=time.time() - 40 * 86400)}}

    assert rs.publish(fetch=fetch, say=lambda *_: None) == 0
    put = next(b for m, u, b in sent if m == "PUT")
    assert list(put["payload"]) == ["node:laptop"] and list(put["meta"]) == ["node:laptop"]
    assert (tmp_path / "resilience" / "health.jsonl").read_text().count('"ok": false') == 1
    names = {c["name"] for c in rs.cards(fetch=fetch)}
    assert names == {"laptop", "vps"}, "a node unseen for 30 days drops out"
