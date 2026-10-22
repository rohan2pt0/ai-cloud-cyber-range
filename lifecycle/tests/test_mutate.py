"""tools/mutate.py: the operators make the expected mutants, arid code is left alone, killed and surviving mutants are told apart,
the original file always comes back (even when the run crashes), diff mode keeps to changed lines, and the ratchet fails only on new
survivors. Everything runs on a tiny fixture module and its own test, written to tmp_path."""
import importlib.util
import json
import os
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("mutate_tool", REPO / "tools" / "mutate.py")
mut = importlib.util.module_from_spec(spec)
sys.modules["mutate_tool"] = mut                      # dataclasses look the module up by name
spec.loader.exec_module(mut)

RAIL = '''"""A tiny rail. Docstrings are never mutated: 3 < 4."""
import logging

LIMIT = 3  # the limit
TABLE = [0, 1, 2, 3, 4, 5, 6]


def allowed(n):
    if n < LIMIT:
        return True
    return False


def check(x):
    if x is None:
        raise ValueError("no value")
    return x


def spare(a, b):
    return a and b


def describe(n: int = 2) -> str:
    logging.info("n is %s", 5)
    print(f"n={n + 1}")
    return [i for i in range(0, n)]


class Box:
    def __repr__(self):
        return "Box" if 1 > 2 else "box"


if __name__ == "__main__":
    print(allowed(7))
'''

TEST = '''import pytest
from rail import allowed, check


def test_allowed():
    assert allowed(2) and not allowed(3)


def test_check():
    with pytest.raises(ValueError):
        check(None)
    assert check(5) == 5
'''


@pytest.fixture
def fx(tmp_path):
    (tmp_path / "rail.py").write_text(RAIL, "utf-8")
    (tmp_path / "test_rail.py").write_text(TEST, "utf-8")
    return tmp_path, {"file": "rail.py", "tests": ["test_rail.py"]}


def by_op(ms):
    return {(m.operator, m.mutated) for m in ms}


def test_operators_make_the_expected_mutants():
    ms = mut.find_mutants(RAIL, "rail.py")
    got = by_op(ms)
    assert ("compare", "if (n <= LIMIT):") in got
    assert ("negate", "if (not (n < LIMIT)):") in got
    assert ("compare", "if (x is not None):") in got
    assert ("raise-pass", "pass") in got
    assert ("and-or", "return ((a) or (b))") in got
    assert ("return-bool", "return False") in got and ("return-bool", "return True") in got
    assert ("number", "LIMIT = 4  # the limit") in got and ("number", "LIMIT = 2  # the limit") in got   # the comment survives the splice
    assert ("number", "def describe(n: int = 3) -> str:") in got                                         # a default is behaviour
    for m in ms:                                                                                          # every mutant is valid Python
        compile(mut.apply(RAIL.encode(), m), "rail.py", "exec")


def test_arid_code_is_skipped():
    ms = mut.find_mutants(RAIL, "rail.py")
    lines = {m.line for m in ms}
    src = RAIL.splitlines()
    arid = [i + 1 for i, s in enumerate(src) if any(k in s for k in ('"""', "TABLE", "logging.info", "print(", "range(", "Box",
                                                                     "__main__", "allowed(7)"))]
    assert not lines & set(arid), [m.mutated for m in ms if m.line in arid]
    assert len({m.key for m in ms}) == len(ms)                                                            # keys are unique


def test_killed_and_surviving_mutants_are_classified(fx):
    root, target = fx
    res = mut.mutate_target(target, root)
    assert res["error"] is None and res["mutants"] == res["killed"] + res["survived"] > 5
    survived = {(s["operator"], s["mutated"]) for s in res["survivors"]}
    assert ("and-or", "return ((a) or (b))") in survived                         # spare() has no test: it must survive
    assert ("compare", "if (n <= LIMIT):") not in survived                      # allowed(3) is tested: killed
    assert ("raise-pass", "pass") not in survived                               # check(None) must raise: killed
    assert all(s["file"] == "rail.py" and s["line"] > 0 and s["key"] for s in res["survivors"])
    assert (root / "rail.py").read_text("utf-8") == RAIL
    assert res["score"] == round(100 * res["killed"] / res["mutants"], 1)


def test_the_original_comes_back_even_when_the_run_crashes(fx, monkeypatch):
    root, target = fx
    path = root / "rail.py"
    os.utime(path, ns=(1_700_000_000_000_000_000, 1_700_000_000_000_000_000))
    before = path.stat().st_mtime_ns
    calls = []

    def crashing(cmd, cwd, timeout, cache):
        calls.append(path.read_text("utf-8"))
        if len(calls) == 1:
            return "passed", 0.1                                                  # the clean run
        raise RuntimeError("the test runner fell over")

    monkeypatch.setattr(mut, "run_tests", crashing)
    with pytest.raises(RuntimeError):
        mut.mutate_target(target, root)
    assert calls[1] != RAIL                                                       # it really was mutated while the tests ran
    assert path.read_text("utf-8") == RAIL and path.stat().st_mtime_ns == before
    assert not mut._journal(root).exists()


