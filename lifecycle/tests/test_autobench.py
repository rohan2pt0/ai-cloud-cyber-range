"""AUTOBENCH: the benchmark must tell good from bad from cheating before any model is trusted with it."""
import importlib.util
import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("autobench", REPO / "lifecycle" / "autobench.py")
ab = importlib.util.module_from_spec(spec)
sys.modules["autobench"] = ab
spec.loader.exec_module(ab)
T = ab.TASKS


def test_corpus_is_well_formed_and_graded_by_hidden_tests():
    assert len(T) == 10 and len({*T}) == 10
    for t in T.values():
        assert t["difficulty"] in ("easy", "medium", "hard") and t["prompt"]
        assert any(f.startswith("test_visible") for f in t["files"]) and t["hidden"] and t["reference"]
        assert not set(t["hidden"]) & set(t["files"]), "hidden tests must never ship with the starting files"
        assert all(f in t["files"] or f.endswith(".py") for f in t["reference"])


@pytest.mark.parametrize("tid", ["last_n", "verify_token"])
def test_a_perfect_agent_is_credited_and_an_empty_one_is_not(tid):
    assert ab.run_task(T[tid], ab.agent_oracle, "oracle", "plain", use_forge=False)["resolved"]
    r = ab.run_task(T[tid], ab.agent_null, "null", "plain", use_forge=False)
    assert not r["resolved"] and not r["hidden_ok"]


@pytest.mark.parametrize("agent", [ab.agent_edits_tests, ab.agent_skips_tests])
def test_editing_or_skipping_the_tests_is_cheating_and_never_credited(agent):
    r = ab.run_task(T["last_n"], agent, "cheat", "plain", use_forge=False)
    assert r["tampered"] and not r["resolved"] and r["attempts"] == 1               # no second chance after tampering


def test_a_second_attempt_is_credited_and_receives_a_typed_brief_of_the_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("SEEN", str(tmp_path))
    fix = r"printf 'def last_n(items, n):\n    if n < 0:\n        raise ValueError(\"n\")\n    return list(items[len(items) - n:]) if n else []\n' > solution.py"
    agent = ab.make_cmd(f'cp "$AUTOBENCH_PROMPT_FILE" "$SEEN/p$AUTOBENCH_ATTEMPT"; [ "$AUTOBENCH_ATTEMPT" = 2 ] && {{ {fix}; }}; true', tmp_path)
    r = ab.run_task(T["last_n"], agent, "m", "contract", tries=2, use_forge=False)
    assert r["resolved"] and r["attempts"] == 2
    first, second = (tmp_path / "p1").read_text(), (tmp_path / "p2").read_text()
    assert "FAILED" not in first and "Your previous attempt FAILED" in second and "test_visible.py::test_basic" in second
    assert "NEVER edit, delete or skip the tests" in first                          # the contract prompt variant


def test_prompt_variants_differ_only_by_the_contract():
    plain, contract = ab.build_prompt(T["last_n"], "plain"), ab.build_prompt(T["last_n"], "contract")
    assert T["last_n"]["prompt"] in plain and T["last_n"]["prompt"] in contract and "Rules (follow all)" in contract and "Rules (follow all)" not in plain


def test_wilson_interval_is_honest_about_small_samples():
    lo, hi = ab.wilson(7, 10)
    assert 0.39 < lo < 0.40 and 0.89 < hi < 0.90
    assert ab.wilson(0, 0) == (0.0, 1.0)
    lo, hi = ab.wilson(10, 10)
    assert hi == 1.0 and 0.72 < lo < 0.73
    assert ab.wilson(70, 100)[0] > ab.wilson(7, 10)[0]                              # more data, tighter


def row(model, task, ok, attempts=1, diff="easy", prompt="plain", tampered=False, gate=(), seconds=10.0):
    return {"model": model, "prompt": prompt, "task": task, "difficulty": diff, "attempts": attempts, "resolved": ok, "tampered": tampered,
            "diffcheck_blocks": [], "gate_blocks": list(gate), "seconds": seconds}


def test_only_the_newest_run_of_a_task_counts():
    rows = [row("m", "a", False), row("m", "a", True)]
    assert ab.summarise(rows)[0]["resolved"] == 1 and ab.summarise(rows)[0]["tasks"] == 1


