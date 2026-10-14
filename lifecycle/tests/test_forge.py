"""FORGE: the admission gate catches changes that pass `verify` without proving anything, and never leaves damage behind."""
import importlib.util
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("forge", REPO / "lifecycle" / "forge.py")
fg = importlib.util.module_from_spec(spec)
sys.modules["forge"] = fg
spec.loader.exec_module(fg)

BASE_SRC = "def price(n):\n    return n * 2\n"
GOOD_SRC = BASE_SRC + "\n\ndef tier(n):\n    if n >= 10 and n < 100:\n        return 'mid'\n    return 'low'\n"
STRONG = ("import calc\n\ndef test_tier():\n    assert calc.tier(10) == 'mid'\n    assert calc.tier(99) == 'mid'\n    assert calc.tier(9) == 'low'\n"
          "    assert calc.tier(100) == 'low'\n")
WEAK = "import calc\n\ndef test_tier():\n    assert calc.tier(50) in ('mid', 'low')\n"


def git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd, check=True, text=True, capture_output=True).stdout


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "calc.py").write_text(BASE_SRC)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_price.py").write_text("import calc\n\ndef test_price():\n    assert calc.price(2) == 4\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path


def run_gate(repo, **kw):
    return fg.gate("HEAD", None, kw.get("max_mutants", 24), kw.get("min_score", 0.6), False, repo)


def test_a_change_with_sharp_tests_passes_and_a_change_with_vague_tests_is_blocked(repo):
    (repo / "calc.py").write_text(GOOD_SRC)
    (repo / "tests" / "test_tier.py").write_text(STRONG)
    res, stats = run_gate(repo)
    assert stats["mutants"] >= 3 and stats["score"] >= 0.6, (res, stats)
    assert not [r for r in res if r["level"] == "BLOCK"]
    (repo / "tests" / "test_tier.py").write_text(WEAK)                      # same code, a test that cannot notice a broken line
    res, stats = run_gate(repo)
    assert stats["survived"] and any(r["rule"] == "mutation-score" and r["level"] == "BLOCK" for r in res), (res, stats)


def test_mutation_never_leaves_a_mutant_in_the_working_tree(repo):
    (repo / "calc.py").write_text(GOOD_SRC)
    (repo / "tests" / "test_tier.py").write_text(WEAK)
    run_gate(repo)
    assert (repo / "calc.py").read_text() == GOOD_SRC


def test_new_tests_that_also_pass_on_the_old_code_are_flagged(repo):
    (repo / "calc.py").write_text(GOOD_SRC)
    (repo / "tests" / "test_tier.py").write_text("def test_nothing():\n    assert 1 + 1 == 2\n")       # never touches the change
    res, _ = run_gate(repo)
    assert any(r["rule"] == "fail-to-pass" for r in res)


def test_new_tests_that_fail_on_the_old_code_satisfy_fail_to_pass(repo):
    (repo / "calc.py").write_text(GOOD_SRC)
    (repo / "tests" / "test_tier.py").write_text(STRONG)
    assert not [r for r in fg.fail_to_pass("HEAD", fg.changed_lines("HEAD", repo), repo)]
    assert git(repo, "worktree", "list").count("\n") == 1                   # the temporary worktree is gone


def test_a_new_forty_branch_function_is_blocked_but_old_complexity_is_not_punished(repo):
    body = "def big(x):\n" + "".join(f"    if x == {i}:\n        return {i}\n" for i in range(20)) + "    return None\n"
    (repo / "calc.py").write_text(BASE_SRC + "\n\n" + body)
    res = fg.budget("HEAD", fg.changed_lines("HEAD", repo), repo)
    assert any(r["rule"] == "complexity" and "big" in r["why"] for r in res)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "legacy")
    (repo / "calc.py").write_text(BASE_SRC + "\n\n" + body + "\n# touched a comment elsewhere\n")
    assert not fg.budget("HEAD", fg.changed_lines("HEAD", repo), repo)       # big() already existed and was not made worse


def test_complexity_counts_decisions():
    f = fg.functions("def f(a, b):\n    if a and b:\n        return [x for x in a if x]\n    return 0\n")["f"]
    assert f[0] == 5                                                         # 1 + if + and + comprehension + its if


def test_classify_separates_infrastructure_from_code():
    assert fg.classify("Cannot connect to the Docker daemon at unix:///var/run/docker.sock")["verdict"] == "infra"
    assert fg.classify("FAILED tests/test_a.py::test_x - AssertionError: 1 != 2\nE   assert 1 == 2")["verdict"] == "code"
    mixed = fg.classify("Cannot connect to the Docker daemon\nFAILED tests/test_a.py::test_x - assert 0")
    assert mixed["verdict"] == "mixed"
    assert fg.classify("something odd")["verdict"] == "unknown"


def test_brief_is_short_typed_and_tells_infra_to_retry_not_repair():
    log = "noise\n" * 200 + "FAILED tests/test_a.py::test_x - AssertionError\nE   assert 1 == 2\ncalc.py:3:5: F821 undefined name 'z'\n"
    b = fg.brief(log)
    assert len(b.splitlines()) <= 16 and "FAILED tests/test_a.py::test_x" in b and "F821" in b and "noise" not in b
    assert "Do not skip, delete or weaken a test" in b
    assert "INFRASTRUCTURE" in fg.brief("error during connect: docker daemon is not running")


def test_strict_turns_warnings_into_blocks(repo):
    (repo / "calc.py").write_text(GOOD_SRC)
    (repo / "tests" / "test_tier.py").write_text("def test_nothing():\n    assert 1 + 1 == 2\n")
    res, _ = fg.gate("HEAD", None, 24, 0.6, True, repo)
    assert res and all(r["level"] == "BLOCK" for r in res)


def test_the_real_cli_runs_end_to_end(repo):
    (repo / "calc.py").write_text(GOOD_SRC)
    (repo / "tests" / "test_tier.py").write_text(STRONG)
    p = subprocess.run([sys.executable, str(REPO / "lifecycle" / "forge.py"), "gate", "--base", "HEAD"], cwd=repo, text=True, capture_output=True)
    assert p.returncode in (0, 1) and "forge:" in p.stdout


def test_the_sandbox_retries_only_failures_that_are_entirely_infrastructure():
    sr = importlib.util.spec_from_file_location("sbx_run", REPO / "sandbox" / "run.py")
    sys.path.insert(0, str(REPO / "sandbox"))
    mod = importlib.util.module_from_spec(sr)
    sr.loader.exec_module(mod)
    infra, code = mod.Checks("a"), mod.Checks("b")
    infra.ok(False, "the stack starts", "Cannot connect to the Docker daemon at unix:///var/run/docker.sock")
    infra.ok(True, "something else")
    code.ok(False, "the gateway blocks the injection", "got 200, want 400")
    mixed = mod.Checks("c")
    mixed.ok(False, "the stack starts", "Cannot connect to the Docker daemon")
    mixed.ok(False, "tests pass", "FAILED tests/test_x.py::test_y - AssertionError")
    assert mod.infra_only(infra) and not mod.infra_only(code) and not mod.infra_only(mixed) and not mod.infra_only(mod.Checks("empty"))


def test_a_broken_test_command_is_reported_not_counted_as_every_mutant_killed(repo):
    (repo / "calc.py").write_text(GOOD_SRC)
    res, stats = fg.gate("HEAD", "python3 -c 'import sys; sys.exit(1)'", 24, 0.6, False, repo)
    assert any(r["rule"] == "mutation-baseline" and r["level"] == "BLOCK" for r in res) and stats["mutants"] == 0
