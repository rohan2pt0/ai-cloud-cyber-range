"""The estate's own records travel with the backup (doc 82): which versions worked, the restore drills and the honesty
checks. A restore brings back only what the new machine does not have, so its own newer records are never overwritten.
The test runs the very lines ./securax uses, in bash, on temporary folders."""
import pathlib
import subprocess
import tarfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
CLI = (ROOT / "securax").read_text("utf-8").splitlines()


def snippet(start: str, lines: int) -> str:
    i = next(n for n, line in enumerate(CLI) if line.strip().startswith(start))
    return "\n".join(CLI[i:i + lines])


def run(script: str, env: dict) -> None:
    subprocess.run(["bash", "-c", "set -e\n" + script], env={"PATH": "/usr/bin:/bin", **env}, check=True)


def test_the_records_go_into_the_backup_and_come_back_without_overwriting(tmp_path):
    home, stg = tmp_path / "home", tmp_path / "stg"
    home.mkdir()
    stg.mkdir()
    (home / "known-good.jsonl").write_text('{"version":"0.2.0"}\n')
    (home / "drills.log").write_text("drill ok\n")
    run(snippet('_RH="${SECURAX_HOME_DIR:-$HOME/.securax}"; _REC=""', 2), {"SECURAX_HOME_DIR": str(home), "STG": str(stg)})
    with tarfile.open(stg / "records.tgz") as tf:
        assert sorted(tf.getnames()) == ["drills.log", "known-good.jsonl"]          # honesty.jsonl absent: simply skipped
    assert (stg / "MANIFEST").read_text().split() == ["records"]

    new = tmp_path / "new"
    new.mkdir()
    (new / "known-good.jsonl").write_text('{"version":"0.3.0"}\n')                   # this machine already has its own
    run(snippet('if [ -f "$STG/records.tgz" ]; then', 4), {"SECURAX_HOME_DIR": str(new), "STG": str(stg)})
    assert (new / "known-good.jsonl").read_text() == '{"version":"0.3.0"}\n'
    assert (new / "drills.log").read_text() == "drill ok\n"


def test_no_records_means_no_part_and_no_failure(tmp_path):
    stg = tmp_path / "stg"
    stg.mkdir()
    run(snippet('_RH="${SECURAX_HOME_DIR:-$HOME/.securax}"; _REC=""', 2), {"SECURAX_HOME_DIR": str(tmp_path / "empty"), "STG": str(stg)})
    assert not (stg / "records.tgz").exists() and not (stg / "MANIFEST").exists()
