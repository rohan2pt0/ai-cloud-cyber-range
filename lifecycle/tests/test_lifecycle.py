"""The lifecycle genome: stages are dormant by default, hibernation keeps data, and every definition is well-formed.
(Behaviour with real containers is proven by the sandbox journeys; the Terraform dormancy logic by infra/terraform/lifecycle/prove.py.)"""
import importlib.util
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess

import pytest
import yaml

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
spec = importlib.util.spec_from_file_location("lc", REPO / "lifecycle" / "lifecycle.py")
lc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lc)
STAGES = json.loads((REPO / "lifecycle" / "stages.json").read_text())
ORGANS = json.loads((REPO / "lifecycle" / "organs.json").read_text())["organs"]
COMPOSE = REPO / "local" / "compose"


# ───────────────────────────── the ladder ─────────────────────────────
def test_ladder_is_complete_and_ordered():
    ids = [s["id"] for s in STAGES["stages"]]
    assert ids == ["seed", "sprout", "burrow", "tree", "canopy", "forest"]
    assert [s["phase"] for s in STAGES["stages"]] == [0, 1, 2, 2, 3, 4]       # the burrow is stage 2a: own hardware, before the cloud tree
    assert STAGES["aliases"] == {"crawl": "seed", "walk": "sprout", "run-": "burrow", "run": "tree", "run+": "canopy", "fly": "forest"}
    for s in STAGES["stages"]:
        assert s["wake"].startswith("./securax") and s["sleep"].startswith("./securax"), s["id"]
        assert s["dormant_cost"] and s["awake_cost"] and s["what"] and s["where"]
    nxt = {s["id"]: s["grows_into"] for s in STAGES["stages"]}
    assert nxt == {"seed": "sprout", "sprout": "burrow", "burrow": "tree", "tree": "canopy", "canopy": "forest", "forest": None}


def test_aliases_resolve_and_unknown_stage_is_refused():
    assert lc.resolve_stage("crawl") == "seed" and lc.resolve_stage("FLY") == "forest" and lc.resolve_stage("run+") == "canopy"
    with pytest.raises(SystemExit):
        lc.resolve_stage("jungle")


def test_cloud_stages_have_a_genome_for_every_supported_cloud():
    for cloud in ("aws", "gcp", "azure"):
        root = REPO / "infra" / "terraform" / "lifecycle" / cloud
        assert (root / "main.tf").exists() and (root / "variables.tf").exists(), cloud
        txt = (root / "variables.tf").read_text()
        # THE hibernation switch exists, defaults to dormant, and a stage selector exists
        assert re.search(r'variable "awake"\s*\{[^}]*default\s*=\s*false', txt, re.S), f"{cloud}: awake must default to false"
        assert 'variable "stage"' in txt


def test_terraform_modules_never_carry_their_own_provider():
    # A module with its own provider block cannot be used with count/for_each — which is exactly how dormancy is expressed.
    for tf in (REPO / "infra" / "terraform").rglob("*.tf"):
        if "/modules/" in str(tf):
            assert not re.search(r'^\s*provider\s+"', tf.read_text(), re.M), f"{tf} must not define a provider block"


def test_every_compute_module_is_called_behind_the_dormancy_switch():
    for cloud, mods in {"aws": ["tree_aws", "canopy_aws"], "gcp": ["canopy"], "azure": ["canopy"]}.items():
        txt = (REPO / "infra" / "terraform" / "lifecycle" / cloud / "main.tf").read_text()
        for m in mods:
            block = re.search(rf'module "{m}" \{{(.*?)\n\}}', txt, re.S).group(1)
            assert re.search(r"count\s*=.*awake", block), f"{cloud}/{m}: compute must be gated on the awake switch"


