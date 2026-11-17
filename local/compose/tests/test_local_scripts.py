"""The four scripts in local/scripts fail well and never cost a person their data (review ledger, slice 2).

Each script runs in a throwaway copy of its folder layout, with stand-ins for docker, kind, kubectl, helm and curl first on
the PATH: nothing here starts, builds or deletes anything real.
"""
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "local" / "scripts"


def _tree(tmp_path, script):
    """A copy of the script in the same layout it lives in, so its own ROOT is the temp folder."""
    (tmp_path / "local" / "scripts").mkdir(parents=True)
    (tmp_path / "local" / "compose").mkdir()
    (tmp_path / "local" / "k8s").mkdir()
    (tmp_path / "local" / "compose" / ".env.example").write_text("EXAMPLE=1\n")
    (tmp_path / "local" / "compose" / "litellm-config.yaml").write_text("model_list: []\n")
    shutil.copy(SCRIPTS / script, tmp_path / "local" / "scripts" / script)
    return tmp_path / "local" / "scripts" / script


def _fake(tmp_path, name, body):
    d = tmp_path / "fakebin"
    d.mkdir(exist_ok=True)
    p = d / name
    p.write_text("#!/bin/sh\n" + body + "\n")
    p.chmod(0o755)


def _run(tmp_path, script, *args, stdin=""):
    env = {"PATH": f"{tmp_path / 'fakebin'}:/usr/bin:/bin", "HOME": str(tmp_path), "CALLS": str(tmp_path / "calls.log")}
    return subprocess.run(["bash", str(script), *args], input=stdin, capture_output=True, text=True, env=env, timeout=60)


def _calls(tmp_path):
    f = tmp_path / "calls.log"
    return f.read_text() if f.exists() else ""


def _teardown(tmp_path):
    script = _tree(tmp_path, "teardown.sh")
    _fake(tmp_path, "docker", 'echo "docker $*" >> "$CALLS"')
    _fake(tmp_path, "kind", 'echo "kind $*" >> "$CALLS"')
    return script


def test_teardown_stops_everything_and_keeps_the_data(tmp_path):
    r = _run(tmp_path, _teardown(tmp_path))
    calls = _calls(tmp_path)
    assert r.returncode == 0, r.stderr
    assert " down" in calls and " -v" not in calls and "--volumes" not in calls
    assert "kept" in r.stdout.lower()


def test_teardown_erases_only_after_the_typed_word_and_names_the_safe_step_first(tmp_path):
    script = _teardown(tmp_path)
    no = _run(tmp_path, script, "--erase", stdin="y\n")
    assert no.returncode == 0 and " -v" not in _calls(tmp_path)
    assert "./securax backup" in no.stdout and "Nothing was deleted" in no.stdout
    (tmp_path / "calls.log").unlink()
    nothing_typed = _run(tmp_path, script, "--erase", stdin="")
    assert nothing_typed.returncode == 0 and " -v" not in _calls(tmp_path)
    (tmp_path / "calls.log").unlink()
    yes = _run(tmp_path, script, "--erase", stdin="erase\n")
    assert yes.returncode == 0 and " down -v" in _calls(tmp_path)


def test_teardown_refuses_an_option_it_does_not_know(tmp_path):
    r = _run(tmp_path, _teardown(tmp_path), "-v")
    assert r.returncode != 0 and "--erase" in (r.stdout + r.stderr) and " down" not in _calls(tmp_path)


def test_bootstrap_says_the_gateway_never_answered_instead_of_blaming_the_guardrail(tmp_path):
    script = _tree(tmp_path, "bootstrap-laptop.sh")
    for tool in ("docker", "kind", "kubectl", "helm", "sleep"):
        _fake(tmp_path, tool, 'echo "' + tool + ' $*" >> "$CALLS"')
    _fake(tmp_path, "curl", "exit 7")                      # nothing is listening
    r = _run(tmp_path, script)
    out = r.stdout + r.stderr
    assert r.returncode != 0
    assert "did not answer" in out and "./securax why" in out
    assert "expected 400" not in out                       # the smoke test never ran, so it cannot have failed


def test_bootstrap_keeps_no_answer_file_at_a_fixed_path_in_tmp():
    assert "/tmp/range_resp.json" not in (SCRIPTS / "bootstrap-laptop.sh").read_text()


def _kind_up(tmp_path, refusal):
    script = _tree(tmp_path, "kind-up.sh")
    _fake(tmp_path, "kind", '[ "$1 $2" = "get clusters" ] && echo range; exit 0')
    _fake(tmp_path, "docker", "exit 0")
    _fake(tmp_path, "helm", "exit 0")
    _fake(tmp_path, "kubectl", 'case "$*" in *" run bad "*) echo "' + refusal + '" >&2; exit 1 ;; esac; exit 0')
    return _run(tmp_path, script)


def test_kind_up_passes_when_the_admission_policy_refuses_the_insecure_pod(tmp_path):
    r = _kind_up(tmp_path, "Error from server: admission webhook validate.kyverno.svc-fail denied the request: policy says no")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS" in r.stdout


def test_kind_up_does_not_call_any_other_failure_a_pass(tmp_path):
    r = _kind_up(tmp_path, "The connection to the server was refused - did you specify the right host or port?")
    out = r.stdout + r.stderr
    assert r.returncode != 0 and "PASS" not in out
    assert "NOT PROVEN" in out


def test_update_does_not_blame_local_changes_when_there_was_nothing_new():
    text = (ROOT / "securax").read_text()
    branch = text[text.index("\n  update)\n"):text.index("\n  channel)")]
    nothing_new = branch.index("There was nothing new to pull")
    assert branch.index('if [ "$PREV" = "$NEW" ]; then', branch.index("# 2) the new version did not come up healthy")) < nothing_new
    assert nothing_new < branch.index("an automatic rollback was not safe")
