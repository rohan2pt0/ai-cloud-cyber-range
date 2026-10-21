"""`./securax up --safe` (doc 82): when even a working version is short of memory, only the AI gateway, its router and the
Command Center start; nothing is remembered, no add-on comes back, and a safe start is never recorded as a working version."""
import pathlib
import subprocess

CLI = (pathlib.Path(__file__).resolve().parents[2] / "securax").read_text("utf-8")
LINES = CLI.splitlines()


def services(*args: str) -> str:
    i = next(n for n, line in enumerate(LINES) if line.strip().startswith('SAFE=0; if [ "${2:-}" = "--safe" ]'))
    script = 'C(){ :; }; SVCS="lite-or-empty"\n' + "\n".join(LINES[i:i + 2]) + '\necho "$SAFE|$SVCS"'
    return subprocess.run(["bash", "-c", script, "securax", *args], capture_output=True, text=True, check=True).stdout.strip()


def test_safe_starts_only_the_gateway_and_the_command_center():
    assert services("up", "--safe") == "1|gateway litellm guiding-map"
    assert services("up") == "0|lite-or-empty" and services("up", "--lite") == "0|lite-or-empty"


def test_safe_brings_back_no_add_on_and_records_no_working_version():
    for guarded in ('[ "$SAFE" = 1 ] || case " $(ev SECURAX_OPTIONAL) " in *" passwords "*)',
                    '[ "$SAFE" = 1 ] || case " $(ev SECURAX_OPTIONAL) " in *" online "*)',
                    '[ "$SAFE" = 1 ] || python3 "$ROOT/governance/recovery.py" --record up',
                    '[ "$SAFE" = 1 ] && SIDE="gateway-tls litellm-tls"'):
        assert guarded in CLI, guarded
    assert "up --safe" in CLI[CLI.index("THE 20% YOU USE 80% OF THE TIME"):]          # in ./securax help
