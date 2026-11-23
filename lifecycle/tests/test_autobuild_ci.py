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
    # two providers, never one (no single point of failure, owner 2026-11-20); still no web for the model
    assert cfg["enabled_providers"] == ["gocode", "openrouter", "gemini"] and cfg["permission"]["webfetch"] == "deny"
    assert cfg["provider"]["gocode"]["options"]["baseURL"] == ci.GO_BASE
    assert "{env:OPENCODE_GO_API_KEY}" == cfg["provider"]["gocode"]["options"]["apiKey"]
    assert ci.chain("strong")[0] == "deepseek-v4-pro" and ci.chain("builder")[0] == "deepseek-v4.1-flash"


def test_hard_work_uses_the_strong_chain_and_a_failed_model_hands_over(monkeypatch, tmp_path):
    calls = []

    def run(cmd, cwd=None, **kw):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 1 if len(calls) == 1 else 0)
    monkeypatch.setattr(ci, "tier", lambda task: "strong")
    assert ci.agent({"AUTOBUILD_TASK": "fake: harden the sync merge", "AUTOBUILD_PROBE": "0"}, run=run) == 0
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


def test_the_open_models_get_the_specialist_agents_and_reviewers_cannot_edit():
    agents = {p.stem: p.read_text("utf-8") for p in (ROOT / ".opencode" / "agents").glob("*.md")}
    assert {"planner", "code-reviewer", "security-reviewer", "test-writer", "docs-keeper"} <= set(agents)
    for name, text in agents.items():
        front = yaml.safe_load(text.split("---")[1])
        assert front["description"] and front["mode"] == "subagent" and front["permission"]["webfetch"] == "deny", name
    for name in ("planner", "code-reviewer", "security-reviewer"):
        assert yaml.safe_load(agents[name].split("---")[1])["permission"]["edit"] == "deny", name


def test_every_pull_request_gets_an_open_model_review_without_exposing_a_write_token_to_code():
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "ai-review.yml").read_text("utf-8"))
    on = wf.get("on", wf.get(True))
    assert "pull_request" in on and "pull_request_target" not in on
    assert wf["permissions"] == {"contents": "read", "pull-requests": "write"}
    step = wf["jobs"]["review"]["steps"][0]
    assert step["with"]["persist-credentials"] is False
    run = wf["jobs"]["review"]["steps"][-1]["run"]
    assert "lifecycle/review.py" in run and 'if [ -z "$REVIEW_API_KEY" ]' in run


def test_a_hung_model_is_cut_off_and_the_next_one_takes_over(monkeypatch):
    calls = []

    def run(cmd, cwd=None, timeout=None, **kw):
        calls.append((cmd, timeout))
        if cmd[0] == "opencode" and len([c for c in calls if c[0][0] == "opencode"]) == 1:
            raise subprocess.TimeoutExpired(cmd, timeout)
        return subprocess.CompletedProcess(cmd, 0)
    monkeypatch.setattr(ci, "tier", lambda task: "local")
    assert ci.agent({"AUTOBUILD_TASK": "fake: a small page fix", "AUTOBUILD_PROBE": "0", "AUTOBUILD_MODEL_MINUTES": "2"}, run=run) == 0
    tried = [(c[3], t) for c, t in calls if c[0] == "opencode"]
    assert len(tried) == 2 and tried[0][1] == 120 and tried[0][0] != tried[1][0]


def test_models_the_account_cannot_use_are_dropped_once_and_remembered(tmp_path):
    cache, calls = tmp_path / "go.json", []

    def run(cmd, cwd=None, **kw):
        calls.append(cmd[3])
        if cmd[3].endswith("blocked"):
            return subprocess.CompletedProcess(cmd, 1)
        if cmd[3].endswith("hangs"):
            raise subprocess.TimeoutExpired(cmd, 60)
        return subprocess.CompletedProcess(cmd, 0, stdout="OK")     # a healthy model really answers
    assert ci.usable(["blocked", "hangs", "good"], run, cache, now=1000.0) == ["good"]
    assert ci.usable(["blocked", "hangs", "good"], run, cache, now=2000.0) == ["good"] and len(calls) == 3   # remembered
    assert ci.usable(["blocked"], run, cache, now=1000.0 + ci.PROBE_TTL_S + 1) == ["blocked"]              # never empty