# ───────────────────────────── sprout: dormant by default ─────────────────────────────
def compose_services(*files, profile=None):
    argv = ["docker", "compose"]
    for f in files:
        argv += ["-f", str(COMPOSE / f)]
    argv += ["--env-file", str(COMPOSE / ".env.example")]
    if profile:
        argv += ["--profile", profile]
    env = {**os.environ, "SECURAX_SPROUT_DIR": "/tmp/x", "KEYCLOAK_DB_PASSWORD": "a", "KEYCLOAK_ADMIN_PASSWORD": "b"}
    p = subprocess.run(argv + ["config", "--services"], capture_output=True, text=True, env=env)
    assert p.returncode == 0, p.stderr
    return set(p.stdout.split())


@pytest.mark.skipif(not shutil.which("docker"), reason="docker CLI not installed")
def test_sprout_is_dormant_unless_explicitly_grown():
    sprout = set(lc.SPROUT_SERVICES)
    # The normal start-up path never sees them…
    assert not (compose_services("docker-compose.yml", profile="ai") & sprout)
    assert not (compose_services("docker-compose.yml", "stage-sprout.yml", profile="ai") & sprout)      # even with the file loaded
    # …only the sprout profile does.
    assert compose_services("docker-compose.yml", "stage-sprout.yml", profile="sprout") >= sprout


def test_sprout_services_are_pinned_hardened_and_local_only():
    doc = yaml.safe_load((COMPOSE / "stage-sprout.yml").read_text())
    assert set(doc["services"]) == set(lc.SPROUT_SERVICES)
    for name, svc in doc["services"].items():
        assert svc["profiles"] == ["sprout"], name
        tag = svc["image"].rsplit(":", 1)[-1]
        assert tag not in ("latest", "main", "master"), f"{name}: image must be pinned"
        assert "no-new-privileges:true" in svc["security_opt"], name
        assert svc.get("mem_limit"), f"{name}: needs a memory cap (elasticity within limits)"
        for port in svc.get("ports", []):
            assert "BIND_HOST:-127.0.0.1" in port, f"{name}: ports must default to localhost-only"
    assert set(doc["volumes"]) == set(lc.SPROUT_VOLUMES)


def test_openbao_is_not_given_its_config_twice():
    # Found by running it: the image entrypoint already loads /openbao/config, so an explicit -config flag defines the
    # listener twice and the second bind dies with "address already in use".
    svc = yaml.safe_load((COMPOSE / "stage-sprout.yml").read_text())["services"]["openbao"]
    assert svc["command"] == ["server"]


# ───────────────────────────── generated config / secrets ─────────────────────────────
@pytest.fixture
def sprout_home(tmp_path, monkeypatch):
    monkeypatch.setattr(lc, "HOME_DIR", str(tmp_path))
    monkeypatch.setattr(lc, "SPROUT_DIR", str(tmp_path / "sprout"))
    monkeypatch.setattr(lc, "run", lambda *a, **k: (0, ""))          # no docker volumes
    return tmp_path


def test_sprout_prepare_creates_private_secrets_once(sprout_home):
    lc.sprout_prepare()
    env_file = sprout_home / "sprout" / ".env.sprout"
    first = lc.read_env_file(str(env_file))
    assert {"KEYCLOAK_DB_PASSWORD", "KEYCLOAK_ADMIN_PASSWORD", "S3_ACCESS_KEY", "S3_SECRET_KEY"} <= set(first)
    assert all(len(v) >= 12 for v in first.values())
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600 and stat.S_IMODE((sprout_home / "sprout" / "s3.json").stat().st_mode) == 0o600
    # the Alertmanager image runs unprivileged and must be able to read its (non-secret) config
    assert stat.S_IMODE((sprout_home / "sprout" / "alertmanager.yml").stat().st_mode) == 0o644
    lc.sprout_prepare()
    assert lc.read_env_file(str(env_file)) == first, "re-running must never rotate a password under a running database"
    s3 = json.loads((sprout_home / "sprout" / "s3.json").read_text())
    assert s3["identities"][0]["credentials"][0]["accessKey"] == first["S3_ACCESS_KEY"]


def test_lost_secrets_with_surviving_data_is_refused_not_silently_broken(sprout_home, monkeypatch):
    monkeypatch.setattr(lc, "run", lambda *a, **k: (0, "vulnbank-range_keycloak_db\n"))
    with pytest.raises(SystemExit) as e:
        lc.sprout_prepare()
    assert "backup" in str(e.value) and "prune" in str(e.value)


