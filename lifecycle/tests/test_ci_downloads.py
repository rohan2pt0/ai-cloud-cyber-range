"""A GitHub Releases hiccup (a 504) must not turn CI red: every curl in the workflows that fetches a pinned tool from a
release endpoint retries with backoff, and every downloaded release archive is checksum-verified with `sha256sum -c`
before it is used (a retry that lands a corrupted or tampered file would otherwise be trusted). This test fails instead."""
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
RETRY_FLAGS = ("--retry 5", "--retry-all-errors", "--retry-delay 3")
RELEASE_URL = re.compile(r"(get\.helm\.sh|github\.com/[^\"'\s]+/releases/download/)\S*")
ARCHIVE_URL = re.compile(r"\S+\.(?:tar\.gz|tgz)\b")


def _runs():
    for f in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        doc = yaml.safe_load(f.read_text("utf-8"))
        for job, spec in (doc.get("jobs") or {}).items():
            for i, step in enumerate(spec.get("steps", [])):
                if isinstance(step, dict) and isinstance(step.get("run"), str):
                    where = f"{f.name}:{job}: step {step.get('name', i + 1)!r}"
                    yield where, step["run"].splitlines()


def test_every_release_download_retries_and_is_checksum_verified():
    found = False
    for where, lines in _runs():
        for i, line in enumerate(lines):
            if "curl" not in line or not RELEASE_URL.search(line):
                continue
            found = True
            for flag in RETRY_FLAGS:
                assert flag in line, f"{where}: release download without {flag}: {line.strip()}"
            assert not re.search(r"\|\s*tar\b", line), f"{where}: download piped straight into tar: {line.strip()}"
            url = RELEASE_URL.search(line).group(0)
            if not ARCHIVE_URL.search(url):
                continue  # a checksums.txt is the trust anchor itself; it cannot verify itself
            m = re.search(r"-o\s+(\S+)", line)
            assert m, f"{where}: archive download must go to a file (-o), not a pipe: {line.strip()}"
            target = m.group(1)
            name = pathlib.Path(target.rstrip('"\'')).name
            rest = lines[i + 1:]
            checked = next((j for j, l in enumerate(rest) if "sha256sum" in l and name in l), None)
            assert checked is not None, f"{where}: {name} is never verified with sha256sum -c before use"
            used = next((j for j, l in enumerate(rest) if re.search(r"\btar\s", l)), None)
            assert used is None or used > checked, f"{where}: {name} is unpacked before its sha256 check"
    assert found, "no release download found in any workflow: the test checks nothing"


def test_no_download_is_piped_straight_into_tar():
    for where, lines in _runs():
        for line in lines:
            if "curl" in line and RELEASE_URL.search(line):
                assert not re.search(r"\|\s*tar\b", line), f"{where}: {line.strip()}"