def test_small_work_skips_the_subagents_and_hard_work_keeps_them():
    assert "no subagents" in ci.prompt({"AUTOBUILD_TASK": "fake"}, strong=False)
    assert "@planner" in ci.prompt({"AUTOBUILD_TASK": "fake"}, strong=True)


# ── speed without lowering the bar (2026-11-10): a delegated task took 46-80+ min because every brief was routed strong ──
_r = importlib.util.spec_from_file_location("securax_route_t", ROOT / "lifecycle" / "route.py")
route = importlib.util.module_from_spec(_r)
_r.loader.exec_module(route)


def test_a_file_name_in_the_paperwork_is_not_a_sensitive_topic():
    # every brief ends with "python3 tools/readme_sync.py"; "sync" in a file name made every task strong (3-4x slower)
    t = "Add a CHANGELOG line; python3 tools/readme_sync.py and python3 docs/sync_status.py; then features_sync"
    assert route.decide(t, impact={})["tier"] != "strong"


def test_real_sensitive_work_still_goes_strong():
    for t in ("fix the sync merge conflict in the hub", "rotate the api key handling", "change how the jwt is checked"):
        assert route.decide(t, impact={})["tier"] == "strong", t
    assert route.decide("edit apps/estate-sync/app.py to log more", impact={})["tier"] == "strong"   # a sensitive path, by path


def test_the_agent_is_told_the_exact_gates_that_will_judge_it():
    p = ci.prompt({"AUTOBUILD_TASK": "a small thing"}, strong=False)
    for gate in ("./securax verify", "lifecycle/diffcheck.py", "lifecycle/forge.py gate"):
        assert gate in p, gate


def test_a_red_attempt_shows_why_in_the_log_and_the_commit_title_is_short():
    src = (ROOT / "securax").read_text("utf-8")
    assert 'forge.py" brief "$FB" 2>/dev/null | head -14' in src
    assert "commit -q -m \"autobuild: $(printf '%s' \"$TASK\" | head -1 | cut -c1-120)\"" in src


def test_a_timed_out_model_hands_its_work_over_instead_of_the_next_starting_blind():
    import subprocess as sp
    seen = []

    def run(cmd, **kw):
        if cmd[:2] == ["opencode", "run"]:
            seen.append(cmd[-1])
            if len(seen) == 1:
                raise sp.TimeoutExpired(cmd, 1)
        return sp.CompletedProcess(cmd, 0)
    ci.agent({"AUTOBUILD_TASK": "a small thing", "AUTOBUILD_PROBE": "0"}, run=run)
    assert len(seen) == 2 and "ran out of time" not in seen[0] and "git diff FIRST" in seen[1]


def test_the_delegate_skill_keeps_slow_audits_out_of_briefs():
    assert "Never put a slow check in a brief" in (ROOT / ".claude" / "skills" / "delegate" / "SKILL.md").read_text("utf-8")


def test_a_silent_model_is_stopped_early_and_a_talking_one_is_not(tmp_path):
    import sys as _s
    import time as _t
    t0 = _t.time()
    rc = ci.watched([_s.executable, "-c", "import time; time.sleep(30)"], budget=60, stall=2, cwd=str(tmp_path))
    assert rc == 124 and _t.time() - t0 < 15                       # silent: stopped at the stall, not at the budget
    talk = "import time,sys\nfor i in range(4):\n    print('working', i, flush=True); time.sleep(1)"
    assert ci.watched([_s.executable, "-c", talk], budget=60, stall=2, cwd=str(tmp_path)) == 0   # output keeps it alive


