"""Navigator mode is enforced by a hook, not left to the model's memory (owner, 2026-11-10; LESSONS.md)."""
import importlib.util
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _mod():
    spec = importlib.util.spec_from_file_location("navigator_hook", ROOT / "lifecycle" / "navigator_hook.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_the_repo_settings_run_the_hook_on_every_message_and_at_start():
    cfg = json.loads((ROOT / ".claude" / "settings.json").read_text("utf-8"))["hooks"]
    for event in ("SessionStart", "UserPromptSubmit"):
        cmds = [h["command"] for block in cfg[event] for h in block["hooks"]]
        assert any("lifecycle/navigator_hook.py" in c for c in cmds), event


def test_a_build_request_gets_the_delegate_rule():
    text = _mod().message("build the next queue item")
    assert "delegate" in text and "delegate_here.sh" in text and "strong-tier" in text


def test_the_hook_answers_in_the_hook_format_and_never_fails():
    for payload in ('{"hook_event_name":"UserPromptSubmit","prompt":"fix the inbox"}', "not json", ""):
        out = subprocess.run([sys.executable, str(ROOT / "lifecycle" / "navigator_hook.py")], input=payload,
                             capture_output=True, text=True, timeout=30)
        assert out.returncode == 0
    out = subprocess.run([sys.executable, str(ROOT / "lifecycle" / "navigator_hook.py")],
                         input='{"hook_event_name":"UserPromptSubmit","prompt":"fix the inbox"}', capture_output=True, text=True, timeout=30)
    ctx = json.loads(out.stdout)["hookSpecificOutput"]
    assert ctx["hookEventName"] == "UserPromptSubmit" and "NAVIGATOR MODE" in ctx["additionalContext"]


def test_the_rule_is_written_where_every_agent_reads():
    assert "NAVIGATOR" in (ROOT / "CLAUDE.md").read_text("utf-8")
    agents = (ROOT / "AGENTS.md").read_text("utf-8")
    assert "Claude is the navigator, the open models are the builders" in agents and "navigator_hook.py" in agents