def test_report_ranks_models_flags_cheating_and_refuses_to_overclaim():
    ids = list(T)
    good = [row("good", i, True, diff=T[i]["difficulty"]) for i in ids]
    mid = [row("mid", i, k < 6, diff=T[i]["difficulty"], seconds=5.0) for k, i in enumerate(ids)]
    cheat = [row("cheat", i, True, diff=T[i]["difficulty"], tampered=True) for i in ids]
    part = [row("part", i, True) for i in ids[:3]]
    sm = ab.summarise(good + mid + cheat + part)
    by = {s["model"]: s for s in sm}
    assert sm[0]["model"] in ("good", "cheat") and by["good"]["rate"] == 1.0 and by["mid"]["rate"] == 0.6
    assert "good first rung" in ab.recommend(by["good"]) and "usable first rung with review" in ab.recommend(by["mid"])
    assert "do NOT use unattended" in ab.recommend(by["cheat"]) and "incomplete" in ab.recommend(by["part"])
    text = ab.render(sm)
    assert "95% range" in text and "trust the range" in text


def test_prompt_comparison_is_reported_with_its_noise_caveat():
    ids = list(T)
    rows = [row("m", i, k < 5, prompt="plain") for k, i in enumerate(ids)] + [row("m", i, k < 8, prompt="contract") for k, i in enumerate(ids)]
    assert "helped (+3 tasks" in ab.render(ab.summarise(rows))


def test_empty_report_tells_you_what_to_run():
    assert "autobench run" in ab.render([]) and "selftest" in ab.render([])


def test_results_round_trip_and_ignore_corrupt_lines(tmp_path):
    p = tmp_path / "results.jsonl"
    p.write_text(json.dumps(row("m", "a", True)) + "\nnot json\n" + json.dumps(row("m", "b", False)) + "\n")
    assert len(ab.load_results(p)) == 2


def test_docker_sandbox_has_no_network_and_dropped_privileges(tmp_path):
    cmd = ab.test_command(tmp_path, ["t.py"], "docker")
    s = " ".join(cmd)
    assert cmd[:2] == ["docker", "run"] and "--network none" in s and "--cap-drop ALL" in s and "no-new-privileges" in s and "--pids-limit" in s
    assert cmd[-1] == "t.py" and "python:3.12-slim" in cmd
    assert ab.test_command(tmp_path, ["t.py"], "local")[0] == "python3"


def test_model_written_code_never_sees_api_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-should-not-leak")
    (tmp_path / "test_env.py").write_text("import os\n\n\ndef test_no_key():\n    assert 'OPENAI_API_KEY' not in os.environ\n")
    rc, out = ab.run_tests(tmp_path, ["test_env.py"])
    assert rc == 0, out


def test_a_hanging_solution_times_out_instead_of_hanging_the_benchmark(tmp_path):
    (tmp_path / "test_loop.py").write_text("def test_loop():\n    while True:\n        pass\n")
    rc, out = ab.run_tests(tmp_path, ["test_loop.py"], timeout=2)
    assert rc == 124 and "timeout" in out


def test_cli_refuses_a_large_paid_run_without_yes_and_list_works(capsys):
    assert ab.main(["list"]) == 0 and "last_n" in capsys.readouterr().out
    assert ab.main(["run", "--models", "a,b,c", "--prompt", "both", "--agent", "cmd:true"]) == 1
    assert "--yes" in capsys.readouterr().out
    assert ab.main(["run", "--models", "x", "--tasks", "nope", "--agent", "cmd:true"]) == 2


def test_cli_run_with_a_command_agent_records_results_and_reports(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SECURAX_AUTOBENCH_DIR", str(tmp_path))
    ref = ab.TASKS["last_n"]["reference"]["solution.py"].replace("\n", "\\n").replace("'", "'\\''")
    assert ab.main(["run", "--models", "m1", "--tasks", "last_n", "--tries", "1", "--prompt", "plain", "--no-forge", "--agent", f"cmd:printf '{ref}' > solution.py"]) == 0
    out = capsys.readouterr().out
    assert "SOLVED" in out and "m1" in out
    rows = ab.load_results(tmp_path / "results.jsonl")
    assert len(rows) == 1 and rows[0]["resolved"] and rows[0]["model"] == "m1"