def test_a_hung_model_is_skipped_for_six_hours(tmp_path):
    cache = tmp_path / "probe.json"
    ci._mark_hung("some-model", cache)
    calls = []
    keep = ci.usable(["some-model", "other"], run=lambda *a, **k: (calls.append(a), ci.subprocess.CompletedProcess(a, 0, stdout="OK"))[1], cache=cache)
    assert keep == ["other"]                                             # still barred while the mark is fresh
    later = ci.usable(["some-model", "other"], run=lambda *a, **k: ci.subprocess.CompletedProcess(a, 0, stdout="OK"), cache=cache,
                      now=ci.time.time() + ci.HUNG_TTL_S + 1)
    assert later == ["some-model", "other"]                              # re-probed after 30 min: an outage clears


def test_a_provider_error_with_exit_0_is_not_a_healthy_model(tmp_path):
    # opencode exits 0 on "Error: UnknownError ... Unexpected server error" (2026-11-10); the probe must read the answer
    err = 'Error: {"name": "UnknownError", "data": {"message": "Unexpected server error."}}'
    run = lambda cmd, **k: ci.subprocess.CompletedProcess(cmd, 0, stdout="", stderr=err) if "bad" in cmd[3] else ci.subprocess.CompletedProcess(cmd, 0, stdout="OK")
    assert ci.usable(["gocode-bad", "good"], run=run, cache=tmp_path / "p.json") == ["good"]


def test_autobuild_uses_only_the_flat_opencode_go_plan():
    """Spend guard slice 3 (owner's cap: Rs 1,000 a month per provider): OpenCode Go is a flat monthly plan (about $10,
    with its own dollar usage limits), so the build loop cannot spend past the cap as long as it calls ONLY the Go
    endpoint. A second provider or a pay-per-use route (OpenCode Zen) would make spend open-ended: this fails first."""
    import json
    spec = importlib.util.spec_from_file_location("abci_go", pathlib.Path(__file__).resolve().parents[1] / "autobuild_ci.py")
    ci = importlib.util.module_from_spec(spec); spec.loader.exec_module(ci)
    assert ci.GO_BASE.rstrip("/").endswith("/inference/go/v1")
    cfg = ci.config()
    # 2026-11-20: OpenRouter is the second provider, used only after Go fails; its spend is capped by the key's own credit
    # limit (a prepaid key, about $10, inside the owner's cap). Nothing else, and never a pay-per-use Go route (Zen).
    assert list(cfg["provider"]) == ["gocode", "openrouter", "gemini"] and "zen" not in json.dumps(cfg).lower()
    assert cfg["provider"]["openrouter"]["options"]["baseURL"] == "https://openrouter.ai/api/v1"
    lad = ci.ladder("builder", {})
    assert lad[0].startswith("gocode/") and lad[-1].startswith("openrouter/")   # the flat plan is always spent first


def test_a_model_running_its_own_command_in_silence_is_working_not_hung(tmp_path):
    # 2026-11-15: the Life OS suite passed 6 minutes; OpenCode prints a command only when it ends, so every delegated
    # task was stopped mid-test as "silent". A child process means the model is working.
    import sys as _s
    child = "import subprocess,sys\nsubprocess.run([sys.executable,'-c','import time; time.sleep(6)'])\nprint('done', flush=True)"
    assert ci.watched([_s.executable, "-c", child], budget=60, stall=2, cwd=str(tmp_path)) == 0


def test_a_command_that_never_ends_is_stopped_with_its_children_and_the_model_is_not_blamed(tmp_path):
    import os as _o
    import sys as _s
    import time as _t
    pidf = tmp_path / "pid"
    child = ("import subprocess,sys\np=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])\n"
             f"open({str(pidf)!r},'w').write(str(p.pid))\np.wait()")
    t0 = _t.time()
    rc = ci.watched([_s.executable, "-c", child], budget=60, stall=2, cwd=str(tmp_path), tool=4)
    assert rc == ci.OUT_OF_TIME != 124 and _t.time() - t0 < 30
    _t.sleep(0.5)
    orphan = int(pidf.read_text())
    try:
        _o.kill(orphan, 0)
        stat = pathlib.Path(f"/proc/{orphan}/stat")
        alive = not stat.exists() or stat.read_text().split()[2] != "Z"
    except OSError:
        alive = False
    assert not alive, "the model's command outlived the model and would write into the next model's checkout"


