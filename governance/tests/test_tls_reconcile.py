"""`./securax tls reconcile` (doc 40): COMPOSE_FILE must always define exactly the services `up` asks for.

The real incident this guards: `tls on` run after `tls internal on` left TLS_INTERNAL=1 while COMPOSE_FILE dropped
tls-internal.yml, so `up gateway-tls` died with "no such service" and even rollback could not start the estate. The fix
is twofold — `tls on` now preserves internal mode, and every `up` reconciles first — and both are asserted here.
"""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load(tmp_env):
    spec = importlib.util.spec_from_file_location("securax_tls_reconcile_t", ROOT / "governance" / "tls.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ENVF = tmp_env                      # point read_env/set_env at a throwaway .env
    mod.write_private = lambda p, d: p.write_text(d, "utf-8")   # avoid chmod/dir assumptions in the test
    return mod


def _env(tmp_path, **kv):
    p = tmp_path / ".env"
    p.write_text("".join(f"{k}={v}\n" for k, v in kv.items()), "utf-8")
    return p


def test_reconcile_adds_the_missing_internal_overlay(tmp_path):
    # the exact broken state from the field: internal flag on, but its compose file missing -> up would fail.
    env = _env(tmp_path, TLS_INTERNAL="1", COMPOSE_FILE="docker-compose.yml:tls.yml")
    tls = _load(env)
    assert tls.cmd_reconcile() == 0
    assert tls.read_env()["COMPOSE_FILE"] == "docker-compose.yml:tls.yml:tls-internal.yml"


def test_reconcile_removes_the_overlay_when_internal_is_off(tmp_path):
    env = _env(tmp_path, COMPOSE_FILE="docker-compose.yml:tls.yml:tls-internal.yml")   # no TLS_INTERNAL
    tls = _load(env)
    assert tls.cmd_reconcile() == 0
    assert tls.read_env()["COMPOSE_FILE"] == "docker-compose.yml:tls.yml"


def test_reconcile_preserves_other_overlays_and_order(tmp_path):
    env = _env(tmp_path, TLS_INTERNAL="1", COMPOSE_FILE="docker-compose.yml:tls.yml:tls-move.yml")
    tls = _load(env)
    tls.cmd_reconcile()
    # tls-internal.yml goes right after tls.yml; the move overlay is kept.
    assert tls.read_env()["COMPOSE_FILE"] == "docker-compose.yml:tls.yml:tls-internal.yml:tls-move.yml"


def test_reconcile_is_a_noop_when_edge_is_off_or_already_consistent(tmp_path):
    off = _load(_env(tmp_path, COMPOSE_FILE=""))
    assert off.cmd_reconcile() == 0 and off.read_env().get("COMPOSE_FILE", "") == ""
    ok = _load(_env(tmp_path, TLS_INTERNAL="1", COMPOSE_FILE="docker-compose.yml:tls.yml:tls-internal.yml"))
    ok.cmd_reconcile()
    assert ok.read_env()["COMPOSE_FILE"] == "docker-compose.yml:tls.yml:tls-internal.yml"


def test_tls_on_preserves_internal_in_the_compose_file():
    # Fix A at the source: cmd_on must choose the INTERNAL compose set when TLS_INTERNAL is already 1.
    src = (ROOT / "governance" / "tls.py").read_text("utf-8")
    assert 'TLS_COMPOSE_INTERNAL if read_env().get("TLS_INTERNAL") == "1" else TLS_COMPOSE' in src


def test_up_reconciles_before_starting():
    # Fix B wiring: the start path heals the config before composing.
    cli = (ROOT / "securax").read_text("utf-8")
    assert 'governance/tls.py" reconcile' in cli
    # Fix C: a plain-mode last resort so the user is never left with nothing.
    assert "Fallback 3" in cli and "COMPOSE_FILE=docker-compose.yml docker compose --profile ai up -d gateway" in cli
