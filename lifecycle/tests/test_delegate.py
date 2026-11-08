"""The delegate hand-off: the in-session path parses, never touches the caller's branch or git config, and the skill keeps
four paths so no single one (a GitHub secret, Actions, one session) can stop the work."""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "lifecycle" / "delegate_here.sh"
SKILL = ROOT / ".claude" / "skills" / "delegate" / "SKILL.md"


def test_the_in_session_path_parses_and_builds_in_a_throwaway_worktree():
    assert subprocess.run(["bash", "-n", str(SCRIPT)]).returncode == 0
    text = SCRIPT.read_text("utf-8")
    assert "git worktree add" in text and "worktree remove" in text
    assert "git config" not in text, "a worktree shares the repo config: set the author with GIT_* variables"
    assert "git push -q origin \"HEAD:refs/heads/$br\"" in text and "autobuild/" in text


def test_the_skill_keeps_four_paths_and_never_needs_the_github_pr_setting():
    text = SKILL.read_text("utf-8")
    for path in ("**A. GitHub Actions**", "**B. This session.**", "**C. Claude does it**", "**D. On the owner's laptop:**"):
        assert path in text
    assert "request_credential" in text and "opencode.ai" in text
    assert "is never needed" in text