def test_only_a_real_hang_marks_a_model_unusable(monkeypatch, tmp_path):
    marked = []
    monkeypatch.setattr(ci, "_mark_hung", marked.append)
    monkeypatch.setattr(ci, "tier", lambda task: "local")
    monkeypatch.setattr(ci, "ladder", lambda name, env=None: ["one", "two"])
    codes, limits = iter([ci.OUT_OF_TIME, 124]), []

    def watched(cmd, budget, stall, tool=0):
        limits.append((budget, stall, tool))
        return next(codes)
    monkeypatch.setattr(ci, "watched", watched)

    def run(cmd, **kw):                                  # stands in for the real runner, so the watchdog path is taken
        return subprocess.CompletedProcess(cmd, 0)       # and the closing git add does not touch this checkout
    monkeypatch.setattr(ci.subprocess, "run", run)
    ci.agent({"AUTOBUILD_TASK": "a small thing", "AUTOBUILD_PROBE": "0"}, run=run)
    assert marked == ["two"]
    # 40 minutes for the work and the one slow gate; 6 silent minutes with no command; 20 for one command of its own
    assert limits == [(2400, 360, 1200)] * 2 and (ci.STALL_S, ci.TOOL_S) == (360, 1200)
    codes = iter([0])
    ci.agent({"AUTOBUILD_TASK": "x", "AUTOBUILD_PROBE": "0", "AUTOBUILD_MODEL_MINUTES": "3", "AUTOBUILD_STALL_MINUTES": "1",
              "AUTOBUILD_TOOL_MINUTES": "2"}, run=run)
    assert limits[-1] == (180, 60, 120)


def test_a_command_of_its_own_is_a_child_process_and_no_ps_means_not_busy():
    seen = {}

    def ps(cmd, **kw):
        seen.update(kw, cmd=cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="    1     0\n   10     1\n   11    10\n  110    12\n")
    assert ci._busy(10, ps) and ci._busy(1, ps)
    assert not ci._busy(11, ps) and not ci._busy(110, ps)          # a pid is not a parent; 11 is not 110
    assert seen["cmd"] == ["ps", "-eo", "pid=,ppid="] and seen["timeout"] == 10 and seen["text"]

    def none(cmd, **kw):
        raise FileNotFoundError("ps")
    assert ci._busy(10, none) is False


def test_the_slow_gate_comes_last_and_once_and_no_command_ends_in_a_full_stop():
    p = ci.prompt({"AUTOBUILD_TASK": "a small thing"}, strong=False)
    assert p.index("see it fail") < p.index("python3 lifecycle/diffcheck.py") < p.index("./securax verify")
    assert "ONCE" in p and "Do not run a browser audit" in p and "do not install anything" in p
    assert "gate --base HEAD\n" in p and "HEAD ." not in p      # the model once ran the sentence's full stop as an argument


GOOD = ("Life OS Property tab: a let-out home with no rent shows one calm line. Test first: add guiding-map/tests/test121.js; it "
        "fails now because no such line exists. Change: guiding-map/ops.js. Paperwork: CHANGELOG.md; python3 tools/readme_sync.py.")


def test_a_brief_is_one_step_with_its_test_named_and_no_slow_audit():
    assert ci.brief_problems(GOOD) == []
    assert any("names no test" in x for x in ci.brief_problems("Life OS: make the Property tab calmer. Change guiding-map/ops.js."))
    assert any("slow check" in x for x in ci.brief_problems(GOOD + " Then run python3 guiding-map/tests/ui_audit.py OUT."))
    assert any("characters" in x for x in ci.brief_problems(GOOD + " and also" * 200))
    many = GOOD + " Also change governance/a.py, lifecycle/b.py, securax, docs/c.md and website/d.html."
    assert any("files to change" in x for x in ci.brief_problems(many))