def test_a_killed_run_is_recovered_from_the_journal(fx):
    root, _ = fx
    path = root / "rail.py"
    import base64
    mut._journal(root).write_text(json.dumps({"rail.py": {"data": base64.b64encode(RAIL.encode()).decode(), "mtime_ns": 1}}))
    path.write_text("LIMIT = 999\n", "utf-8")                                     # what a SIGKILLed run would leave behind
    assert mut.recover(root) == ["rail.py"]
    assert path.read_text("utf-8") == RAIL and not mut._journal(root).exists()


def test_a_hanging_test_run_is_a_timeout(tmp_path):
    status, took = mut.run_tests([sys.executable, "-c", "import time; time.sleep(30)"], tmp_path, 0.5, str(tmp_path))
    assert status == "timeout" and took < 10


def test_the_unmutated_file_must_pass_first(fx):
    root, target = fx
    (root / "test_rail.py").write_text("def test_red():\n    assert False\n", "utf-8")
    res = mut.mutate_target(target, root)
    assert res["error"] and res["killed"] == res["survived"] == 0


def git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd, check=True, text=True,
                          capture_output=True).stdout


def test_diff_mode_mutates_only_changed_lines(fx):
    root, target = fx
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "base")
    path = root / "rail.py"
    path.write_text(RAIL.replace("    return a and b\n", "    return a and b  # touched\n"), "utf-8")
    lines = mut.changed_lines("HEAD", "rail.py", root)
    assert lines == {RAIL.splitlines().index("    return a and b") + 1}
    res = mut.mutate_target(target, root, lines=lines)
    assert res["mutants"] == 1 and res["survived"] == 1 and res["survivors"][0]["operator"] == "and-or"
    assert mut.changed_lines("HEAD", "test_rail.py", root) == set()


def test_max_spreads_over_the_whole_file():
    assert mut.spread(list(range(10)), 3) == [0, 3, 6]
    assert mut.spread([1, 2], 5) == [1, 2] and mut.spread([1, 2], None) == [1, 2]


def result(file, ran, survivors, all_keys=None):
    return {"file": file, "error": None, "ran": ran, "all_keys": all_keys or ran,
            "survivors": [{"key": k, "file": file} for k in survivors]}


def test_the_ratchet_fails_only_on_new_survivors():
    base = {"a.py::f::number::x => y": "equivalent: a tuning constant"}
    r = result("a.py", ["a.py::f::number::x => y", "a.py::g::and-or::p => q"], ["a.py::f::number::x => y"])
    new, fixed = mut.compare([r], base)
    assert new == [] and fixed == []
    r2 = result("a.py", ["a.py::f::number::x => y", "a.py::g::and-or::p => q"], ["a.py::g::and-or::p => q"])
    new, fixed = mut.compare([r2], base)
    assert [s["key"] for s in new] == ["a.py::g::and-or::p => q"] and fixed == ["a.py::f::number::x => y"]


def test_update_baseline_keeps_reasons_and_what_did_not_run():
    base = {"a.py::f::number::x => y": "equivalent: a tuning constant", "a.py::h::compare::m => n": "missing test",
            "a.py::gone::negate::u => v": "old", "b.py::k::raise-pass::r => pass": "missing test"}
    r = result("a.py", ["a.py::f::number::x => y", "a.py::g::and-or::p => q"], ["a.py::f::number::x => y", "a.py::g::and-or::p => q"],
               all_keys=["a.py::f::number::x => y", "a.py::g::and-or::p => q", "a.py::h::compare::m => n"])
    nb = mut.updated_baseline([r], base)
    assert nb["a.py::f::number::x => y"] == "equivalent: a tuning constant"   # the reviewed reason is kept
    assert nb["a.py::g::and-or::p => q"] == mut.UNREVIEWED                     # a new survivor asks for review
    assert nb["a.py::h::compare::m => n"] == "missing test"                    # exists but did not run (--max): kept
    assert "a.py::gone::negate::u => v" not in nb                              # that code is gone: dropped
    assert "b.py::k::raise-pass::r => pass" in nb                              # another file untouched


def test_targets_name_real_files_and_tests():
    targets = mut.load_targets()
    assert {t["file"] for t in targets} >= {"apps/llm-gateway/app/guardrails.py", "apps/estate-sync/syncsvc/guard.py",
                                            "apps/llm-gateway/app/killswitch.py"}
    for t in targets:
        assert (REPO / t["file"]).is_file()
        assert all((REPO / p).exists() for p in t["tests"])
        assert mut.find_mutants((REPO / t["file"]).read_bytes(), t["file"])          # every rail file parses and has mutants
    base = json.loads((REPO / "tools" / "mutate-baseline.json").read_text("utf-8"))["survivors"]
    assert base and all(v and v != mut.UNREVIEWED for v in base.values())             # every known survivor carries a reason
    reviewed = ("apps/estate-sync/syncsvc/guard.py::", "apps/llm-gateway/app/killswitch.py::")
    for k, v in base.items():                                                         # these two files are fully triaged
        if k.startswith(reviewed):
            assert v.startswith(("missing test:", "equivalent")), k
