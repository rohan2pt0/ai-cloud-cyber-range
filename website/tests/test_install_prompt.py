"""Install by pasting one sentence into the AI agent you already use (queue ai-install): install.txt is written for the
agent that does the install, stops and hands the person the deploy guide's steps when it cannot run shell commands, asks
before installing Docker, names only the real commands and never asks for a key or password; the site build fills its
address, and the homepage hero shows the sentence with a Copy button."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
INSTALL = ROOT / "website" / "install.txt"
HERO = ROOT / "website" / "index.html"
BUILD = ROOT / "website" / "build.sh"

ASKED = re.compile(r"(paste|enter|type|provide|send|share|copy|asks? for)\s+(your|a|the|their)?\s*"
                   r"(api[\s-]?key|key|token|password|secret)", re.I)


def test_the_install_file_opens_as_a_note_to_the_ai_that_does_the_install():
    text = INSTALL.read_text("utf-8")
    first = next(line for line in text.splitlines() if line.strip())
    assert "AI" in first and "install" in first.lower(), first


def test_the_agent_stops_and_hands_the_person_the_deploy_guide_when_it_cannot_run_shell_commands():
    text = INSTALL.read_text("utf-8")
    low = text.lower()
    assert "cannot run shell commands" in low
    assert "docs/securax/114-GO-LIVE-TODAY.md" in text
    for step in ("git clone", "./securax go", "./securax doctor"):
        assert step in text


def test_it_asks_the_person_before_installing_docker():
    assert "ask the person before you install docker" in INSTALL.read_text("utf-8").lower()


def test_it_names_only_the_real_commands_and_never_asks_for_a_key_or_password():
    text = INSTALL.read_text("utf-8")
    for command in ("git clone", "./securax go", "./securax doctor", "./securax why"):
        assert command in text
    named = [ln.strip() for ln in text.splitlines() if re.match(r"^\s*(git clone|\./securax)\b", ln)]
    allowed = ("git clone ", "./securax go", "./securax doctor", "./securax why")
    assert named and all(ln.startswith(allowed) for ln in named), named
    assert not [ln for ln in text.splitlines() if ASKED.search(ln)]


def test_the_site_build_fills_the_address_in_the_install_file_too():
    assert "install.txt" in BUILD.read_text("utf-8")


def test_the_homepage_hero_shows_the_sentence_in_a_box_with_a_copy_button():
    page = HERO.read_text("utf-8")
    # SITE_URL ends with a slash (website/build.sh builds "${SITE_URL}docs/"), so no second one here.
    assert "Read {{SITE_URL}}install.txt and install SecuRAX for me" in page
    start = page.index('<section class="hero">')
    hero = page[start:page.index("</section>", start)]
    assert re.search(r'class="term"', hero)
    assert re.search(r"<button[^>]*>\s*Copy\s*</button>", hero, re.I)
    assert "navigator.clipboard" in page and ".select()" in page


def test_the_commands_work_exactly_as_printed_on_a_fresh_machine():
    # A newcomer's AI runs these as written: the clone names its folder and the next line enters it, before any ./securax.
    lines = [ln.strip() for ln in INSTALL.read_text("utf-8").splitlines()]
    at = lines.index("git clone https://github.com/{{REPO_SLUG}} securax")
    assert lines[at + 1] == "cd securax" and lines[at + 2] == "./securax go"


def test_the_ai_is_told_to_run_nothing_else_and_clone_only_this_repository():
    # A tampered or injected page must not steer the agent: the file fences what it may do (threat model hosted-apps).
    text = INSTALL.read_text("utf-8")
    assert "Run only the commands in this file" in text and "never a fork or a mirror" in text


def test_windows_is_sent_to_the_launcher_that_exists():
    text = INSTALL.read_text("utf-8")
    assert "START-HERE-Windows.bat" in text and (ROOT / "START-HERE-Windows.bat").exists()
