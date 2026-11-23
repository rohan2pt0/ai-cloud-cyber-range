"""The Codex builder rung: available only when installed and signed in, the right argv, a plain reason, a plain limit message.
No network: the run is injected and nothing real is started."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("codex_agent", ROOT / "lifecycle" / "codex_agent.py")
ca = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ca)


def _signed_in(home):
    (home / ".codex").mkdir()
    (home / ".codex" / "auth.json").write_text("{}", "utf-8")


def test_available_needs_the_binary_and_the_sign_in_file(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_HOME", raising=False)
    have = lambda name: "/usr/bin/codex"  # noqa: E731
    none = lambda name: None  # noqa: E731
    ok, why = ca.available(which=have, home=tmp_path)
    assert not ok and "codex login" in why and "ChatGPT account" in why     # binary, no sign-in
    _signed_in(tmp_path)
    assert ca.available(which=have, home=tmp_path) == (True, "")
    ok, why = ca.available(which=none, home=tmp_path)                         # sign-in, no binary
    assert not ok and "codex login" in why


def test_the_command_is_workspace_write_never_asks_and_carries_the_task_gates_and_feedback(tmp_path):
    fb = tmp_path / "fb"
    fb.write_text("test_x failed: boom", "utf-8")
    argv = ca.command("add a thing", fb)
    assert argv[:4] == ["codex", "exec", "--sandbox", "workspace-write"]
    assert 'approval_policy="never"' in argv
    p = argv[-1]
    assert "add a thing" in p and "ruff check ." in p and "python3 -m pytest -q" in p and "test_x failed: boom" in p
    assert "FAILED" not in ca.command("add a thing", tmp_path / "missing")[-1]


def test_main_exits_2_with_the_reason_when_not_available(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("CODEX_HOME", raising=False)
    ran = []
    rc = ca.main(env={"AUTOBUILD_TASK": "x"}, run=lambda a: ran.append(a), which=lambda n: None, home=tmp_path)
    assert rc == 2 and not ran
    assert "codex login" in capsys.readouterr().err


def test_main_runs_codex_and_passes_its_result_on(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_HOME", raising=False)
    _signed_in(tmp_path)
    seen = []

    def fake(argv):
        seen.append(argv)
        return 0, "done"
    rc = ca.main(env={"AUTOBUILD_TASK": "build it"}, run=fake, which=lambda n: "/x/codex", home=tmp_path)
    assert rc == 0 and "build it" in seen[0][-1]


def test_a_usage_limit_is_said_plainly_not_a_bare_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("CODEX_HOME", raising=False)
    _signed_in(tmp_path)
    rc = ca.main(env={"AUTOBUILD_TASK": "x"}, run=lambda a: (1, "ERROR: You've hit your usage limit. Try again later."),
                 which=lambda n: "/x/codex", home=tmp_path)
    assert rc == 3
    assert "Codex usage limit reached on your ChatGPT plan; the next rung takes over" in capsys.readouterr().err
