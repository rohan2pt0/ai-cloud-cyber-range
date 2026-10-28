"""Gate 1 — every command we TELL a user to run must be a real command.

A broken `docker run codercom/code-server … --install-extension X --bind-addr Y` shipped in doc 119 because no gate
ever executed the recipes in docs/: `--install-extension` makes code-server install-and-EXIT, so that line never served
the editor, and the user hit it on their real machine. Code is checked; prose was not. This closes the class: every
fenced `bash` block in docs/ must (1) pass `bash -n` (real shell syntax) and (2) carry none of the command shapes we have
already been burned by. It is static — it parses, it never runs anything — so it is safe to run in the normal pytest floor.

Angle-bracket placeholders a human fills in (`<domain>`, `<your checkout>`, `<short-name>`) are normalised away first:
they are documentation, not a shell redirection, and `bash -n` would otherwise read `<plan.json>` as `< plan.json`."""
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

FENCE = re.compile(r"^[ \t]*```(\w+)?[ \t]*$")
# A placeholder the reader replaces: `<` then a letter, no inner `<`/`>`, then `>`. This never matches a real redirection
# (`< file` has a space, `<<EOF` has another `<`, `<(…)` has a paren, `2>&1` is `>&`), so normalising it cannot hide a syntax bug.
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>]*>")

# Command shapes a real run proved wrong, each with why. A finding here is a doc telling the user to run something that
# does not do what the prose says. Add a row when a recipe burns someone; never relax one to make a doc pass.
BAD_SHAPES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"code-server\b(?=[^\n]*--install-extension)(?=[^\n]*--bind-addr)"),
     "code-server with --install-extension AND --bind-addr in one command: --install-extension installs and EXITS, "
     "so the editor never serves. Serve with a plain `code-server …`; install the extension in a separate command."),
]


def bash_blocks(md: pathlib.Path) -> list[tuple[int, str]]:
    """(1-based line of the opening fence, body) for every ```bash / ```sh / ```shell block in a doc."""
    lines, out, i = md.read_text("utf-8").splitlines(), [], 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if m and (m.group(1) or "").lower() in ("bash", "sh", "shell"):
            j, body = i + 1, []
            while j < len(lines) and not re.match(r"^[ \t]*```[ \t]*$", lines[j]):
                body.append(lines[j])
                j += 1
            out.append((i + 1, "\n".join(body)))
            i = j
        i += 1
    return out


def syntax_errors(body: str) -> str:
    """'' if the block is valid shell (after placeholder-normalising), else bash's own last error line."""
    norm = PLACEHOLDER.sub("PLACEHOLDER", body)
    p = subprocess.run(["bash", "-n"], input=norm, capture_output=True, text=True)
    return "" if p.returncode == 0 else (p.stderr.strip().splitlines() or ["?"])[-1]


def bad_shapes(body: str) -> list[str]:
    return [why for rx, why in BAD_SHAPES if rx.search(body)]


def test_every_bash_recipe_in_the_docs_is_valid_shell():
    bad = []
    for md in sorted(DOCS.rglob("*.md")):
        for ln, body in bash_blocks(md):
            err = syntax_errors(body)
            if err:
                bad.append(f"{md.relative_to(ROOT)}:{ln}  {err}")
    assert not bad, "Doc commands that are not valid shell:\n" + "\n".join(bad)


def test_no_doc_recipe_uses_a_command_shape_we_were_burned_by():
    bad = []
    for md in sorted(DOCS.rglob("*.md")):
        for ln, body in bash_blocks(md):
            for why in bad_shapes(body):
                bad.append(f"{md.relative_to(ROOT)}:{ln}  {why}")
    assert not bad, "Doc commands with a known-bad shape:\n" + "\n".join(bad)


def test_it_would_have_caught_the_code_server_recipe_that_shipped():
    # the exact shape doc 119 shipped before #179 — one command that installs an extension AND tries to serve
    broken = ('docker run -d --name securax-studio -p 127.0.0.1:8443:8080 '
              'codercom/code-server:4.143.1 --install-extension saoudrizwan.claude-dev --bind-addr 0.0.0.0:8080')
    assert bad_shapes(broken), "the known-bad screen must flag install-extension + bind-addr in one command"
    fixed = "docker run -d --name securax-studio -p 127.0.0.1:8443:8080 codercom/code-server:4.143.1"
    assert not bad_shapes(fixed), "a plain serve command must pass"


def test_the_syntax_check_catches_a_real_error_but_allows_placeholders():
    assert syntax_errors("for x in; do echo $x")              # unterminated — a real syntax error
    assert not syntax_errors("cd <your SecuRAX checkout>")     # a placeholder the reader fills in is fine
    assert not syntax_errors("git checkout -b feat/<name>")