def test_alertmanager_config_only_sends_when_you_configured_a_webhook():
    assert "webhook_configs" not in lc.alertmanager_yaml("")
    y = yaml.safe_load(lc.alertmanager_yaml("https://ntfy.example/topic"))
    assert y["receivers"][0]["webhook_configs"][0]["url"] == "https://ntfy.example/topic"


# ───────────────────────────── organs ─────────────────────────────
def test_organs_are_pinned_to_an_exact_ref_and_bound_to_localhost():
    for name, o in ORGANS.items():
        assert re.fullmatch(r"[0-9a-f]{40}|v\d+\.\d+\.\d+", o["ref"]), f"{name}: pin a tag or full commit, never a branch"
        assert o["repo"].startswith("https://github.com/")
        for svc, ports in o["override"].items():
            for p in ports:
                host_port = p.split(":")[-2]
                # agent enrolment ports must be reachable by agents; every admin/API/UI port is localhost-only
                assert p.startswith("127.0.0.1:") or host_port in ("1514", "1515"), f"{name}/{svc}: {p} would expose an admin port"
    assert len({p.split(":")[1] for o in ORGANS.values() for ports in o["override"].values() for p in ports if p.startswith("127.0.0.1")}) \
        == sum(1 for o in ORGANS.values() for ports in o["override"].values() for p in ports if p.startswith("127.0.0.1")), "host ports must not clash across organs"


def test_prepare_env_generates_secrets_keeps_existing_values(tmp_path):
    (tmp_path / "template.env").write_text("BASE_URL=http://localhost\n# ADMIN_PASSWORD=\nMYSQL_PASSWORD=\nOTHER=1\n")
    spec = {"file": ".env", "copy_from": "template.env", "set": {"BASE_URL": "https://localhost:8445", "ADMIN_PASSWORD": "@secret", "MYSQL_PASSWORD": "@secret", "NEW_KEY": "@secret"}}
    lc.prepare_env(str(tmp_path), spec)
    env = lc.read_env_file(str(tmp_path / ".env"))
    assert env["BASE_URL"] == "https://localhost:8445" and env["OTHER"] == "1"
    assert len(env["ADMIN_PASSWORD"]) >= 16 and len(env["MYSQL_PASSWORD"]) >= 16 and len(env["NEW_KEY"]) >= 16
    assert stat.S_IMODE((tmp_path / ".env").stat().st_mode) == 0o600
    lc.prepare_env(str(tmp_path), spec)
    assert lc.read_env_file(str(tmp_path / ".env")) == env, "second run must not rotate secrets"


def test_override_yaml_replaces_published_ports():
    y = yaml.compose = lc.override_yaml({"web": ["127.0.0.1:8443:5601"]})
    assert "ports: !override" in y and '"127.0.0.1:8443:5601"' in y


def test_organ_fetch_is_idempotent_and_pins_to_the_given_ref(tmp_path, monkeypatch):
    # Uses a local stand-in repo: proves germination mechanics (fetch exact ref → checkout) without the network.
    src = tmp_path / "src"
    src.mkdir()
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    sh = lambda *a, cwd=src: subprocess.run(["git", *a], cwd=cwd, env=env, check=True, capture_output=True, text=True)  # noqa: E731
    sh("init", "-q", "-b", "main")
    (src / "docker-compose.yml").write_text("services: {}\n")
    sh("add", "-A")
    sh("commit", "-qm", "one")
    sha1 = sh("rev-parse", "HEAD").stdout.strip()
    (src / "docker-compose.yml").write_text("services: {x: {image: busybox}}\n")
    sh("commit", "-qam", "two")
    monkeypatch.setattr(lc, "ORGANS_DIR", str(tmp_path / "organs"))
    monkeypatch.setenv("SECURAX_ORGAN_OVERRIDE", json.dumps({"wazuh": {"repo": str(src), "ref": sha1, "dir": "."}}))
    d = lc.organ_fetch("wazuh")
    assert (pathlib.Path(d) / "docker-compose.yml").read_text() == "services: {}\n", "must check out the PINNED commit, not the branch tip"
    assert lc.organ_fetch("wazuh") == d                                   # idempotent