def test_the_golden_brief_passes_its_own_check_and_the_hand_off_refuses_an_unfit_one():
    gold = (ROOT / ".claude" / "skills" / "delegate" / "GOLDEN-BRIEF.md").read_text("utf-8")
    example = gold.split("## A filled example")[1].split("```")[1].strip()
    assert ci.brief_problems(example) == [], ci.brief_problems(example)
    skill = (ROOT / ".claude" / "skills" / "delegate" / "SKILL.md").read_text("utf-8")
    assert "GOLDEN-BRIEF.md" in skill and "autobuild_ci.py check" in skill and "model: sonnet" in skill
    here = (ROOT / "lifecycle" / "delegate_here.sh").read_text("utf-8")
    assert "autobuild_ci.py check" in here and "CANNOT-START the brief" in here and "DELEGATE_FORCE" in here
    assert here.index("autobuild_ci.py check") < here.index("git worktree add"), "refuse before anything is built"
    # the check itself is run for real; the hand-off script is NOT (under the mutation gate a broken check let this test
    # start a real delegation of a dummy task, 2026-11-16)
    import os as _o
    import sys as _s
    r = subprocess.run([_s.executable, str(ROOT / "lifecycle" / "autobuild_ci.py"), "check"], capture_output=True, text=True,
                       env={**_o.environ, "TASK": "make it nicer"})
    assert r.returncode == 1 and "names no test" in r.stdout
    ok = subprocess.run([_s.executable, str(ROOT / "lifecycle" / "autobuild_ci.py"), "check"], capture_output=True, text=True,
                        env={**_o.environ, "TASK": example})
    assert ok.returncode == 0 and ok.stdout == ""


