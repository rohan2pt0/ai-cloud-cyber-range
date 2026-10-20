"""./securax nodes: adding a node proves the other side accepts the token before anything is saved, a beta node is pull-only,
removing keeps the rest, and the status names what is wrong. No network: a stand-in answers for the other node."""
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "governance"))
_s = importlib.util.spec_from_file_location("nodes", ROOT / "governance" / "nodes.py")
nd = importlib.util.module_from_spec(_s)
_s.loader.exec_module(nd)


def test_add_checks_the_token_first_then_saves_and_remove_keeps_the_rest(tmp_path, monkeypatch):
    envf = tmp_path / ".env"
    envf.write_text("SYNC_TOKENS=this-node-token\n")
    monkeypatch.setattr(nd.online, "ENVF", envf)
    for k in ("SYNC_PEERS", "SYNC_TOKENS"):
        monkeypatch.delenv(k, raising=False)
    ok = lambda url, tok, timeout=10: (200, ["me"]) if tok == "good" else (401, None)
    out = []
    assert nd.main(["add", "https://vps.example.invalid/sync", "wrong"], say=out.append, fetch=ok) == 1
    assert "SYNC_PEERS" not in envf.read_text()                                   # nothing saved when the other side refused
    assert nd.main(["add", "https://vps.example.invalid/sync", "good"], say=out.append, fetch=ok) == 0
    assert nd.main(["add", "https://beta.example.invalid/sync", "good", "--pull-only"], say=out.append, fetch=ok) == 0
    text = envf.read_text()
    assert "https://vps.example.invalid/sync|good,https://beta.example.invalid/sync|good|pull" in text and oct(envf.stat().st_mode)[-3:] == "600"
    assert nd.main(["remove", "https://vps.example.invalid/sync"], say=out.append, fetch=ok) == 0
    assert "SYNC_PEERS=https://beta.example.invalid/sync|good|pull" in envf.read_text()
    assert nd.main(["add", "ftp://nope", "good"], say=out.append, fetch=ok) == 2


def test_status_reports_each_node_and_fails_when_one_is_out_of_step(tmp_path, monkeypatch):
    envf = tmp_path / ".env"
    envf.write_text("SYNC_TOKENS=t\nSYNC_PEERS=https://a.example.invalid/sync|x,https://b.example.invalid/sync|y|pull\n")
    monkeypatch.setattr(nd.online, "ENVF", envf)
    for k in ("SYNC_PEERS", "SYNC_TOKENS"):
        monkeypatch.delenv(k, raising=False)
    report = {"node": "laptop", "peers": [{"url": "https://a.example.invalid/sync", "ok": True, "at": "now", "pulled": 1, "pushed": 2},
                                          {"url": "https://b.example.invalid/sync", "ok": False, "error": "cannot reach it"}]}
    out = []
    assert nd.main(["status"], say=out.append, fetch=lambda u, t, timeout=10: (200, report)) == 1
    text = "\n".join(out)
    assert "This node: laptop" in text and "✔ in step" in text and "✗ cannot reach it" in text and "pull only (beta)" in text