# ───────────────────────────── gitops / tenants ─────────────────────────────
def test_every_argo_application_points_at_something_that_exists():
    for f in (REPO / "gitops").rglob("*.yaml"):
        if "charts" in f.parts or "templates" in f.parts:
            continue
        for doc in yaml.safe_load_all(f.read_text()):
            if not doc or doc.get("kind") not in ("Application", "ApplicationSet"):
                continue
            spec_ = doc["spec"]
            srcs = [spec_["source"]] if "source" in spec_ else [spec_["template"]["spec"]["source"]]
            for src in srcs:
                if "chart" in src:
                    assert src["repoURL"].startswith("https://") and src["targetRevision"], f"{f}: chart needs a version range"
                else:
                    assert (REPO / src["path"]).exists(), f"{f}: path {src['path']} does not exist"


def test_helm_charts_are_pinned_to_a_range_never_to_head():
    for f in (REPO / "gitops" / "platform").glob("*.yaml"):
        doc = yaml.safe_load(f.read_text())
        src = doc["spec"]["source"]
        if "chart" in src:
            assert src["targetRevision"] not in ("", "HEAD", "latest", "main"), f.name


def test_core_router_manifest_matches_the_shipped_baseline():
    p = subprocess.run(["python3", str(REPO / "lifecycle" / "render_core.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_tenant_files_round_trip_into_the_terraform_genome(tmp_path, monkeypatch):
    monkeypatch.setattr(lc, "TENANT_DIR", str(tmp_path / "tenants"))
    monkeypatch.setattr(lc, "TF_DIR", str(tmp_path / "tf"))
    (tmp_path / "tf" / "aws").mkdir(parents=True)
    monkeypatch.setenv("SECURAX_CLOUD", "aws")
    ns = type("A", (), {"action": "add", "id": "acme", "name": 'ACME "Bank"', "tier": "medium", "group": ""})
    assert lc.cmd_tenant(ns) == 0
    t = lc.list_tenants()["acme"]
    assert t["tier"] == "medium" and t["oidcGroup"] == "acme-staff" and "ACME" in t["name"]
    tfv = json.loads((tmp_path / "tf" / "aws" / "tenants.auto.tfvars.json").read_text())
    assert tfv == {"tenants": {"acme": {}}}
    with pytest.raises(SystemExit):
        lc.cmd_tenant(ns)                                                 # duplicate
    bad = type("A", (), {"action": "add", "id": "Bad_Id", "name": "", "tier": "small", "group": ""})
    with pytest.raises(SystemExit):
        lc.cmd_tenant(bad)
    rm = type("A", (), {"action": "remove", "id": "acme", "name": "", "tier": "small", "group": ""})
    assert lc.cmd_tenant(rm) == 0 and not lc.list_tenants()


@pytest.mark.skipif(not shutil.which("helm"), reason="helm not installed")
def test_tenant_chart_renders_every_tier_and_refuses_unknown_tiers():
    chart = str(REPO / "gitops" / "charts" / "tenant")
    for tier in ("small", "medium", "large"):
        p = subprocess.run(["helm", "template", "t", chart, "--set", "tenant.id=acme", "--set", f"tier={tier}", "--set", "oidcGroup=acme-staff"],
                           capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        docs = [d for d in yaml.safe_load_all(p.stdout) if d]
        kinds = {d["kind"] for d in docs}
        assert {"Namespace", "ResourceQuota", "LimitRange", "NetworkPolicy", "Deployment", "Service", "PodDisruptionBudget",
                "HorizontalPodAutoscaler", "Role", "RoleBinding", "ServiceMonitor"} <= kinds
        ns = next(d for d in docs if d["kind"] == "Namespace")
        assert ns["metadata"]["name"] == "t-acme" and ns["metadata"]["labels"]["pod-security.kubernetes.io/enforce"] == "restricted"
        np_ = [d for d in docs if d["kind"] == "NetworkPolicy"]
        assert any(d["metadata"]["name"] == "default-deny-all" and d["spec"]["policyTypes"] == ["Ingress", "Egress"] for d in np_)
    bad = subprocess.run(["helm", "template", "t", chart, "--set", "tier=huge"], capture_output=True, text=True)
    assert bad.returncode != 0 and "tier must be" in bad.stderr


# ───────────────────────────── the burrow (own hardware) ─────────────────────────────
bspec = importlib.util.spec_from_file_location("bw", REPO / "lifecycle" / "burrow.py")
bw = importlib.util.module_from_spec(bspec)
bspec.loader.exec_module(bw)
BURROW = json.loads((REPO / "lifecycle" / "burrow.json").read_text())


def test_burrow_twin_is_one_server_and_exactly_one_gpu_node():
    nodes = BURROW["twin"]["nodes"]
    assert [n["role"] for n in nodes].count("server") == 1 and len(nodes) == 3
    assert [n["name"] for n in nodes if n.get("gpu")] == ["agent2"]
    assert "--cluster-init" in BURROW["server_args"], "embedded etcd from day one: one server grows to three without a rebuild"


def test_twin_and_hardware_use_the_same_k3s_flags():
    for role in ("server", "agent"):
        for flag in bw.k3s_flags(role, gpu=False):
            assert flag in bw.install_script(role, "n1", join_url="https://10.0.0.1:6443" if role == "agent" else "", tok="t")
    assert bw.k3s_flags("server", gpu=True)[-2:] == ["--node-label", BURROW["gpu_label"]]
    joined = bw.k3s_flags("server", gpu=False, join_url="https://10.0.0.1:6443")
    assert "--cluster-init" not in joined and joined[-2:] == ["--server", "https://10.0.0.1:6443"], "a 2nd/3rd server joins; it does not start a new cluster"


def test_spore_is_valid_bash_and_cloud_init_yaml(tmp_path):
    script = bw.install_script("server", "burrow1", gpu=True, ups=True, gitops=True, tok="TOKEN123")
    f = tmp_path / "s.sh"
    f.write_text(script)
    assert subprocess.run(["bash", "-n", str(f)], capture_output=True).returncode == 0
    assert "securax-power-hibernate" in script and "INSTALL_K3S_VERSION=" in script and "argocd" in script.lower()
    doc = yaml.safe_load(bw.cloud_init(script, "burrow1"))
    assert doc["hostname"] == "burrow1" and doc["write_files"][0]["content"].startswith("#!/usr/bin/env bash")


def test_agent_needs_a_server_to_join_and_unknown_roles_are_refused():
    with pytest.raises(ValueError):
        bw.install_script("agent", "a1")
    with pytest.raises(ValueError):
        bw.install_script("queen", "q")
    assert "K3S_URL=https://10.0.0.5:6443" in bw.install_script("agent", "a1", join_url="https://10.0.0.5:6443", tok="t")


def test_power_reflex_is_valid_posix_sh_and_never_drains_itself_twice(tmp_path):
    hook = bw.power_hook()
    f = tmp_path / "h.sh"
    f.write_text(hook)
    assert subprocess.run(["sh", "-n", str(f)], capture_output=True).returncode == 0
    assert "etcd-snapshot save" in hook and "drain" in hook and 'grep -vx "$ME"' in hook, "other nodes first, then itself, then snapshot"
    assert "SECURAX_POWER_FINAL" in hook, "the final stop is overridable so the twin can rehearse it without killing itself"


def test_join_token_is_random_stable_and_owner_only(tmp_path, monkeypatch):
    monkeypatch.setattr(bw, "BURROW_DIR", str(tmp_path / "burrow"))
    t1, t2 = bw.token(), bw.token()
    assert t1 == t2 and len(t1) >= 32
    assert (os.stat(tmp_path / "burrow" / "token").st_mode & 0o077) == 0
