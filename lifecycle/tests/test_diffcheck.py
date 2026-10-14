"""diffcheck enforces the build contract's mechanical hard rules on a real git diff."""
import importlib.util
import pathlib
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("dc", REPO / "lifecycle" / "diffcheck.py")
dc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dc)


def git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd, check=True, text=True, capture_output=True).stdout


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    files = {
        "tests/test_a.py": "def test_one():\n    assert 1 == 1\n    assert 2 == 2\n\n\ndef test_two():\n    assert 3 == 3\n",
        "app/guardrails.py": 'RULES = [\n    ("PI-001-override", "x", "high"),\n    ("PI-002-sysprompt-exfil", "y", "high"),\n]\n',
        "app/code.py": "# a long explanatory comment line one\n# a long explanatory comment line two\n# a long explanatory comment line three\n"
                       "# a long explanatory comment line four\n# a long explanatory comment line five\nx = 1\n",
        ".github/workflows/ci.yml": "jobs:\n  t:\n    steps:\n      - run: pytest\n",
    }
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path


def rules(repo, strict=False):
    changes, ws = dc.collect("HEAD", repo)
    return {r["rule"] for r in dc.evaluate(changes, ws) if r["level"] == "BLOCK" or strict}


def test_a_clean_change_passes(repo):
    (repo / "app/code.py").write_text((repo / "app/code.py").read_text() + "y = 2\n")
    (repo / "tests/test_b.py").write_text("def test_new():\n    assert True\n")
    assert rules(repo) == set()


def test_skipping_a_test_is_blocked(repo):
    t = repo / "tests/test_a.py"
    t.write_text("import pytest\n\n\n@pytest.mark.skip\n" + t.read_text())
    assert "test-skipped" in rules(repo)


def test_deleting_tests_and_assertions_is_blocked(repo):
    (repo / "tests/test_a.py").write_text("def test_one():\n    pass\n")
    r = rules(repo)
    assert "test-removed" in r and "assertions-weakened" in r


def test_deleting_a_guardrail_rule_is_blocked(repo):
    g = repo / "app/guardrails.py"
    g.write_text(g.read_text().replace('    ("PI-002-sysprompt-exfil", "y", "high"),\n', ""))
    assert "rail-removed" in rules(repo)


def test_loosening_fail_closed_defaults_is_blocked(repo):
    (repo / "app/cfg.py").write_text('FAIL_MODE = "open"\n')
    assert "rails-loosened" in rules(repo)


@pytest.mark.parametrize("line", ["    continue-on-error: true", "      - run: pytest || true"])
def test_making_ci_non_fatal_is_blocked(repo, line):
    w = repo / ".github/workflows/ci.yml"
    w.write_text(w.read_text() + line + "\n")
    assert "fake-green" in rules(repo)


def test_a_secret_or_env_file_is_blocked(repo):
    (repo / "app/k.py").write_text('KEY = "' + "AKIA" + 'ABCDEFGHIJKLMNOP"\n')
    (repo / ".env").write_text("X=1\n")
    r = rules(repo)
    assert "secret-added" in r and "env-file-added" in r
    (repo / ".env").unlink()
    (repo / ".env.example").write_text("X=\n")
    assert "env-file-added" not in rules(repo)


def test_scope_creep_and_churn_only_warn_unless_strict(repo):
    for i in range(14):
        (repo / f"app/m{i}.py").write_text("x = 1\n")
    assert rules(repo) == set() and "scope-files" in rules(repo, strict=True)


def test_deleted_comments_and_new_dependencies_warn(repo):
    c = repo / "app/code.py"
    c.write_text("x = 1\n")
    (repo / "requirements.txt").write_text("requests\n")
    assert {"comments-deleted", "dependency-change"} <= rules(repo, strict=True)


def test_whitespace_only_churn_is_noticed_on_existing_files(repo):
    c = repo / "app/code.py"
    c.write_text("".join(f"x{i} =   {i}\n" for i in range(12)))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "more")
    c.write_text("".join(f"x{i} = {i}\n" for i in range(12)))          # pure reformat of 12 lines
    assert "whitespace-churn" in rules(repo, strict=True)
