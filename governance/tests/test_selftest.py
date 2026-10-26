"""Tests for ./securax selftest (doc 117): it proves commands load/run, and it must itself catch real breakage."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("securax_selftest_t", ROOT / "governance" / "selftest.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


st = _load()


def test_the_estate_passes_its_own_selftest():
    # the whole point: on a clean checkout every command is wired, every module loads, every read-only probe runs.
    data = st.run(probe_readonly=True)
    assert data["ok"], data["summary"]["failed_commands"] + data["summary"]["modules_broken"] + data["summary"]["probes_failed"]
    assert data["summary"]["commands"] >= 40                 # the real surface, not an empty parse
    assert "selftest" in [r["command"] for r in data["commands"]]


def test_every_advertised_command_is_wired():
    text = (ROOT / "securax").read_text("utf-8")
    known = st.recognized(text)
    missing = [c for c in st.advertised() if c not in known]
    assert not missing, f"advertised but not dispatched: {missing}"


def test_load_module_flags_broken_but_not_missing_deps(tmp_path):
    good = tmp_path / "good.py"
    good.write_text("X = 1\n")
    broken = tmp_path / "broken.py"
    broken.write_text("def f(:\n")                            # a syntax error = a real fault
    needs_dep = tmp_path / "needsdep.py"
    needs_dep.write_text("import a_package_that_is_not_installed_anywhere_12345\n")
    # load_module resolves paths under ROOT, so test the logic via a relative path trick: copy into a temp rel dir.
    import shutil
    d = ROOT / "governance" / "_selftest_tmp_"
    d.mkdir(exist_ok=True)
    try:
        shutil.copy(good, d / "good.py")
        shutil.copy(broken, d / "broken.py")
        shutil.copy(needs_dep, d / "needsdep.py")
        assert st.load_module("governance/_selftest_tmp_/good.py")[0] == "ok"
        assert st.load_module("governance/_selftest_tmp_/broken.py")[0] == "fail"
        assert st.load_module("governance/_selftest_tmp_/needsdep.py")[0] == "dep"   # missing dep is NOT a code fault
        assert st.load_module("governance/_selftest_tmp_/does_not_exist.py")[0] == "fail"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_threw_detects_a_traceback_not_a_handled_nonzero():
    import subprocess
    thrown = subprocess.CompletedProcess([], 1, "", "Traceback (most recent call last):\n  ValueError")
    handled = subprocess.CompletedProcess([], 1, "nothing configured yet\n", "")
    assert st._threw(thrown) and not st._threw(handled)


def test_report_marks_a_failure_clearly():
    data = {"ok": False, "summary": {"commands": 2, "wired": 1, "not_wired": ["bogus"], "modules_loaded": 1,
            "modules_need_dep": 0, "modules_broken": [], "probes_run": 0, "probes_failed": [], "failed_commands": ["bogus"]},
            "commands": [{"command": "bogus", "wired": False, "modules": [], "probe": None, "ok": False}]}
    lines = []
    st.report(data, say=lines.append)
    assert any("not wired" in ln for ln in lines) and any("need attention" in ln for ln in lines)
