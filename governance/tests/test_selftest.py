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


def test_network_probes_run_offline_so_ci_does_not_time_out():
    # a read-only probe must not depend on a live network: `backlog` reaches GitHub (15s api timeout) and timed out past
    # the 60s cap in CI, so its probe uses the local-only --offline mode the cockpit already uses.
    assert st.READONLY["backlog"] == ["backlog", "--offline"]


def test_subcommand_probes_are_real_and_read_only():
    # every SUBCOMMAND_PROBES key is a command the CLI dispatches (found via dispatch_table on the real securax text),
    # and no probe argv uses a word that changes state, so the extra probes stay side-effect free like READONLY.
    text = (ROOT / "securax").read_text("utf-8")
    bodies = st.dispatch_table(text)
    deny = {"up", "down", "start", "stop", "render", "reconcile", "pull", "push",
            "send", "write", "add", "approve", "install", "update", "release"}
    assert set(st.SUBCOMMAND_PROBES) <= set(bodies), \
        f"not a dispatched command: {sorted(set(st.SUBCOMMAND_PROBES) - set(bodies))}"
    for cmd, argvs in st.SUBCOMMAND_PROBES.items():
        assert argvs, f"{cmd} lists no subcommand probes"
        for argv in argvs:
            bad = deny & set(argv)
            assert not bad, f"{cmd} probe {argv} uses a state-changing word: {bad}"


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


def test_is_ok_requires_wired_clean_modules_and_clean_probes():
    clean = {"command": "x", "wired": True, "modules": [{"state": "ok"}], "probe": {"state": "ok"}, "subprobes": []}
    assert st._is_ok(clean)
    assert not st._is_ok({"command": "x", "wired": False, "modules": [], "probe": None, "subprobes": []})
    assert not st._is_ok({"command": "x", "wired": True, "modules": [{"state": "fail"}], "probe": None, "subprobes": []})
    assert not st._is_ok({"command": "x", "wired": True, "modules": [], "probe": {"state": "fail"}, "subprobes": []})
    assert not st._is_ok({"command": "x", "wired": True, "modules": [], "probe": None, "subprobes": [{"state": "fail"}]})


def test_summary_counts_probes_and_lists_failures():
    # _summarize is pure, so feed it synthetic results to prove the counts and the failure list are exact.
    results = [
        {"command": "comply", "wired": True, "modules": [{"file": "a.py", "state": "ok", "detail": ""}],
         "probe": {"argv": ["comply", "rbi"], "state": "ok", "detail": ""},
         "subprobes": [{"argv": ["comply", "owasp-ai"], "state": "fail", "detail": "boom"}], "ok": False},
        {"command": "bogus", "wired": False, "modules": [{"file": "b.py", "state": "fail", "detail": "x"},
                                                          {"file": "c.py", "state": "dep", "detail": "y"}],
         "probe": None, "subprobes": [], "ok": False},
    ]
    s = st._summarize(results)
    assert s["probes_run"] == 2
    assert s["probes_failed"] == ["comply comply owasp-ai: boom"]
    assert s["modules_broken"] == ["b.py (x)"]
    assert s["modules_loaded"] == 1
    assert s["modules_need_dep"] == 1
    assert s["wired"] == 1
    assert s["not_wired"] == ["bogus"]
    assert s["failed_commands"] == ["comply", "bogus"]


def test_summary_reports_every_probe_run_on_the_real_estate():
    data = st.run(probe_readonly=True)
    expected = sum((1 if r["probe"] else 0) + len(r["subprobes"]) for r in data["commands"])
    assert data["summary"]["probes_run"] == expected
    assert expected > 0


def test_report_marks_a_failure_clearly():
    data = {"ok": False, "summary": {"commands": 2, "wired": 1, "not_wired": ["bogus"], "modules_loaded": 1,
            "modules_need_dep": 0, "modules_broken": [], "probes_run": 0, "probes_failed": [], "failed_commands": ["bogus"]},
            "commands": [{"command": "bogus", "wired": False, "modules": [], "probe": None, "ok": False}]}
    lines = []
    st.report(data, say=lines.append)
    assert any("not wired" in ln for ln in lines) and any("need attention" in ln for ln in lines)