def test_openrouter_takes_over_when_opencode_go_fails(monkeypatch):
    """Owner 2026-11-20: no single point of failure. OpenCode Go first, then OpenRouter automatically; a forced choice puts
    OpenRouter first; OPENROUTER_MODELS overrides its models."""
    import importlib.util
    import pathlib
    spec = importlib.util.spec_from_file_location("abci_or", pathlib.Path(__file__).resolve().parent.parent / "autobuild_ci.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    lad = m.ladder("builder", {})
    go = [x for x in lad if x.startswith("gocode/")]
    orr = [x for x in lad if x.startswith("openrouter/")]
    assert go and orr and sorted(lad) == sorted(go + orr + [x for x in lad if x.startswith("gemini/")]) and orr == ["openrouter/" + x for x in m.OR_MODELS]
    lad2 = m.ladder("builder", {"AUTOBUILD_PROVIDER": "openrouter"})
    assert lad2[0].startswith("openrouter/") and lad2[-1].startswith("gocode/")
    assert m.or_chain({"OPENROUTER_MODELS": "a/one, b/two"}) == ["a/one", "b/two"]
    c = m.config()
    assert c["provider"]["openrouter"]["options"]["apiKey"] == "{env:OPENROUTER_API_KEY}"
    # a failed Go model hands over to the OpenRouter one in the same attempt
    calls = []

    def run(cmd, **kw):
        import subprocess as sp
        if cmd and cmd[0] != "opencode":                 # the closing git step: nothing to record
            return sp.CompletedProcess(cmd, 0)
        calls.append(cmd[3])
        return sp.CompletedProcess(cmd, 0 if cmd[3].startswith("openrouter/") else 1)
    monkeypatch.setattr(m, "tier", lambda task: "local")
    monkeypatch.setattr(m, "ladder", lambda name, env=None: ["gocode/x", "openrouter/y"])
    m.agent({"AUTOBUILD_TASK": "t", "AUTOBUILD_PROBE": "0"}, run=run)
    assert calls[:2] == ["gocode/x", "openrouter/y"]


def test_a_provider_that_cannot_pay_is_seen_before_any_work():
    """No single point of failure, for money too (owner 2026-11-23): a capped plan and an account with no credit are both read as
    out of allowance from their own answers, in one call each, never as a bad model; a working answer is OK."""
    capped = '{"type":"error","error":{"type":"GoUsageLimitError","message":"OpenCode Go usage limit reached (monthly, resets in 14d)"}}'
    assert ci.out_of_allowance(capped)
    assert ci.out_of_allowance("This request requires more credits, or fewer max_tokens. You requested up to 16384 tokens, but can only afford 285.")
    assert not ci.out_of_allowance('{"choices":[{"message":{"content":"OK"}}]}')
    answers = {"/chat/completions": capped, "/credits": '{"data":{"total_credits":0,"total_usage":0.2}}'}
    fake = lambda url, env, body=None, headers=None: next(v for k, v in answers.items() if url.endswith(k))  # noqa: E731
    a = ci.allowance({}, http=fake)
    assert not a[ci.PROVIDER]["ok"] and "usage limit" in a[ci.PROVIDER]["why"]
    assert not a[ci.OR_PROVIDER]["ok"] and "$-0.20" in a[ci.OR_PROVIDER]["why"]
    answers.update({"/chat/completions": '{"choices":[{"message":{"content":"OK"}}]}', "/credits": '{"data":{"total_credits":10,"total_usage":1}}'})
    b = ci.allowance({}, http=fake)
    assert b[ci.PROVIDER]["ok"] and b[ci.OR_PROVIDER]["ok"]


def test_when_none_can_pay_the_handoff_stops_in_seconds_and_names_path_c():
    sh = (ROOT / "lifecycle" / "delegate_here.sh").read_text("utf-8")
    skill = (ROOT / ".claude" / "skills" / "delegate" / "SKILL.md").read_text("utf-8")
    assert sh.index("autobuild_ci.py allowance") < sh.index("bash ./securax autobuild \"$TASK\""), "ask who can pay before any build starts"
    assert "exit 3" in sh and "path C" in sh
    assert "ALL-OUT" in skill and "go to C at once" in skill


def test_gemini_is_the_third_builder_account_and_its_quota_is_read_with_a_real_sized_request():
    """Owner 2026-11-23 (builder-no-money-spof, slice 1): a third provider on its own budget. Order: Go, OpenRouter paid, Gemini,
    OpenRouter free. Fake answers only: no network, no money."""
    lad = ci.ladder("builder", {})
    pre = [m.split("/", 1)[0] for m in lad]
    assert pre[0] == "gocode" and pre[-1] == "openrouter" and lad[-1].endswith(":free")
    assert pre.index("openrouter") < pre.index("gemini") < len(pre) - 1
    assert [m for m in lad if m.startswith("gemini/")] == ["gemini/" + x for x in ci.GEMINI_MODELS]
    assert ci.ladder("builder", {"GEMINI_MODELS": "a, b"})[-3:-1] == ["gemini/a", "gemini/b"]
    cfg = ci.config()
    g = cfg["provider"]["gemini"]
    assert "gemini" in cfg["enabled_providers"] and g["npm"] == "@ai-sdk/openai-compatible"
    assert g["options"] == {"baseURL": "https://generativelanguage.googleapis.com/v1beta/openai", "apiKey": "{env:GEMINI_API_KEY}"}
    assert ci.out_of_allowance("You exceeded your current quota, please check your plan") and ci.out_of_allowance('{"status":"RESOURCE_EXHAUSTED"}')
    seen = []
    state = {"gem": '{"error":{"code":429,"message":"You exceeded your current quota","status":"RESOURCE_EXHAUSTED"}}'}

    def fake(url, env, body=None, headers=None):
        if url.endswith("/credits"):
            return '{"data":{"total_credits":10,"total_usage":1}}'
        if url.startswith(ci.GEMINI_BASE):
            assert url == ci.GEMINI_BASE + "/chat/completions"
            seen.append(body)
            return state["gem"](body) if callable(state["gem"]) else state["gem"]
        return '{"choices":[{}]}'
    a = ci.allowance({}, http=fake)
    assert not a["gemini"]["ok"] and "quota" in a["gemini"]["why"]
    assert len(seen[0]["messages"][0]["content"]) >= 4000
    seen.clear()
    state["gem"] = lambda b: '{"error":{"code":503,"message":"high demand"}}' if b["model"] == ci.GEMINI_MODELS[0] else '{"choices":[{"message":{"content":"OK"}}]}'
    b = ci.allowance({}, http=fake)
    assert b["gemini"]["ok"] and [x["model"] for x in seen] == ci.GEMINI_MODELS[:2]
    state["gem"] = '{"error":{"code":503,"message":"high demand"}}'
    c = ci.allowance({}, http=fake)
    assert not c["gemini"]["ok"] and c["gocode"]["ok"]
