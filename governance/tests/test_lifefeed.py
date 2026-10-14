"""The estate feed tells the Guiding Map what the estate already knows: urgent first, never duplicated, never personal, never a crash."""
import datetime as dt
import importlib.util
import json
import os
import pathlib
import sys
import time

G = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("securax_lifefeed_t", G / "lifefeed.py")
lf = importlib.util.module_from_spec(spec)
sys.modules["securax_lifefeed_t"] = lf
spec.loader.exec_module(lf)


def cockpit(tmp_path, metrics):
    p = tmp_path / "cockpit.json"
    p.write_text(json.dumps({"metrics": metrics}))
    return p


def test_red_cockpit_items_come_first_with_their_fix_and_ok_items_last(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_CERTS_STATE", str(tmp_path / "s.json"))
    c = cockpit(tmp_path, [{"id": "tls", "label": "Encryption", "status": "red", "action": "Turn it on", "cmd": "./securax tls on", "importance": 3},
                           {"id": "disk", "label": "Disk", "status": "amber", "action": "watch"}])
    (tmp_path / "b").mkdir()
    f = tmp_path / "b" / "securax-1.tar.gz.gpg"
    f.write_bytes(b"x")
    d = lf.build(now=time.time(), env={"SECURAX_BACKUP_DIR": str(tmp_path / "b")}, cockpit=c, today=dt.date(2026, 11, 2))
    assert d["items"][0]["text"] == "Encryption: Turn it on" and d["items"][0]["cmd"] == "./securax tls on"
    assert d["items"][-1]["level"] == "ok" and "encrypted" in d["items"][-1]["text"]                  # a fresh encrypted backup is good news, shown last
    assert any(i["src"] == "certs" and "CPTS" in i["text"] for i in d["items"])
    assert len(d["items"]) <= 4


def test_a_backup_the_cockpit_already_flagged_is_not_said_twice(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_CERTS_STATE", str(tmp_path / "s.json"))
    c = cockpit(tmp_path, [{"id": "backup-age", "label": "Latest backup", "status": "red", "action": "Take a backup now", "cmd": "./securax backup"}])
    d = lf.build(env={"SECURAX_BACKUP_DIR": str(tmp_path / "none")}, cockpit=c)
    assert sum("backup" in i["text"].lower() for i in d["items"]) == 1


def test_old_or_plain_backups_ask_for_action(tmp_path):
    (tmp_path / "b").mkdir()
    old = tmp_path / "b" / "securax-1.tar.gz"
    old.write_bytes(b"x")
    os.utime(old, (time.time() - 10 * 86400, time.time() - 10 * 86400))
    it = lf.backup_item({"SECURAX_BACKUP_DIR": str(tmp_path / "b")})
    assert it["level"] == "act" and "10 days" in it["text"] and "NOT encrypted" in it["text"] and it["cmd"] == "./securax protect"
    assert lf.backup_item({"SECURAX_BACKUP_DIR": str(tmp_path / "missing")})["cmd"] == "./securax backup"


def test_missing_or_corrupt_sources_never_crash_the_feed(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_CERTS_STATE", str(tmp_path / "s.json"))
    bad = tmp_path / "cockpit.json"
    bad.write_text("{not json")
    assert lf.cockpit_items(bad) == [] and lf.cockpit_items(tmp_path / "nope.json") == []
    d = lf.build(env={}, cockpit=bad)
    assert d["items"] and d["generated"]


def test_a_healthy_cockpit_says_so(tmp_path):
    assert lf.cockpit_items(cockpit(tmp_path, [{"id": "x", "label": "X", "status": "green"}]))[0]["level"] == "ok"


def test_the_feed_carries_no_money_names_or_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_CERTS_STATE", str(tmp_path / "s.json"))
    out = tmp_path / "feed.json"
    lf.write(out, env={"LITELLM_MASTER_KEY": "sk-secret-123", "SECURAX_BACKUP_DIR": str(tmp_path)}, cockpit=tmp_path / "none.json")
    text = out.read_text()
    assert "sk-secret" not in text and "₹" not in text and json.loads(text)["items"]
    assert not out.with_suffix(".tmp").exists()                                   # written atomically


def test_cli_writes_the_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SECURAX_CERTS_STATE", str(tmp_path / "s.json"))
    out = tmp_path / "f.json"
    assert lf.main(["--out", str(out)]) == 0 and json.loads(out.read_text())["items"]
    assert "Estate feed written" in capsys.readouterr().out
