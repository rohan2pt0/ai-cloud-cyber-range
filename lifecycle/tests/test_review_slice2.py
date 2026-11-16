"""Review slice 2 (docs/specs/review-ledger.md): what the review fixed stays fixed.

Nothing here starts Docker or a cluster: the scripts run against stand-ins that only record how they were called.
"""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def _stubs(tmp_path):
    """A folder of stand-in `docker` and `kind` that write their arguments to calls.log and do nothing else."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "calls.log"
    for name in ("docker", "kind"):
        f = bin_dir / name
        f.write_text('#!/bin/sh\necho "%s $*" >> "%s"\n' % (name, log), encoding="utf-8")
        f.chmod(0o755)
    return {"PATH": "%s:/usr/bin:/bin" % bin_dir, "HOME": str(tmp_path)}, log


def _teardown(tmp_path, *args):
    env, log = _stubs(tmp_path)
    r = subprocess.run(["bash", str(ROOT / "local/scripts/teardown.sh"), *args], env=env, text=True,
                       capture_output=True, stdin=subprocess.DEVNULL, timeout=30)
    return r, (log.read_text(encoding="utf-8") if log.exists() else "")


def test_teardown_keeps_the_data_unless_asked(tmp_path):
    r, calls = _teardown(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "compose" in calls and " down" in calls
    assert "down -v" not in calls                      # a plain stop never deletes a volume
    assert "data is kept" in r.stdout


def test_teardown_erase_needs_a_person_and_a_typed_word(tmp_path):
    r, calls = _teardown(tmp_path, "--erase")          # no terminal: nobody can type the word
    assert r.returncode == 1
    assert calls == ""                                 # nothing stopped, nothing deleted
    assert "Nothing was deleted" in r.stdout and "./securax backup" in r.stdout
    text = _read("local/scripts/teardown.sh")
    assert '[ "$_word" = "ERASE" ]' in text            # a typed word, not a single key
    assert text.index('"$_word" = "ERASE"') < text.index("down -v")


def test_teardown_refuses_an_option_it_does_not_know(tmp_path):
    r, calls = _teardown(tmp_path, "--force")
    assert r.returncode == 2 and calls == ""


def _function(rel, start, end="}"):
    out, on = [], False
    for line in _read(rel).splitlines():
        if line.startswith(start):
            on = True
        if on:
            out.append(line)
            if line.rstrip().endswith(end) and (line.startswith("}") or line.startswith(start)):
                if line.startswith("}") or line.rstrip().endswith("; }"):
                    break
    return "\n".join(out)


def test_a_key_is_strong_without_python(tmp_path):
    fn = _function("securax", "rand_hex(){")
    assert fn, "rand_hex is gone from securax"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for tool in ("head", "od", "tr"):                  # no python3 and no openssl on this path
        for base in ("/usr/bin", "/bin"):
            if os.path.exists(os.path.join(base, tool)):
                (bin_dir / tool).symlink_to(os.path.join(base, tool))
                break
    r = subprocess.run(["/bin/bash", "-c", fn + "\nrand_hex 24"], env={"PATH": str(bin_dir)}, text=True,
                       capture_output=True, timeout=30)
    key = r.stdout.strip()
    assert len(key) == 48 and all(c in "0123456789abcdef" for c in key), r.stderr
    again = subprocess.run(["/bin/bash", "-c", fn + "\nrand_hex 24"], env={"PATH": str(bin_dir)}, text=True,
                           capture_output=True, timeout=30).stdout.strip()
    assert again != key


def test_up_never_writes_a_short_key():
    text = _read("securax")
    assert "secrets.token_hex(24))')\"" not in text    # the old form wrote "sk-" when python3 was missing
    assert text.count('[ "${#_rk}" -ge 48 ] ||') == 2  # the gateway key and the sync token both check the length
    assert "read -rs GK" in text                       # a pasted key is not shown on the screen


def test_wsl_systemd_adds_to_the_file_and_respects_a_choice(tmp_path):
    fn = _function("install.sh", "wsl_systemd(){")
    assert fn, "wsl_systemd is gone from install.sh"

    def run(content):
        f = tmp_path / "wsl.conf"
        if content is None:
            f.unlink(missing_ok=True)
        else:
            f.write_text(content, encoding="utf-8")
        rc = subprocess.run(["bash", "-c", fn + '\nwsl_systemd "$1"', "x", str(f)], timeout=30).returncode
        return rc, f.read_text(encoding="utf-8")

    rc, out = run("[boot]\ncommand=x\n[user]\ndefault=a")
    assert rc == 0 and out.count("[boot]") == 1 and "[boot]\nsystemd=true\ncommand=x" in out
    rc, out = run("[network]\nfoo=1")                  # no newline at the end: the section must not be glued to it
    assert rc == 0 and "foo=1\n[boot]\nsystemd=true\n" in out
    rc, out = run("[boot]\nsystemd = false\n")         # the person chose: leave it
    assert rc != 0 and out == "[boot]\nsystemd = false\n"
    rc, out = run(None)
    assert rc == 0 and "[boot]\nsystemd=true" in out


def test_the_dns_advice_never_overwrites_the_wsl_file():
    for rel in ("securax", "docs/securax/121-DRIVE-HOME.md"):
        assert "sudo tee /etc/wsl.conf" not in _read(rel), rel
        assert "sudo tee -a /etc/wsl.conf" in _read(rel), rel


def test_the_server_install_checks_before_it_changes_the_machine():
    text = _read("install.sh")
    start = text.index('if [ "$SERVER" = 1 ]; then')
    first_change = text.index("run apt-get update", start)
    for check in ("needs the installer saved as a file", "Backup not found: $RESTORE", "Key file not found: $KEYFILE",
                  "--offline cannot be used with it"):
        assert start < text.index(check, start) < first_change, check
    assert "sed -n '2,18p'" in text                    # --help prints the whole header, not half of it
    assert 'if "$DIR/securax" open' in text            # "is open" is said only when it opened


def test_the_admission_test_passes_only_on_a_policy_denial():
    text = _read("local/scripts/kind-up.sh")
    assert "denied the request" in text and "not by the admission policy" in text
    assert "/tmp/" not in text
    assert "/tmp/" not in _read("local/scripts/bootstrap-laptop.sh")   # no fixed, guessable temp file
    assert "did not answer within a minute" in _read("local/scripts/bootstrap-laptop.sh")


def test_a_port_clash_gives_advice_for_this_system():
    text = _read("securax")
    assert "lsof -nP -iTCP:" in text and "ss -ltnp" in text
