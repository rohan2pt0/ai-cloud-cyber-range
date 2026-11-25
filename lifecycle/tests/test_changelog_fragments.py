"""tools/changelog_fold.py (queue changelog-fragments): a change writes one line in changes/<branch>.md instead of
editing CHANGELOG.md, and the fold moves every fragment to the top of [Unreleased] in file-name order, then removes it.
A fragment that is empty or longer than one line is refused, and with no fragments the changelog is untouched."""
import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("securax_changelog_fold_t", ROOT / "tools" / "changelog_fold.py")
cf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cf)

LOG = """# Changelog

Intro kept as written.

## [Unreleased]
- an older line

## [0.2.0] - 2026-10-17
- old
"""


def repo(tmp_path, fragments):
    (tmp_path / "CHANGELOG.md").write_text(LOG)
    d = tmp_path / "changes"
    d.mkdir()
    for name, body in fragments.items():
        (d / name).write_text(body)
    return tmp_path


def test_two_fragments_become_bullets_at_the_top_in_file_name_order_and_are_removed(tmp_path):
    r = repo(tmp_path, {"b.md": "second change\n", "a.md": "first change\n"})
    assert cf.fold(r) == 2
    text = (r / "CHANGELOG.md").read_text()
    assert "## [Unreleased]\n- first change\n- second change\n- an older line\n" in text
    assert text.endswith("- old\n")
    assert not (r / "changes" / "a.md").exists() and not (r / "changes" / "b.md").exists()


@pytest.mark.parametrize("fragments", [{}, None])
def test_no_fragments_changes_nothing(tmp_path, fragments):
    (tmp_path / "CHANGELOG.md").write_text(LOG)
    if fragments is not None:
        (tmp_path / "changes").mkdir()
    before = (tmp_path / "CHANGELOG.md").read_text()
    assert cf.fold(tmp_path) == 0
    assert (tmp_path / "CHANGELOG.md").read_text() == before


def test_a_fragment_with_more_than_one_line_is_refused(tmp_path):
    r = repo(tmp_path, {"a.md": "one line\ntwo lines\n"})
    before = (r / "CHANGELOG.md").read_text()
    with pytest.raises(ValueError, match="one line"):
        cf.fold(r)
    assert (r / "CHANGELOG.md").read_text() == before and (r / "changes" / "a.md").exists()


def test_an_empty_fragment_is_refused(tmp_path):
    r = repo(tmp_path, {"a.md": " \n"})
    before = (r / "CHANGELOG.md").read_text()
    with pytest.raises(ValueError, match="empty"):
        cf.fold(r)
    assert (r / "CHANGELOG.md").read_text() == before and (r / "changes" / "a.md").exists()


def test_the_command_folds_and_reports_a_refusal(tmp_path, capsys):
    r = repo(tmp_path, {"a.md": "one change\n"})
    assert cf.main([str(r)]) == 0
    assert "1 fragment(s) folded" in capsys.readouterr().out
    bad = tmp_path / "bad"
    bad.mkdir()
    r2 = repo(bad, {"a.md": "one line\ntwo lines\n"})
    assert cf.main([str(r2)]) == 1
    assert "one line" in capsys.readouterr().err


def test_help_names_the_tool(capsys):
    with pytest.raises(SystemExit) as exit_code:
        cf.main(["--help"])
    assert exit_code.value.code == 0
    assert "CHANGELOG FRAGMENTS" in capsys.readouterr().out
