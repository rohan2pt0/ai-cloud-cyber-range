"""tools/release.py (doc 21): the next version follows from the changelog alone, a cut moves [Unreleased] under it
without touching anything else, the notes of a version are its own section only, and an empty [Unreleased] cuts nothing."""
import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("securax_release_t", ROOT / "tools" / "release.py")
rel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rel)

LOG = """# Changelog

Intro kept as written.

## [Unreleased]
{body}
## [0.2.0] - 2026-10-17
### Added
- **Old thing** (doc 1)
  - a sub-point

## [0.1.0] - 2026-10-11
### Added
- First
"""


def repo(tmp_path, body, version="0.2.0"):
    (tmp_path / "CHANGELOG.md").write_text(LOG.format(body=body))
    (tmp_path / "VERSION").write_text(version + "\n")
    return tmp_path


@pytest.mark.parametrize("body, version, want", [
    ("### Fixed\n- a fix\n", "0.2.0", ("0.2.1", "patch")),
    ("### Fixed\n- a fix\n### Security\n- a CVE closed\n", "0.2.1", ("0.2.2", "patch")),
    ("### Added\n- new\n### Fixed\n- a fix\n", "0.2.1", ("0.3.0", "minor")),
    ("### Changed\n- BREAKING: renamed a command\n", "0.3.0", ("0.4.0", "minor")),     # 0.x promises no stability
    ("### Changed\n- BREAKING: renamed a command\n", "1.4.2", ("2.0.0", "major")),
])
def test_the_next_version_follows_from_the_changelog(body, version, want):
    assert rel.bump(version, body) == want


def test_an_empty_unreleased_has_nothing_to_release(tmp_path):
    r = repo(tmp_path, "\n### Added\n\n")
    assert rel.plan(r)["next"] == ""
    with pytest.raises(SystemExit, match="nothing"):
        rel.cut(r, refresh=False)


def test_a_cut_moves_unreleased_under_the_new_version_and_keeps_the_rest(tmp_path):
    r = repo(tmp_path, "### Added\n- **Releases like open projects ship them**\n  - weekly\n### Fixed\n- a fix\n")
    before = (r / "CHANGELOG.md").read_text()
    assert rel.cut(r, date="2026-10-22", refresh=False) == "0.3.0"
    after = (r / "CHANGELOG.md").read_text()
    assert (r / "VERSION").read_text() == "0.3.0\n"
    assert "## [Unreleased]\n\n## [0.3.0] - 2026-10-22\n### Added\n- **Releases like open projects ship them**" in after
    assert after.replace("## [Unreleased]\n\n## [0.3.0] - 2026-10-22\n", "## [Unreleased]\n") == before   # nothing else moved
    assert rel.plan(r)["next"] == ""                                     # the new [Unreleased] is empty
    assert rel.notes("0.3.0", r).startswith("### Added") and "0.2.0" not in rel.notes("0.3.0", r)
    assert "Old thing" in rel.notes("0.2.0", r) and "First" not in rel.notes("0.2.0", r)


def test_the_real_changelog_plans_cleanly():
    p = rel.plan()
    assert p["current"] == (ROOT / "VERSION").read_text().strip()
    assert not p["next"] or p["next"] != p["current"]
