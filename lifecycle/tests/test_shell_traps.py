"""A `[ test ] && action` as the LAST thing a command does makes it exit 1 whenever the test is false, though nothing failed:
`./securax start flows` reported failure that way while n8n ran fine. This finds that shape in the CLI, and proves it would have found
the original."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
# lines that end the block without running anything after the test: fi, done, }, esac, or a one-line `else …; fi` (the then-branch's
# last command still decides the result when the then-branch ran)
CLOSER = re.compile(r"^\s*((fi|done|\}|esac)\s*(;;)?|else\b.*;\s*fi\s*(;;)?)\s*$")


def traps(text: str) -> list[int]:
    lines, out = text.splitlines(), []
    for i, line in enumerate(lines):
        st = re.sub(r"^[\w|*\-]+\)\s+", "", line.split(" #")[0].strip())        # `pattern) [ … ] && … ;;` on one line
        if not re.match(r"^\[\[? .*\]\]? &&", st) or "||" in st:
            continue
        if st.endswith(";;"):
            out.append(i + 1)
            continue
        j = i + 1
        while j < len(lines) and (not lines[j].strip() or CLOSER.match(lines[j])):
            if lines[j].strip().endswith(";;"):
                break
            j += 1
        if j < len(lines) and (lines[j].strip().startswith(";;") or lines[j].strip().endswith(";;") and CLOSER.match(lines[j])):
            out.append(i + 1)
    return out


def test_no_command_ends_on_a_test_that_can_be_false():
    assert traps((ROOT / "securax").read_text("utf-8")) == []


def test_it_finds_the_shape_that_broke_start_flows():
    old = '''  start)
    for _s in $_svc; do
      if web_up "$_n"; then C "$_n is running"
        [ "$_n" = pass ] && { skv "$ENVF" PASSWORDS_ENABLED 1; }
      else C "still starting"; fi
    done
    ;;
  other) [ -n "$x" ] && echo y ;;
'''
    assert traps(old) == [4, 8]
    fixed = old.replace('[ "$_n" = pass ] && { skv "$ENVF" PASSWORDS_ENABLED 1; }', 'if [ "$_n" = pass ]; then skv "$ENVF" PASSWORDS_ENABLED 1; fi')
    assert traps(fixed) == [8]


def _run_guard(tmp_path, env_text: str) -> tuple[str, str]:
    """Run the CLI's own online_guard (cut from the securax file, with its helpers) against a temporary .env."""
    import subprocess
    src = (ROOT / "securax").read_text("utf-8")
    def pick(name):
        if name == "online_guard":
            return re.search(r"^online_guard\(\)\{.*?^\}$", src, re.M | re.S).group(0)
        return re.search(rf"^{name}\(\).*$", src, re.M).group(0)                     # a one-line helper
    (tmp_path / "local" / "compose").mkdir(parents=True)
    envf = tmp_path / "local" / "compose" / ".env"
    envf.write_text(env_text)
    script = "\n".join([f'ROOT="{tmp_path}"', 'C(){ printf "%s\\n" "$*"; }', pick("ev"),
                        re.search(r"^skv\(\)\{.*?\n(?=\S)", src, re.M | re.S).group(0), pick("online_guard"), "online_guard"])
    (tmp_path / "guard.sh").write_text(script)
    p = subprocess.run(["bash", str(tmp_path / "guard.sh")], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout, envf.read_text()


def test_chat_stops_trusting_the_signin_header_once_ports_leave_loopback(tmp_path):
    out, env = _run_guard(tmp_path, "BIND_HOST=0.0.0.0\nOWUI_TRUSTED_EMAIL_HEADER=Cf-Access-Authenticated-User-Email\n")
    assert "could be forged" in out and "OWUI_TRUSTED_EMAIL_HEADER=\n" in env


def test_on_loopback_the_signin_header_stays_trusted(tmp_path):
    out, env = _run_guard(tmp_path / "b", "BIND_HOST=127.0.0.1\nOWUI_TRUSTED_EMAIL_HEADER=Cf-Access-Authenticated-User-Email\n")
    assert out == "" and "OWUI_TRUSTED_EMAIL_HEADER=Cf-Access-Authenticated-User-Email" in env
