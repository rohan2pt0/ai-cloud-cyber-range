"""`./securax residency` and the lifecycle's cloud-region guard; plus the router property residency depends on (a local alias never falls back to a cloud one)."""
import importlib.util
import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("residency_cli", REPO / "governance" / "residency.py")
rc = importlib.util.module_from_spec(spec)
sys.modules["residency_cli"] = rc
spec.loader.exec_module(rc)


@pytest.fixture
def env(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text("LITELLM_MASTER_KEY=x\n")
    monkeypatch.setattr(rc, "ATTEST", tmp_path / "attest.json")
    for k in ("RESIDENCY_MODE", "RESIDENCY_POLICY_B64", "TF_VAR_region"):
        monkeypatch.delenv(k, raising=False)
    return p


def run(env, *a):
    return rc.main(["--env-file", str(env), *a])


def test_shipped_policies_are_valid_and_the_template_is_ignored_by_enable():
    for f in (REPO / "governance" / "residency").glob("*.json"):
        if f.name.endswith(".example.json"):
            continue
        assert rc.gw().problems(json.loads(f.read_text())) == [], f.name
    with pytest.raises(SystemExit):
        rc.load_template("TEMPLATE.example")


def test_enable_writes_a_policy_the_gateway_loads(env):
    assert run(env, "enable", "--jurisdiction", "IN") == 0
    e = rc.read_env(env)
    assert e["RESIDENCY_MODE"] == "enforce" and e["RESIDENCY_ACTION"] == "reroute"
    pol = rc.gw().Policy.from_env({k: e[k] for k in ("RESIDENCY_MODE", "RESIDENCY_ACTION", "RESIDENCY_POLICY_B64")})
    assert pol.data["jurisdiction"] == "IN" and pol.mode == "enforce"
    run(env, "disable")
    assert rc.read_env(env)["RESIDENCY_MODE"] == "off"


def test_enable_monitor_and_unknown_jurisdiction(env):
    run(env, "enable", "--jurisdiction", "in", "--monitor")
    assert rc.read_env(env)["RESIDENCY_MODE"] == "monitor"
    with pytest.raises(SystemExit):
        run(env, "enable", "--jurisdiction", "ZZ")


def test_check_shows_what_the_gateway_would_do(env, capsys):
    run(env, "enable", "--jurisdiction", "IN")
    capsys.readouterr()
    assert run(env, "check", "--finding", "AADHAAR", "--model", "bank-assistant") == 0
    assert "rerouted" in capsys.readouterr().out.lower()
    run(env, "enable", "--jurisdiction", "IN", "--action", "block")
    assert run(env, "check", "--finding", "AADHAAR", "--model", "bank-assistant") == 1


def test_status_warns_when_off_and_lists_every_router_alias(env, capsys):
    run(env, "status")
    out = capsys.readouterr().out
    assert "nothing stops regulated data" in out and "bank-assistant-local" in out and "global" in out


# -------------------------------------------------------------------------------------------------- cloud region guard
def test_guard_is_inactive_unless_enforced(env):
    assert rc.cloud_guard("aws", "us-east-1", rc.read_env(env)) == (True, "")


def test_region_must_be_allowed_and_the_cloud_attested(env):
    run(env, "enable", "--jurisdiction", "IN")
    e = rc.read_env(env)
    ok, msg = rc.cloud_guard("aws", "us-east-1", e)
    assert not ok and "not allowed" in msg and "ap-south-1" in msg
    ok, msg = rc.cloud_guard("aws", "ap-south-1", e)
    assert not ok and "attest" in msg                                       # right region, but no evidence recorded
    run(env, "attest", "aws", "--ref", "MeitY-CSP-123 / STQC audit 2026-09")
    assert rc.cloud_guard("aws", "ap-south-1", e) == (True, "")
    assert rc.cloud_guard("gcp", "asia-south1", e)[0] is False             # a different cloud needs its own evidence


def test_default_regions_of_the_shipped_genomes_pass_the_india_policy(env):
    run(env, "enable", "--jurisdiction", "IN")
    for cloud in ("aws", "gcp", "azure"):
        region = rc.default_region(cloud, REPO / "infra" / "terraform" / "lifecycle" / cloud)
        run(env, "attest", cloud, "--ref", "x")
        assert rc.cloud_guard(cloud, region, rc.read_env(env)) == (True, ""), (cloud, region)


def test_tf_var_overrides_the_default_region(env, monkeypatch):
    monkeypatch.setenv("TF_VAR_region", "eu-west-1")
    assert rc.default_region("aws", REPO / "infra" / "terraform" / "lifecycle" / "aws") == "eu-west-1"


def test_the_lifecycle_refuses_to_wake_a_stage_outside_policy(env, monkeypatch, capsys):
    spec2 = importlib.util.spec_from_file_location("lifecycle_mod", REPO / "lifecycle" / "lifecycle.py")
    sys.path.insert(0, str(REPO / "lifecycle"))
    lc = importlib.util.module_from_spec(spec2)
    sys.modules["lifecycle_mod"] = lc
    spec2.loader.exec_module(lc)
    run(env, "enable", "--jurisdiction", "IN")
    e = rc.read_env(env)
    for k in ("RESIDENCY_MODE", "RESIDENCY_ACTION", "RESIDENCY_POLICY_B64"):
        monkeypatch.setenv(k, e[k])
    monkeypatch.setenv("TF_VAR_region", "us-east-1")
    monkeypatch.setattr(lc, "cloud_name", lambda: "aws")
    assert lc.tf_run("tree", True, False, False, None) == 1
    assert "data-residency policy" in capsys.readouterr().out


# ----------------------------------------------------------------------------------- the router property residency relies on
def test_no_local_alias_ever_falls_back_to_a_cloud_alias():
    cat = json.loads((REPO / "plugins" / "catalog.json").read_text())
    gen_spec = importlib.util.spec_from_file_location("gen", REPO / "local" / "compose" / "gen_litellm_config.py")
    gen = importlib.util.module_from_spec(gen_spec)
    sys.modules["gen"] = gen
    gen_spec.loader.exec_module(gen)
    local_aliases = {p["alias"] for p in cat["providers"] if p.get("local") and p.get("alias")}
    assert "bank-assistant-local" in local_aliases
    cfg = gen.generate(cat, {"GEMINI_API_KEY": "k", "GROQ_API_KEY": "k", "OPENROUTER_API_KEY": "k"}, baseline=False)
    line = next(ln for ln in cfg.splitlines() if ln.strip().startswith("fallbacks:"))
    fallbacks = json.loads(line.split("fallbacks:", 1)[1])
    keys = {k for d in fallbacks for k in d}
    assert not (keys & local_aliases), f"a local alias falls back to something else: {keys & local_aliases}"
