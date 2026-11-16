"""The Windows launchers are the first thing a Windows user touches, and nothing here can run them.

So these checks are static. They hold the causes found in the 2026-11-16 review: wrong line endings, a window
that closes before the error can be read, a path that breaks on a space, and reading `wsl -l` (UTF-16 on older
Windows). Nothing in this file proves a launcher works on a real PC: that needs a Windows run (review ledger).
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATS = sorted(ROOT.glob("*.bat"))
CMD = ROOT / "securax.cmd"
LOG = "last-run.log"


def _lines(path):
    return path.read_bytes().decode("ascii").split("\r\n")


def _code(path):
    """The lines that run: no REM lines, no blank lines."""
    return [ln for ln in _lines(path) if ln.strip() and not ln.strip().upper().startswith("REM")]


def test_there_are_launchers_to_check():
    assert len(BATS) >= 5 and CMD.exists()


def test_every_batch_file_has_windows_line_endings_and_plain_ascii():
    for path in BATS + [CMD]:
        raw = path.read_bytes()
        assert b"\r\n" in raw, f"{path.name}: no CRLF line endings (cmd.exe misreads labels in an LF file)"
        assert b"\n" not in raw.replace(b"\r\n", b""), f"{path.name}: a line ends in LF alone; it must be CRLF"
        assert all(byte < 128 for byte in raw), f"{path.name}: a non-ASCII character (it prints as noise in cmd.exe)"


def test_git_keeps_batch_files_crlf_on_every_checkout():
    out = subprocess.run(["git", "check-attr", "eol", "--", "securax.cmd", "START-HERE-Windows.bat"],
                         cwd=ROOT, capture_output=True, text=True).stdout
    assert out.count("eol: crlf") == 2, out


def test_every_launcher_pauses_on_every_way_out():
    """A double-clicked window closes at `exit`: each one must have a pause just before it, failures above all."""
    for path in BATS:
        code = _code(path)
        exits = [i for i, ln in enumerate(code) if ln.strip().lower().startswith("exit /b")]
        assert len(exits) >= 3, f"{path.name}: expected a success exit and two failure exits"
        for i in exits:
            assert code[i - 1].strip().lower() == "pause", f"{path.name}: `{code[i].strip()}` with no pause before it"
        assert code[-1].strip().lower().startswith("exit /b"), f"{path.name}: must not fall off the end"
        text = "\n".join(code)
        assert re.search(r"if errorlevel 1 goto failed", text), f"{path.name}: the command's failure is not checked"
        for label in (":failed", ":nofiles"):
            block = text.split("\n" + label + "\n", 1)[1]
            assert "Next step:" in block.split("exit /b", 1)[0], f"{path.name} {label}: no one next step"
            assert "%LOG%" in block, f"{path.name} {label}: does not say where the log is"


def test_every_launcher_survives_a_space_in_its_folder_and_a_missing_neighbour():
    for path in BATS:
        text = "\n".join(_code(path))
        assert 'call "%~dp0securax.cmd" ' in text, f"{path.name}: must call the launcher by a quoted %~dp0 path"
        assert 'if not exist "%~dp0securax.cmd" goto nofiles' in text, f"{path.name}: run from a ZIP, it must say so"
        assert LOG in text and "%LOCALAPPDATA%\\SecuRAX" in text
        for ln in _code(path):
            for m in re.finditer(r"%~dp0", ln):
                assert ln.count('"', 0, m.start()) % 2 == 1, f"{path.name}: %~dp0 outside quotes: {ln.strip()}"


def test_the_wsl_launcher_logs_explains_and_never_reads_the_distribution_list():
    code = _code(CMD)
    text = "\n".join(code)
    assert "%LOCALAPPDATA%\\SecuRAX" in text and LOG in text
    assert not re.search(r"wsl(\.exe)?\s+(-l\b|--list\b)", text), "`wsl -l` prints UTF-16 on older Windows: ask the distribution"
    assert "$WSL_DISTRO_NAME" in text and "docker-desktop" in text
    assert "--cd \"~" not in text and "--cd ~/" not in text, "wsl --cd takes ~ alone, a Linux path or a Windows path"
    for label, words in ((":nowsl", "wsl --install -d Ubuntu"), (":nofiles", "Extract All"), (":nodocker", "Docker Desktop")):
        block = text.split("\n" + label + "\n", 1)[1]
        assert "Next step" in block and words in block, label
    assert "pause" not in [ln.strip().lower() for ln in code], "securax.cmd is used from PowerShell: only the .bat files pause"
    # %* inside a ( ) block breaks on an argument with a bracket; an unquoted wsl path breaks on a space
    depth = 0
    for ln in code:
        if "%*" in ln:
            assert depth == 0 and not ln.rstrip().endswith("("), f"%* inside a block: {ln.strip()}"
        if ln.rstrip().endswith("("):
            depth += 1
        elif ln.strip().startswith(")"):
            depth -= 1
        assert '-d %DISTRO%' not in ln and '--cd %WORK%' not in ln, f"unquoted: {ln.strip()}"
    assert code[-1].strip().endswith("exit /b %RC%")


def test_every_goto_has_its_label():
    for path in BATS + [CMD]:
        code = [ln.strip() for ln in _code(path)]
        labels = {ln[1:].lower() for ln in code if ln.startswith(":")}
        for ln in code:
            for target in re.findall(r"\bgoto\s+:?(\w+)", ln, flags=re.I):
                assert target.lower() in labels, f"{path.name}: goto {target} has no label"


def test_the_powershell_installer_logs_and_keeps_the_window_open_on_failure():
    ps1 = (ROOT / "install.ps1").read_text()
    assert LOG in ps1 and "LOCALAPPDATA" in ps1 and "Next step:" in ps1 and "Read-Host" in ps1
    assert "trap {" in ps1, "an unexpected error must reach Stop-Here, not close the window"
    # every way out with a failure goes through Stop-Here; the only bare exits are success and inside Stop-Here itself
    bare = [ln.strip() for ln in ps1.splitlines() if re.search(r"\bexit\b", ln) and "Stop-Here" not in ln and not ln.strip().startswith("#")]
    assert bare == ["exit $code", "exit 0"], bare
