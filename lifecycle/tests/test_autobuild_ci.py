"""The phone-triggered open-model build (doc 83, section 7): OpenCode Go models only, from the estate's own chains; no web fetch;
hard work goes to the strong chain; a model that fails hands over to the next; new files are staged for the gates; and the
workflow keeps the write token away from the agent and the task text out of every script."""
import importlib.util
import pathlib
import re
import subprocess

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("securax_autobuild_ci_t", ROOT / "lifecycle" / "autobuild_ci.py")
ci = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ci)
WF = ROOT / ".github" / "workflows" / "autobuild.yml"


def test_the_config_reaches_only_opencode_go_and_cannot_fetch_the_web():
    cfg = ci.config()
    assert cfg["enabled_providers"] == ["gocode"] and cfg["permission"]["webfetch"] == "deny"
    assert cfg["provider"]["gocode"]["options"]["baseURL"] == ci.GO_BASE
    assert "{env:OPENCODE_GO_API_KEY}" == cfg["provider"]["gocode"]["options"]["apiKey"]
    assert ci.chain("strong")[0] == "deepseek-v4-pro" and ci.chain("builder")[0] == "deepseek-v4.1-flash"


def test_hard_work_uses_the_strong_chain_and_a_failed_model_hands_over(monkeypatch, tmp_path):
    calls = []

    def run(cmd, cwd=None):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 1 if len(calls) == 1 else 0)
    monkeypatch.setattr(ci, "tier", lambda task: "strong")
    assert ci.agent({"AUTOBUILD_TASK": "fake: harden the sync merge"}, run=run) == 0
    models = [c[3] for c in calls if c[0] == "opencode"]
    assert models[:2] == ["gocode/deepseek-v4-pro", "gocode/kimi-k3"]
    assert calls[-1] == ["git", "add", "-A"]


def test_the_last_failure_rides_into_the_next_prompt(tmp_path):
    fb = tmp_path / "fb"
    fb.write_text("FAILED tests/test_x.py::test_y - AssertionError: fake")
    text = ci.prompt({"AUTOBUILD_TASK": "fake task", "AUTOBUILD_FEEDBACK": str(fb)})
    assert "FAILED the gates" in text and "skip a test" in text


def test_the_workflow_keeps_the_token_from_the_agent_and_the_task_out_of_scripts():
    wf = yaml.safe_load(WF.read_text("utf-8"))
    build, publish = wf["jobs"]["build"], wf["jobs"]["publish"]
    assert wf["permissions"] == {"contents": "read"} and "permissions" not in build
    checkout = next(s for s in build["steps"] if str(s.get("uses", "")).startswith("actions/checkout"))
    assert checkout["with"]["persist-credentials"] is False
    assert "github.repository_owner" in build["if"]
    for job in (build, publish):
        for step in job["steps"]:
            assert not re.search(r"\$\{\{\s*(inputs\.task|github\.event\.issue)", step.get("run", "")), step.get("name")
    assert publish["if"] == "needs.build.outputs.green == '1'"


def test_slugs_are_branch_safe():
    assert ci.slug("Fix: the README's `help` line!!") == "fix-the-readme-s-help-line" and ci.slug("??") == "task"
