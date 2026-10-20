"""`./securax review`: the change (with new files) goes to the strong chain through the gateway with the repo's rules, private
files are never sent, and a dead gateway gives a plain answer. A throwaway git repo; nothing leaves the machine."""
import importlib.util
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("review", ROOT / "lifecycle" / "review.py")
rv = importlib.util.module_from_spec(_s)
_s.loader.exec_module(rv)


def repo(tmp_path):
    sh = lambda *a: subprocess.run(["git", "-C", str(tmp_path), *a], check=True, capture_output=True)  # noqa: E731
    sh("init", "-q", "-b", "main")
    sh("config", "user.email", "t@example.invalid")
    sh("config", "user.name", "t")
    (tmp_path / "AGENTS.md").write_text("# a\n## 4. Rules that are easy to break\n- never fake a green\n## 5. next\n")
    (tmp_path / "app.py").write_text("x = 1\n")
    sh("add", "-A")
    sh("commit", "-q", "-m", "one")
    return tmp_path


def test_the_change_and_new_files_go_to_the_strong_chain_with_the_rules(tmp_path, monkeypatch, capsys):
    r = repo(tmp_path)
    monkeypatch.setattr(rv, "ROOT", r)
    (r / "app.py").write_text("x = 2\n")
    (r / "new.py").write_text("def f():\n    return 1\n")
    sent = {}

    def fake(url, key, body):
        sent.update(url=url, body=body)
        return {"model": "opencodego-pro", "choices": [{"message": {"content": "1. app.py:1 x changed without a test"}}]}
    assert rv.main(["--base", "HEAD"], send=fake) == 0
    msgs = sent["body"]["messages"]
    assert sent["url"].endswith("/chat/completions") and sent["body"]["model"] == "strong"
    assert "never fake a green" in msgs[0]["content"] and "+x = 2" in msgs[1]["content"] and "+++ b/new.py" in msgs[1]["content"]
    assert "answered by opencodego-pro" in capsys.readouterr().out


def test_private_files_are_never_sent_and_a_dead_gateway_says_so(tmp_path, monkeypatch, capsys):
    r = repo(tmp_path)
    monkeypatch.setattr(rv, "ROOT", r)
    (r / "vault").mkdir()
    (r / "vault" / "notes.txt").write_text("private\n")
    called = []
    assert rv.main(["--base", "HEAD"], send=lambda *a: called.append(a)) == 2 and not called
    assert "Refused" in capsys.readouterr().out
    (r / "vault" / "notes.txt").unlink()
    (r / "app.py").write_text("x = 3\n")

    def down(*a):
        raise OSError("connection refused")
    assert rv.main(["--base", "HEAD"], send=down) == 1 and "./securax up" in capsys.readouterr().out
    assert rv.main(["--base", "HEAD", "--dry-run"], send=down) == 0
