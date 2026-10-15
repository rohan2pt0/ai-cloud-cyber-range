"""The scale ladder cannot promise what the repo lacks; the notifier is quiet, safe and secret-aware."""
import importlib.util
import json
import pathlib
import sys
import urllib.error

G = pathlib.Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, G / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


scale, notify = load("scale"), load("notify")


def test_ladder_is_contiguous_and_every_have_or_dormant_has_evidence():
    assert scale.problems() == []


def test_tier_lookup_covers_one_to_a_hundred_thousand():
    ids = [scale.tier_for(n)["id"] for n in (1, 5, 6, 60, 250, 251, 5000, 5001, 100000, 10**7)]
    assert ids == ["solo", "solo", "team", "department", "department", "enterprise", "enterprise", "scale", "scale", "scale"]


def test_every_tier_above_solo_admits_at_least_one_gap():
    for t in scale.load()[1:]:
        assert any(c["state"] == "gap" for c in t["capabilities"]), t["id"]


def test_a_missing_evidence_file_is_caught():
    bad = [{"id": "x", "people": [1, 9], "capabilities": [{"name": "n", "state": "have", "evidence": "no/such/file"}]}]
    assert any("does not exist" in p for p in scale.problems(bad))


def test_cli_json_and_bad_input(capsys):
    assert scale.main(["--people", "60", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["tier"]["id"] == "department"
    assert scale.main(["--people", "0"]) == 2


def test_webhook_url_rules(monkeypatch):
    monkeypatch.delenv("SECURAX_NOTIFY_ALLOW_PLAIN_HTTP", raising=False)
    ok = ["https://chat.example.com/hooks/x", "http://localhost:8065/hooks/x", "http://192.168.1.5/h", "http://box.tail1.ts.net/h"]
    for u in ok:
        assert notify.url_problem(u) is None, u
    for u in ("http://evil.example.com/h", "ftp://x/y", "file:///etc/passwd", "http://8.8.8.8/h"):
        assert notify.url_problem(u), u


def test_digest_is_plain_counts_and_labels_only():
    status, msg = notify.build_digest({"overall": "red", "eisenhower": {"do": ["a", "b", "c", "d"]}}, ["OVERDUE c1 rbi/x was due soon"])
    assert status == "red" and "🔴" in msg
    assert "- a" in msg and "- c" in msg and "- d" not in msg      # top three only
    assert "Regulatory clock" in msg


def test_unconfigured_and_refused_exit_codes(monkeypatch, capsys):
    monkeypatch.delenv("SECURAX_NOTIFY_WEBHOOK", raising=False)
    assert notify.main(["test"]) == 2
    monkeypatch.setenv("SECURAX_NOTIFY_WEBHOOK", "http://evil.example.com/h")
    assert notify.main(["test"]) == 2


def test_failure_never_echoes_the_secret_url(monkeypatch, capsys):
    secret = "https://chat.example.com/hooks/SUPERSECRET"
    monkeypatch.setenv("SECURAX_NOTIFY_WEBHOOK", secret)
    monkeypatch.setattr(notify, "post", lambda *a, **k: (_ for _ in ()).throw(urllib.error.URLError(secret)))
    assert notify.main(["test"]) == 1
    assert "SUPERSECRET" not in capsys.readouterr().out


def test_only_bad_is_silent_when_green(monkeypatch, capsys):
    monkeypatch.setenv("SECURAX_NOTIFY_WEBHOOK", "https://chat.example.com/h")
    monkeypatch.setattr(notify, "build_digest", lambda: ("green", "all fine"))
    sent = []
    monkeypatch.setattr(notify, "post", lambda u, t, **k: sent.append(t))
    assert notify.main(["digest", "--only-bad"]) == 0 and sent == []
    monkeypatch.setattr(notify, "build_digest", lambda: ("amber", "look"))
    assert notify.main(["digest", "--only-bad"]) == 0 and sent == ["look"]


def _isolate(monkeypatch, tmp_path):
    for k in ("SECURAX_NOTIFY_WEBHOOK", "SECURAX_NOTIFY_NTFY", "SECURAX_NOTIFY_NTFY_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(notify, "ENV_FILE", tmp_path / ".env")
    monkeypatch.setattr(notify, "STATE", tmp_path / "state.json")


def test_settings_are_read_from_the_env_file(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    (tmp_path / ".env").write_text('X=1\nSECURAX_NOTIFY_NTFY="https://ntfy.sh/abc-long-topic"\n')
    assert notify.channels() == [("ntfy", "https://ntfy.sh/abc-long-topic")]


def test_ntfy_send_carries_title_priority_and_token(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    monkeypatch.setenv("SECURAX_NOTIFY_NTFY", "https://ntfy.example.com/t")
    monkeypatch.setenv("SECURAX_NOTIFY_NTFY_TOKEN", "tk_secret")
    seen = {}

    class R:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake(req, timeout):
        seen.update(url=req.full_url, body=req.data, headers=dict(req.header_items()))
        return R()
    monkeypatch.setattr(notify.urllib.request, "urlopen", fake)
    assert notify.main(["send", "Backup is 9 days old", "--title", "Andon", "--priority", "high"]) == 0
    assert seen["body"] == b"Backup is 9 days old" and seen["headers"]["Priority"] == "4"
    assert seen["headers"]["Title"] == "Andon" and seen["headers"]["Authorization"] == "Bearer tk_secret"


def test_changed_sends_once_then_only_on_change_including_back_to_green(monkeypatch, tmp_path, capsys):
    _isolate(monkeypatch, tmp_path)
    monkeypatch.setenv("SECURAX_NOTIFY_NTFY", "https://ntfy.example.com/t")
    sent = []
    monkeypatch.setattr(notify, "post_ntfy", lambda url, text, title, prio: sent.append((title, prio)))
    state = {"v": ("red", "🔴 backup old")}
    monkeypatch.setattr(notify, "build_digest", lambda: state["v"])
    args = ["digest", "--changed", "--only-bad"]
    assert notify.main(args) == 0 and sent == [("SecuRAX: RED", "high")]
    assert notify.main(args) == 0 and len(sent) == 1                      # unchanged: silent
    state["v"] = ("green", "🟢 all fine")
    assert notify.main(args) == 0 and sent[-1] == ("SecuRAX: GREEN", "default")   # recovery is news
    state["v"] = ("green", "🟢 all fine, new wording")
    assert notify.main(args) == 0 and len(sent) == 2                      # green to green stays quiet


def test_changed_without_a_channel_is_a_quiet_no_op(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    monkeypatch.setattr(notify, "build_digest", lambda: ("red", "x"))
    assert notify.main(["digest", "--changed"]) == 0
