"""`./securax up --seed` (doc 86): a fallback node on a small cloud server starts only the AI gateway, its router, the
home screen and estate-sync — chosen by itself on a machine under 2500 MB — and `install.sh --server` writes
`SECURAX_SEED=1` on such a machine."""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
CLI = (ROOT / "securax").read_text("utf-8")
LINES = CLI.splitlines()


def _fn(name):
    start = next(n for n, line in enumerate(LINES) if line.strip().startswith(name + "(){"))
    if LINES[start].rstrip().endswith("}"):
        return [LINES[start]]
    end = next(n for n in range(start + 1, len(LINES)) if LINES[n].strip() == "}")
    return LINES[start:end + 1]


def services(*args: str, mem_mb=None, root=None) -> str:
    i = next(n for n, line in enumerate(LINES) if line.strip().startswith('SEED=0; if [ "${2:-}" = "--seed" ]'))
    script = (
        'C(){ :; }; SAFE=0; SVCS="lite-or-empty"\n'
        + "\n".join(_fn("ev")) + "\n"
        + "\n".join(_fn("docker_res")) + "\n"
        + "\n".join(LINES[i:i + 3]) + '\necho "$SEED|$SVCS"'
    )
    env = {"PATH": "/usr/bin:/bin"}
    if mem_mb is not None:
        env["SECURAX_SIM_MEM_MB"] = str(mem_mb)
    if root is not None:
        env["ROOT"] = str(root)
    return subprocess.run(["bash", "-c", script, "securax", *args], capture_output=True, text=True,
                          check=True, env=env).stdout.strip()


def test_a_small_machine_picks_seed_and_starts_only_the_gateway_router_home_and_sync():
    assert services("up", mem_mb=1000) == "1|gateway litellm guiding-map estate-sync"
    assert services("up", mem_mb=16000) == "0|lite-or-empty"


def test_up_seed_forces_it_and_the_env_overrides_it(tmp_path):
    assert services("up", "--seed") == "1|gateway litellm guiding-map estate-sync"
    (tmp_path / "local" / "compose").mkdir(parents=True)
    (tmp_path / "local" / "compose" / ".env").write_text("SECURAX_SEED=1\n")
    assert services("up", mem_mb=16000, root=tmp_path) == "1|gateway litellm guiding-map estate-sync"


def test_install_server_writes_seed_on_a_small_machine():
    install = (ROOT / "install.sh").read_text("utf-8")
    server = install[install.index('if [ "$SERVER" = 1 ]; then'):]
    assert "SECURAX_SEED=1" in server
    assert "-lt 2500" in server


def test_seed_is_named_in_the_help():
    assert "up --seed" in CLI[CLI.index("THE 20% YOU USE 80% OF THE TIME"):]


def test_seed_keeps_the_local_model_and_chat_off_under_internal_tls():
    assert '[ "$SEED" = 1 ] && SIDE="gateway-tls litellm-tls estate-sync-tls"' in CLI
