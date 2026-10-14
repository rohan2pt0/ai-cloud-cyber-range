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
