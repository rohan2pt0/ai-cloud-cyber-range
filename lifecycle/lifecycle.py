#!/usr/bin/env python3
"""SecuRAX lifecycle engine — grow the estate from a dormant seed to a forest, and put it back to sleep.

Nature's own pattern, used deliberately:
  * the GENOME (this repo: compose files, Terraform, GitOps) already contains every stage, fully defined;
  * everything above the seed is DORMANT: no process, no bill — only a seed bank (vault, keys, data disks);
  * GROW germinates one stage from the genome; HIBERNATE puts it to sleep and KEEPS its data; waking restores it;
  * PRUNE (apoptosis) is the only destructive verb and always asks for a typed confirmation.

Cloud stages never spend money by accident: without --apply they only run `terraform plan`.

Standard library only (it must run on a fresh Ubuntu/WSL). Invoked by ./securax; also usable directly:
    python3 lifecycle/lifecycle.py stages | soil <stage> | grow <stage> | hibernate <stage> | prune <stage> | scale <stage> <size> | rhythm on|off|status
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SECURAX_ROOT") or os.path.abspath(os.path.join(HERE, ".."))
COMPOSE_DIR = os.path.join(ROOT, "local", "compose")
TF_DIR = os.path.join(ROOT, "infra", "terraform", "lifecycle")
HOME_DIR = os.environ.get("SECURAX_HOME_DIR") or os.path.join(os.path.expanduser("~"), ".securax")
SPROUT_DIR = os.path.join(HOME_DIR, "sprout")
ORGANS_DIR = os.path.join(HOME_DIR, "organs")
SPROUT_SERVICES = ["keycloak-db", "keycloak", "openbao", "seaweedfs", "prometheus", "alertmanager"]
SPROUT_VOLUMES = ["keycloak_db", "openbao_data", "seaweed_data", "prometheus_data", "alertmanager_data"]
PROJECT = "vulnbank-range"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adrange as rng  # noqa: E402  (the dormant Active Directory practice lab, wrapped around GOAD)
import burrow as bw  # noqa: E402  (stage 2a: own hardware, rehearsed on a Docker twin)

MIN_COMPOSE = (2, 24)  # `ports: !override` (used for organ port remapping) needs Compose 2.24+


# ───────────────────────────────────────────── helpers ─────────────────────────────────────────────
def say(msg: str = "") -> None:
    print(msg, flush=True)


def head(msg: str) -> None:
    print(f"\033[1;36m{msg}\033[0m", flush=True)


def load_json(name: str) -> dict:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


def stages() -> dict[str, dict]:
    data = load_json("stages.json")
    return {s["id"]: s for s in data["stages"]}


def resolve_stage(name: str) -> str:
    data = load_json("stages.json")
    name = name.lower()
    name = data["aliases"].get(name, name)
    if name not in {s["id"] for s in data["stages"]}:
        valid = ", ".join(s["id"] for s in data["stages"])
        raise SystemExit(f"unknown stage '{name}'. Stages: {valid}  (aliases: crawl walk run run+ fly)")
    return name


def run(argv: list[str], cwd: str | None = None, env: dict | None = None, capture: bool = False, timeout: int | None = None) -> tuple[int, str]:
    e = {**os.environ, **(env or {})}
    try:
        p = subprocess.run(argv, cwd=cwd, env=e, text=True, timeout=timeout,
                           stdout=subprocess.PIPE if capture else None, stderr=subprocess.STDOUT if capture else None)
    except FileNotFoundError:
        return 127, f"{argv[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, "timed out"
    return p.returncode, (p.stdout or "") if capture else ""


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def read_env_file(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def write_private(path: str, text: str, mode: int = 0o600) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.chmod(path, mode)


def new_secret(n: int = 24) -> str:
    return secrets.token_urlsafe(n)


def docker_resources() -> tuple[int, int]:
    """(memory MB, CPUs) as Docker sees them (the real cap under WSL2/Docker Desktop)."""
    sim = os.environ.get("SECURAX_SIM_MEM_MB")
    if sim:
        return int(sim), int(os.environ.get("SECURAX_SIM_CPUS", "4"))
    rc, out = run(["docker", "info", "--format", "{{.MemTotal}} {{.NCPU}}"], capture=True, timeout=15)
    try:
        m, c = out.split()
        return int(m) // (1024 * 1024), int(c)
    except ValueError:
        return 0, 0


def free_disk_gb(path: str) -> int:
    try:
        p = path
        while not os.path.exists(p):
            p = os.path.dirname(p) or "/"
        return shutil.disk_usage(p).free // (1024 ** 3)
    except OSError:
        return 0


def compose_version() -> tuple[int, int]:
    rc, out = run(["docker", "compose", "version", "--short"], capture=True, timeout=15)
    m = re.search(r"(\d+)\.(\d+)", out or "")
    return (int(m.group(1)), int(m.group(2))) if (rc == 0 and m) else (0, 0)


def confirm(prompt: str, yes: bool, typed: str | None = None) -> bool:
    if yes and typed is None:
        return True
    if not sys.stdin.isatty() and not os.path.exists("/dev/tty"):
        return False
    try:
        tty = open("/dev/tty") if not sys.stdin.isatty() else sys.stdin
        say(prompt + (f"  Type  {typed}  to continue: " if typed else " [y/N]: "))
        ans = tty.readline().strip()
    except OSError:
        return False
    return ans == typed if typed else ans.lower().startswith("y")


# ───────────────────────────────────────────── sprout (phase 1) ─────────────────────────────────────────────
def sprout_env_file() -> str:
    return os.path.join(SPROUT_DIR, ".env.sprout")


def sprout_compose(*args: str) -> list[str]:
    """`docker compose` pointed at the main file + the dormant-by-default sprout stage file."""
    argv = ["docker", "compose", "-f", "docker-compose.yml", "-f", "stage-sprout.yml"]
    if os.path.exists(os.path.join(COMPOSE_DIR, ".env")):
        argv += ["--env-file", ".env"]
    argv += ["--env-file", sprout_env_file(), "--profile", "sprout", *args]
    return argv


def sprout_env() -> dict[str, str]:
    return {"SECURAX_SPROUT_DIR": SPROUT_DIR, "SECURAX_VERSION": open(os.path.join(ROOT, "VERSION")).read().strip() if os.path.exists(os.path.join(ROOT, "VERSION")) else "dev"}


def alertmanager_yaml(webhook: str) -> str:
    receivers = "receivers:\n  - name: default\n"
    if webhook:
        receivers += f"    webhook_configs:\n      - url: '{webhook}'\n        send_resolved: true\n"
    return ("route:\n  receiver: default\n  group_by: ['alertname']\n  group_wait: 30s\n  group_interval: 5m\n  repeat_interval: 4h\n"
            + receivers)


def s3_config_json(access: str, secret: str) -> str:
    return json.dumps({"identities": [{"name": "securax", "credentials": [{"accessKey": access, "secretKey": secret}],
                                        "actions": ["Admin", "Read", "Write", "List", "Tagging"]}]}, indent=2) + "\n"


def sprout_prepare() -> None:
    """Create the generated, private files the sprout compose file mounts. Idempotent: never rotates existing secrets."""
    os.makedirs(SPROUT_DIR, exist_ok=True)
    os.chmod(HOME_DIR, 0o700)
    if not os.path.exists(sprout_env_file()):
        rc, vols = run(["docker", "volume", "ls", "-q"], capture=True, timeout=15)
        if any(v.endswith("_keycloak_db") for v in (vols or "").split()):
            raise SystemExit("Sprout data exists but its generated secrets (~/.securax/sprout/.env.sprout) are missing, so the database password cannot be\n"
                             "re-created. Restore ~/.securax/sprout from your ./securax backup (it is included), or start fresh with: ./securax prune sprout")
    env = read_env_file(sprout_env_file())
    changed = False
    for key in ("KEYCLOAK_DB_PASSWORD", "KEYCLOAK_ADMIN_PASSWORD", "S3_ACCESS_KEY", "S3_SECRET_KEY"):
        if not env.get(key):
            env[key] = new_secret(12) if key == "S3_ACCESS_KEY" else new_secret()
            changed = True
    if changed or not os.path.exists(sprout_env_file()):
        write_private(sprout_env_file(), "".join(f"{k}={v}\n" for k, v in env.items()))
    write_private(os.path.join(SPROUT_DIR, "s3.json"), s3_config_json(env["S3_ACCESS_KEY"], env["S3_SECRET_KEY"]))
    webhook = read_env_file(os.path.join(COMPOSE_DIR, ".env")).get("ALERT_WEBHOOK", "")
    # 0644 on purpose: the Alertmanager image runs as an unprivileged user and must be able to read it. The directory
    # itself is 0700, so other host users still cannot reach it.
    write_private(os.path.join(SPROUT_DIR, "alertmanager.yml"), alertmanager_yaml(webhook), mode=0o644)


def container_health(service: str) -> str:
    rc, cid = run(sprout_compose("ps", "-a", "-q", service), cwd=COMPOSE_DIR, env=sprout_env(), capture=True, timeout=30)
    cid = (cid or "").strip().splitlines()[-1:] or [""]
    if rc != 0 or not cid[0]:
        return "absent"
    rc, out = run(["docker", "inspect", "-f", "{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{end}}", cid[0]], capture=True, timeout=15)
    status, _, health = (out or "").strip().partition("|")
    return health or status or "unknown"


def wait_healthy(services: list[str], timeout: int = 240) -> bool:
    end = time.time() + timeout
    pending = list(services)
    while pending and time.time() < end:
        pending = [s for s in pending if container_health(s) not in ("healthy", "running")]
        if pending:
            time.sleep(3)
    return not pending


def http_json(method: str, url: str, body: dict | None = None, timeout: int = 10):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"raw": raw}
    except (urllib.error.URLError, OSError, ValueError):
        return 0, {}


def openbao_unseal(base: str = "http://127.0.0.1:8200") -> str:
    """Initialise once; unseal on every wake (a stopped OpenBao always wakes sealed). Returns a one-line status."""
    keyfile = os.path.join(SPROUT_DIR, "openbao-init.json")
    st, init = http_json("GET", f"{base}/v1/sys/init")
    if st != 200:
        return "openbao: not reachable"
    if not init.get("initialized"):
        st, res = http_json("POST", f"{base}/v1/sys/init", {"secret_shares": 1, "secret_threshold": 1})
        if st != 200 or not res.get("keys"):
            return f"openbao: init failed ({st})"
        write_private(keyfile, json.dumps({"unseal_key": res["keys"][0], "root_token": res["root_token"]}))
    try:
        creds = json.load(open(keyfile))
    except (OSError, ValueError):
        return "openbao: initialised, but its key file is missing — restore ~/.securax/sprout/openbao-init.json from your backup"
    st, seal = http_json("GET", f"{base}/v1/sys/seal-status")
    if seal.get("sealed"):
        st, _ = http_json("PUT", f"{base}/v1/sys/unseal", {"key": creds["unseal_key"]})
        if st != 200:
            return f"openbao: unseal failed ({st})"
        return "openbao: unsealed"
    return "openbao: already unsealed"


def sprout_status() -> str:
    states = [container_health(s) for s in SPROUT_SERVICES]
    if all(s in ("healthy", "running") for s in states):
        return "awake"
    if any(s in ("healthy", "running", "starting") for s in states):
        return "partial"
    if any(s in ("exited", "created", "paused") for s in states):
        return "hibernating"          # containers exist, stopped, data kept
    rc, vols = run(["docker", "volume", "ls", "-q"], capture=True, timeout=15)
    if any(v.endswith(tuple("_" + n for n in SPROUT_VOLUMES)) for v in (vols or "").split()):
        return "hibernating"
    return "dormant"


# ───────────────────────────────────────────── organs ─────────────────────────────────────────────
def organ_spec(name: str) -> dict:
    organs = load_json("organs.json")["organs"]
    if name not in organs:
        raise SystemExit(f"unknown organ '{name}'. Organs: {', '.join(organs)}")
    spec = dict(organs[name])
    ov = os.environ.get("SECURAX_ORGAN_OVERRIDE")        # test hook: point an organ at a local stand-in repo
    if ov:
        spec.update(json.loads(ov).get(name, {}))
    return spec


def organ_dir(name: str) -> str:
    return os.path.join(ORGANS_DIR, name)


def organ_fetch(name: str) -> str:
    """Fetch the pinned ref (tag, branch or commit sha) into ~/.securax/organs/<name>. Idempotent."""
    spec = organ_spec(name)
    d = organ_dir(name)
    stamp = os.path.join(d, ".securax-ref")
    want = f"{spec['repo']}@{spec['ref']}"
    if os.path.exists(stamp) and open(stamp).read().strip() == want:
        return d
    os.makedirs(d, exist_ok=True)
    steps = [["git", "init", "-q"], ["git", "remote", "remove", "origin"], ["git", "remote", "add", "origin", spec["repo"]],
             ["git", "fetch", "-q", "--depth", "1", "origin", spec["ref"]], ["git", "checkout", "-q", "--force", "FETCH_HEAD"]]
    for s in steps:
        rc, out = run(s, cwd=d, capture=True, timeout=300)
        if rc != 0 and s[1] != "remote":                 # `remote remove` fails on first run: fine
            raise SystemExit(f"organ {name}: '{' '.join(s)}' failed:\n{out}")
    write_private(stamp, want + "\n")
    return d


def prepare_env(workdir: str, env_spec: dict) -> None:
    """Create <file> from <copy_from> and set keys. A literal value is always applied; '@secret' becomes a fresh random
    secret ONLY if the key has no value yet (re-running never rotates a database password under a running organ)."""
    target = os.path.join(workdir, env_spec["file"])
    if not os.path.exists(target):
        shutil.copyfile(os.path.join(workdir, env_spec["copy_from"]), target)
    lines = open(target, encoding="utf-8").read().splitlines()
    for key, val in env_spec["set"].items():
        pat = re.compile(rf"^\s*#?\s*{re.escape(key)}\s*=(.*)$")
        done = False
        for i, ln in enumerate(lines):
            m = pat.match(ln)
            if m:
                if val == "@secret" and not ln.lstrip().startswith("#") and m.group(1).strip():
                    done = True                          # a secret that already has a value is kept (never rotate under a running DB)
                    break
                lines[i] = f"{key}={new_secret() if val == '@secret' else val}"       # literal settings are always (re)applied
                done = True
                break
        if not done:
            lines.append(f"{key}={new_secret() if val == '@secret' else val}")
    write_private(target, "\n".join(lines) + "\n")


def override_yaml(ports: dict[str, list[str]]) -> str:
    out = ["# generated by SecuRAX: pin every published port to localhost (or a non-clashing one)", "services:"]
    for svc, plist in ports.items():
        out.append(f"  {svc}:")
        out.append("    ports: !override")
        out += [f'      - "{p}"' for p in plist]
    return "\n".join(out) + "\n"


def organ_compose(name: str, *args: str) -> tuple[list[str], str]:
    spec = organ_spec(name)
    wd = os.path.join(organ_dir(name), spec["dir"])
    argv = ["docker", "compose", "-p", f"securax-{name}", "-f", "docker-compose.yml"]
    if os.path.exists(os.path.join(wd, "docker-compose.securax.yml")):
        argv += ["-f", "docker-compose.securax.yml"]
    return argv + list(args), wd


def organ_prepare(name: str, light: bool = False) -> str:
    """Fetch + prepare an organ. light=True skips steps marked heavy (image pulls / big downloads) — for config checks."""
    spec = organ_spec(name)
    d = organ_fetch(name)
    wd = os.path.join(d, spec["dir"])
    if spec.get("env"):
        prepare_env(wd, spec["env"])
    marker = os.path.join(wd, ".securax-prepared")
    if light or not os.path.exists(marker):
        for step in spec.get("pre", []):
            if light and step.get("heavy"):
                continue
            rc, out = run(step["argv"], cwd=wd, env=step.get("env"), capture=True, timeout=900)
            if rc != 0:
                raise SystemExit(f"organ {name}: preparation step '{' '.join(step['argv'])}' failed:\n{out[-1500:]}")
        if not light:
            write_private(marker, "ok\n")
    if spec.get("override"):
        write_private(os.path.join(wd, "docker-compose.securax.yml"), override_yaml(spec["override"]))
    return wd


def organ_status(name: str) -> str:
    spec = organ_spec(name)
    if not os.path.isdir(os.path.join(organ_dir(name), spec["dir"])):
        return "dormant"
    argv, wd = organ_compose(name, "ps", "-a", "--format", "{{.State}}")
    rc, out = run(argv, cwd=wd, capture=True, timeout=30)
    states = [s for s in (out or "").split() if s]
    if rc != 0 or not states:
        return "dormant"
    if all(s == "running" for s in states):
        return "awake"
    if any(s == "running" for s in states):
        return "partial"
    return "hibernating"


def organ_check_config(name: str) -> tuple[bool, str]:
    """Fetch + prepare + `docker compose config` — proves the pinned ref and our recipe are valid without pulling images."""
    wd = organ_prepare(name, light=True)
    argv, _ = organ_compose(name, "config", "-q")
    rc, out = run(argv, cwd=wd, capture=True, timeout=120)
    return rc == 0, out


# ───────────────────────────────────────────── soil (preflight) ─────────────────────────────────────────────
def check(ok: bool | None, label: str, fix: str = "") -> tuple[str, bool]:
    sym = "✔" if ok else ("!" if ok is None else "✘")
    say(f"  {sym} {label}" + (f"\n      → {fix}" if fix and not ok else ""))
    return sym, ok is not False


def cloud_name() -> str:
    return (os.environ.get("SECURAX_CLOUD") or read_env_file(os.path.join(COMPOSE_DIR, ".env")).get("SECURAX_CLOUD") or "aws").lower()


def soil(stage: str, with_organs: list[str] | None = None) -> bool:
    """Is the soil ready for this stage? Prints what is fine and the exact fix for what is not."""
    st = stages()[stage]
    head(f"Soil test for '{stage}' ({st['nature']}, {st['gait']}) — {st['where']}")
    good = True
    need = st.get("needs", {})
    if "docker" in need.get("tools", []):
        ok = run(["docker", "info"], capture=True, timeout=20)[0] == 0
        good &= check(ok, "Docker is running", "start Docker Desktop (Windows: WSL integration ON for your distro)")[1]
        mem, cpus = docker_resources()
        if mem:
            req = need.get("ram_gb", 0) * 1024
            organs = with_organs or []
            req += sum(organ_spec(o)["ram_gb"] * 1024 for o in organs)
            good &= check(mem >= req, f"memory for Docker: {mem // 1024} GB visible, {req // 1024} GB wanted ({cpus} CPUs)",
                          "raise it: Windows %UserProfile%\\.wslconfig [wsl2] memory=…  then  wsl --shutdown; Docker Desktop: Settings → Resources")[1]
        disk = need.get("disk_gb", 0) + sum(organ_spec(o)["disk_gb"] for o in (with_organs or []))
        free = free_disk_gb(HOME_DIR)
        # Below a third of what is wanted is a hard stop; between a third and the full amount it is only a warning
        # (a lab sprout runs fine in less; the organs are what grow).
        disk_ok = True if free >= disk else (None if free * 3 >= disk else False)
        good &= check(disk_ok, f"disk: {free} GB free here, {disk} GB wanted", "free some space (docker system prune -f)")[1]
        if stage == "sprout":
            good &= check(compose_version() >= MIN_COMPOSE, f"Docker Compose ≥ {MIN_COMPOSE[0]}.{MIN_COMPOSE[1]}", "update Docker Desktop / the compose plugin")[1]
        for o in with_organs or []:
            for key, val in organ_spec(o).get("sysctl", {}).items():
                rc, cur = run(["sysctl", "-n", key], capture=True, timeout=10)
                try:
                    okv = int(cur.strip()) >= val
                except ValueError:
                    okv = None
                good &= check(okv, f"{o}: {key} ≥ {val}", f"sudo sysctl -w {key}={val}   (WSL: re-run after each wsl --shutdown)")[1]
            good &= check(have("git"), f"{o}: git is installed", "sudo apt-get install -y git")[1]
    if st.get("cloud"):
        cloud = cloud_name()
        good &= check(have("terraform"), "terraform is installed", "https://developer.hashicorp.com/terraform/install")[1]
        for tool in ([] if offline_plan() else need.get("cloud_tools", {}).get(cloud, [])):
            good &= check(have(tool), f"{tool} CLI is installed ({cloud})", f"install the {cloud} CLI")[1]
        if "kubectl" in need.get("tools", []) and not offline_plan():
            good &= check(have("kubectl"), "kubectl is installed", "https://kubernetes.io/docs/tasks/tools/")[1]
        d = os.path.join(TF_DIR, cloud)
        good &= check(os.path.isdir(d), f"genome for {cloud} present ({os.path.relpath(d, ROOT)})", "git pull")[1]
        if cloud == "aws" and have("aws") and not offline_plan():
            rc, _ = run(["aws", "sts", "get-caller-identity"], capture=True, timeout=20)
            good &= check(rc == 0, "AWS credentials work", "aws configure   (or: export AWS_PROFILE=…)")[1]
        say("  · cost: " + st.get("awake_cost", "") + "  [estimate — check your provider's calculator]")
    say("  → " + ("soil is ready." if good else "fix the ✘ items above, then re-run."))
    return good


# ───────────────────────────────────────────── cloud (terraform) ─────────────────────────────────────────────
def tf_dir() -> str:
    d = os.path.join(TF_DIR, cloud_name())
    if not os.path.isdir(d):
        raise SystemExit(f"no Terraform genome for cloud '{cloud_name()}' (expected {d})")
    return d


def offline_plan() -> bool:
    return os.environ.get("SECURAX_OFFLINE_PLAN") == "1"        # test hook: skip credential checks, plan with fake credentials


def tf_vars(stage: str, awake: bool, size: str | None = None) -> list[str]:
    a = ["-var", f"stage={stage}", "-var", f"awake={'true' if awake else 'false'}"]
    if offline_plan():
        a += ["-var", "offline=true"] if cloud_name() == "aws" else (["-var", "gcp_project_id=proj-offline"] if cloud_name() == "gcp" else [])
    if size and cloud_name() in ("aws", "azure"):
        a += ["-var", f"size={size}"]
    return a


def tf_state(d: str) -> dict:
    if not os.path.exists(os.path.join(d, "terraform.tfstate")):
        return {}
    rc, out = run(["terraform", "output", "-json", "state"], cwd=d, capture=True, timeout=60)
    try:
        return json.loads(out)
    except ValueError:
        return {}


def cloud_status(stage: str) -> str:
    if not have("terraform"):
        return "unknown (terraform not installed)"
    try:
        d = tf_dir()
    except SystemExit:
        return "unknown"
    st = tf_state(d)
    if not st:
        return "dormant"
    if st.get("awake") and ((stage == "forest" and st.get("stage") == "forest") or (stage == "canopy" and st.get("stage") in ("canopy", "forest")) or st.get("stage") == stage):
        return "awake"
    if st.get("stage") == stage or (stage in ("canopy", "forest") and st.get("stage") in ("canopy", "forest")):
        return "hibernating"
    return "dormant"


def tf_run(stage: str, awake: bool, apply: bool, yes: bool, size: str | None) -> int:
    d = tf_dir()
    extra: list[str] = []
    cloud = cloud_name()
    if cloud == "aws" and stage == "tree" and awake:
        ami = os.environ.get("SECURAX_AMI_ID") or ("ami-0123456789abcdef0" if offline_plan() else aws_ubuntu_ami())
        if ami:
            extra += ["-var", f"ami_id={ami}"]
    rc, out = run(["terraform", "init", "-input=false"], cwd=d, capture=True, timeout=900)
    if rc != 0:
        say(out[-1500:])
        return rc
    args = tf_vars(stage, awake, size) + extra
    head(f"terraform plan — {cloud} · stage={stage} · awake={awake}")
    rc, _ = run(["terraform", "plan", "-input=false", *args], cwd=d, timeout=1800)
    if rc != 0:
        return rc
    if not apply:
        say("\nThis was a PLAN only — nothing was created or changed. Add --apply to do it for real.")
        return 0
    if not confirm("\nApply this plan? Cloud resources may start billing.", yes):
        say("cancelled.")
        return 1
    rc, _ = run(["terraform", "apply", "-input=false", "-auto-approve", *args], cwd=d, timeout=3600)
    return rc


def aws_ubuntu_ami() -> str:
    if not have("aws"):
        return ""
    rc, out = run(["aws", "ssm", "get-parameter", "--name", "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id",
                   "--query", "Parameter.Value", "--output", "text", "--region", os.environ.get("AWS_REGION", "ap-south-1")], capture=True, timeout=30)
    return out.strip() if rc == 0 and out.strip().startswith("ami-") else ""


def tf_output(d: str, name: str) -> str:
    rc, out = run(["terraform", "output", "-raw", name], cwd=d, capture=True, timeout=60)
    return out.strip() if rc == 0 else ""


def provider_secret_args() -> list[str]:
    """--from-literal args for the router's provider keys, taken from the local .env (only keys that are set)."""
    env = read_env_file(os.path.join(COMPOSE_DIR, ".env"))
    keys = [k for k in env if (k.endswith("_API_KEY") or k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AZURE_API_BASE")) and env[k]]
    return [f"--from-literal={k}={env[k]}" for k in sorted(keys)]


def render_velero(vault: str, region: str) -> str:
    tmpl = open(os.path.join(ROOT, "gitops", "templates", "velero.app.yaml.tmpl"), encoding="utf-8").read()
    return tmpl.replace("@VAULT_BUCKET@", vault).replace("@REGION@", region)


def k8s_bootstrap(d: str) -> None:
    """After a managed cluster wakes: point kubectl at it and hand over to GitOps (Argo CD + the root app)."""
    cmd = tf_output(d, "connect")
    if not cmd:
        return
    say(f"\nConnect:  {cmd}")
    if not have("kubectl"):
        say("Install kubectl, run the command above, then re-run:  ./securax grow canopy --apply")
        return
    run(cmd.split(), timeout=120)
    argocd = os.environ.get("SECURAX_ARGOCD_VERSION", "v3.5.5")
    for ns in ("argocd", "securax-core", "velero"):
        run(["kubectl", "create", "namespace", ns], capture=True)
    # Secrets that are deliberately NOT in git: the router key (random, generated once) and your provider keys.
    rc, _ = run(["kubectl", "-n", "securax-core", "get", "secret", "router-key"], capture=True)
    if rc != 0:
        run(["kubectl", "-n", "securax-core", "create", "secret", "generic", "router-key", f"--from-literal=LITELLM_MASTER_KEY=sk-{new_secret(24)}"], capture=True)
    pargs = provider_secret_args()
    if pargs:
        p = subprocess.run(["kubectl", "-n", "securax-core", "create", "secret", "generic", "securax-providers", *pargs, "--dry-run=client", "-o", "yaml"], text=True, capture_output=True)
        subprocess.run(["kubectl", "apply", "-f", "-"], input=p.stdout, text=True, capture_output=True)
        say(f"  provider keys from your local .env were stored in the cluster as Secret securax-providers ({len(pargs)} keys)")
    rc, _ = run(["kubectl", "apply", "--server-side", "-n", "argocd", "-f", f"https://raw.githubusercontent.com/argoproj/argo-cd/{argocd}/manifests/install.yaml"], timeout=600)
    if rc != 0:
        say("! could not install Argo CD (check connectivity); re-run ./securax grow canopy --apply")
        return
    run(["kubectl", "apply", "-f", os.path.join(ROOT, "gitops", "root-app.yaml")], timeout=120)
    vault, region = tf_output(d, "vault"), tf_output(d, "region") or "ap-south-1"
    if vault and cloud_name() == "aws":
        subprocess.run(["kubectl", "apply", "-f", "-"], input=render_velero(vault, region), text=True, capture_output=True)
        role = tf_output(d, "velero_role_arn")
        say(f"  backups: Velero → s3://{vault}/velero (pod-identity role {role or 'n/a'})")
    say("Argo CD is installed and the root app applied: the platform now grows itself from git (gitops/). Watch it: kubectl -n argocd get applications")


# ───────────────────────────────────────────── tenants (phase 4) ─────────────────────────────────────────────
TENANT_DIR = os.path.join(ROOT, "gitops", "tenants")
TENANT_ID = re.compile(r"^[a-z][a-z0-9]{1,15}$")


def parse_tenant_file(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^([A-Za-z_][\w]*):\s*(.*?)\s*(#.*)?$", line.strip())
        if m and not line.lstrip().startswith("#"):
            out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return out


def list_tenants() -> dict[str, dict[str, str]]:
    tenants: dict[str, dict[str, str]] = {}
    if os.path.isdir(TENANT_DIR):
        for f in sorted(os.listdir(TENANT_DIR)):
            if f.endswith(".yaml"):
                t = parse_tenant_file(os.path.join(TENANT_DIR, f))
                if t.get("id"):
                    tenants[t["id"]] = t
    return tenants


def sync_tenants_tfvars() -> str:
    """Single source of truth = gitops/tenants/*.yaml. Mirror it into the Terraform genome so each tenant also gets its own
    key + bucket (AWS)."""
    tenants = {tid: {} for tid in list_tenants()}
    path = os.path.join(TF_DIR, "aws", "tenants.auto.tfvars.json")
    if cloud_name() == "aws":
        write_private(path, json.dumps({"tenants": tenants}, indent=2) + "\n", mode=0o644)
    return path


def cmd_tenant(a: argparse.Namespace) -> int:
    if a.action == "list":
        t = list_tenants()
        say("\n".join(f"  {k:<16} tier={v.get('tier', '?'):<7} group={v.get('oidcGroup', '-'):<16} {v.get('name', '')}" for k, v in t.items()) or "no tenants yet: ./securax tenant add <id> --name \"…\" --tier small")
        return 0
    if not a.id or not TENANT_ID.match(a.id):
        raise SystemExit("tenant id: 2-16 chars, lowercase letters/digits, starting with a letter")
    path = os.path.join(TENANT_DIR, f"{a.id}.yaml")
    if a.action == "add":
        if os.path.exists(path):
            raise SystemExit(f"tenant {a.id} already exists ({os.path.relpath(path, ROOT)})")
        os.makedirs(TENANT_DIR, exist_ok=True)
        name = (a.name or a.id).replace('"', "'")
        group = a.group or f"{a.id}-staff"
        write_private(path, f'id: {a.id}\nname: "{name}"\ntier: {a.tier}\noidcGroup: {group}\n', mode=0o644)
        sync_tenants_tfvars()
        say(f"tenant '{a.id}' written to {os.path.relpath(path, ROOT)}. Commit and push it: Argo CD stamps the tenant cell from charts/tenant.")
        say("Cloud-side key + bucket: ./securax grow forest --apply   (reads the same file).")
        return 0
    if a.action == "remove":
        if not os.path.exists(path):
            raise SystemExit(f"no tenant '{a.id}'")
        os.remove(path)
        sync_tenants_tfvars()
        say(f"tenant '{a.id}' removed from git: Argo CD prunes its namespace after you push. Its cloud key/bucket are kept until you remove them in Terraform on purpose.")
        return 0
    return 1


# ───────────────────────────────────────────── commands ─────────────────────────────────────────────
def cmd_stages(_: argparse.Namespace) -> int:
    head("The ladder — everything above the seed is dormant until you grow it")
    for sid, st in stages().items():
        if sid == "seed":
            rc, _out = run(["curl", "-fsS", "-m", "3", "http://localhost:8080/readyz"], capture=True)
            state = "awake" if rc == 0 else "dormant"
        elif sid == "sprout":
            state = sprout_status()
        elif sid == "burrow":
            state = bw.twin_status()
        else:
            state = cloud_status(sid)
        icon = {"awake": "●", "partial": "◐", "hibernating": "◌", "dormant": "○"}.get(state.split()[0], "?")
        say(f"  {icon} {sid:<7} phase {st['phase']} ({st['gait']:<5}) {st['nature']:<7} {state:<12} {st['where']}")
        if sid == "sprout":
            for o in st.get("organs", []):
                say(f"        · organ {o:<8} {organ_status(o)}")
    say(f"\n  ◇ range    Active Directory practice lab (OSCP-style, wraps GOAD): {'recipe fetched' if rng.status() == 'fetched' else 'dormant'}   → ./securax range soil")
    say("\n  ● awake   ◐ partly awake   ◌ hibernating (data kept)   ○ dormant (never grown)")
    say("  Wake: ./securax grow <stage>   Sleep: ./securax hibernate <stage>   Check readiness: ./securax soil <stage>")
    return 0


def cmd_soil(a: argparse.Namespace) -> int:
    stage = resolve_stage(a.stage)
    return 0 if soil(stage, with_list(a)) else 1


def with_list(a: argparse.Namespace) -> list[str]:
    raw = getattr(a, "with_", "") or ""
    if raw == "all":
        return list(load_json("organs.json")["organs"])
    return [x for x in raw.split(",") if x]


def cmd_grow(a: argparse.Namespace) -> int:
    stage = resolve_stage(a.stage)
    organs = with_list(a)
    if stage == "seed":
        return run(["bash", os.path.join(ROOT, "securax"), "up"])[0]
    if not soil(stage, organs):
        return 1
    if stage == "sprout":
        sprout_prepare()
        head("Germinating sprout …")
        rc, _ = run(sprout_compose("up", "-d", *SPROUT_SERVICES), cwd=COMPOSE_DIR, env=sprout_env())
        if rc != 0:
            return rc
        if not wait_healthy(SPROUT_SERVICES):
            say("Some services are still starting: check  ./securax stages  in a minute.")
        say("  " + openbao_unseal())
        say("\n  Keycloak (SSO)   http://localhost:8180   admin password: ~/.securax/sprout/.env.sprout (KEYCLOAK_ADMIN_PASSWORD)")
        say("  OpenBao          http://localhost:8200   root token + unseal key: ~/.securax/sprout/openbao-init.json (mode 600)")
        say("  S3 (SeaweedFS)   http://localhost:8333   keys: ~/.securax/sprout/.env.sprout")
        say("  Prometheus       http://localhost:9090   Alertmanager http://localhost:9093")
        for o in organs:
            rc = grow_organ(o)
            if rc != 0:
                return rc
        return 0
    if stage == "burrow":
        head("Digging the burrow (Docker twin of your future hardware) …")
        rc = bw.twin_up(gitops=getattr(a, "gitops", False))
        if rc == 0:
            say("\n  Real machines: ./securax spore server --name burrow1   (then agents: ./securax spore agent --name burrow2 --join https://<ip>:6443)")
        return rc
    # cloud stages
    return grow_cloud(stage, a)


def grow_organ(name: str) -> int:
    spec = organ_spec(name)
    head(f"Growing organ: {spec['label']}  (pinned {spec['ref'][:12]})")
    wd = organ_prepare(name)
    argv, _ = organ_compose(name, "up", "-d")
    rc, _ = run(argv, cwd=wd, timeout=3600)
    if rc == 0:
        say(f"  {spec['label']}: {spec['url']}")
        if spec.get("warning"):
            say("  ! " + spec["warning"])
    return rc


def grow_cloud(stage: str, a: argparse.Namespace) -> int:
    d = tf_dir()
    if stage == "forest":
        sync_tenants_tfvars()
    rc = tf_run(stage, True, a.apply, a.yes, a.size)
    if rc == 0 and a.apply:
        if stage in ("canopy", "forest"):
            k8s_bootstrap(d)
        else:
            rcc, out = run(["terraform", "output", "-raw", "connect"], cwd=d, capture=True, timeout=60)
            say(f"\nConnect (no open ports):  {out.strip()}" if rcc == 0 else "")
    return rc


def cmd_hibernate(a: argparse.Namespace) -> int:
    stage = resolve_stage(a.stage)
    if stage == "seed":
        return run(["bash", os.path.join(ROOT, "securax"), "down"])[0]
    if stage == "sprout":
        head("Putting sprout to sleep (data is kept) …")
        if not a.no_backup and have("docker"):
            rc, _ = run(["bash", os.path.join(ROOT, "securax"), "backup"])
            if rc != 0:
                say("! backup failed — not hibernating (use --no-backup to override)")
                return rc
        for o in load_json("organs.json")["organs"]:
            if organ_status(o) in ("awake", "partial"):
                argv, wd = organ_compose(o, "stop")
                run(argv, cwd=wd)
        rc, _ = run(sprout_compose("stop", *SPROUT_SERVICES), cwd=COMPOSE_DIR, env=sprout_env())
        say("sprout is hibernating. Wake it with  ./securax grow sprout")
        return rc
    if stage == "burrow":
        head("Putting the burrow twin to sleep (the cluster's memory is kept) …")
        return bw.twin_stop()
    tf_dir()          # fail early (clear message) if there is no genome for the chosen cloud
    if stage in ("canopy", "forest") and not a.no_backup and a.apply and have("kubectl"):
        head("Asking Velero for a last backup before the cluster sleeps …")
        stamp = time.strftime("%Y%m%d-%H%M%S")
        manifest = f"apiVersion: velero.io/v1\nkind: Backup\nmetadata:\n  name: pre-sleep-{stamp}\n  namespace: velero\nspec:\n  includedNamespaces: ['*']\n  ttl: 720h0m0s\n"
        p = subprocess.run(["kubectl", "apply", "-f", "-"], input=manifest, text=True, capture_output=True)
        say("  " + (p.stdout.strip() or p.stderr.strip()))
        for _ in range(60):
            rc, out = run(["kubectl", "-n", "velero", "get", "backup", f"pre-sleep-{stamp}", "-o", "jsonpath={.status.phase}"], capture=True, timeout=30)
            if out.strip() in ("Completed", "PartiallyFailed", "Failed"):
                say(f"  backup phase: {out.strip()}")
                break
            time.sleep(10)
    return tf_run(stage, False, a.apply, a.yes, a.size)


def cmd_prune(a: argparse.Namespace) -> int:
    stage = resolve_stage(a.stage)
    head(f"PRUNE (apoptosis) '{stage}' — this deletes its data")
    if stage == "seed":
        say("The seed is your laptop estate; remove it with: ./securax down  and  docker compose down -v (in local/compose).")
        return 1
    if not confirm(f"This permanently deletes the {stage} stage's data.", False, typed=f"PRUNE {stage}"):
        say("cancelled — nothing was changed.")
        return 1
    if stage == "sprout":
        for o in load_json("organs.json")["organs"]:
            if os.path.isdir(organ_dir(o)):
                argv, wd = organ_compose(o, "down", "-v")
                run(argv, cwd=wd)
                shutil.rmtree(organ_dir(o), ignore_errors=True)
        run(sprout_compose("rm", "-s", "-f", "-v", *SPROUT_SERVICES), cwd=COMPOSE_DIR, env=sprout_env())
        for v in SPROUT_VOLUMES:
            run(["docker", "volume", "rm", "-f", f"{PROJECT}_{v}"], capture=True)
        shutil.rmtree(SPROUT_DIR, ignore_errors=True)
        say("sprout pruned (containers, volumes, generated secrets).")
        return 0
    if stage == "burrow":
        say("Real machines are yours to wipe; this removes only the Docker twin.")
        return bw.twin_down()
    d = tf_dir()
    say("Cloud prune runs `terraform destroy`. Protected data (vault bucket, tenant buckets, the roots disk) has deletion guards on purpose:")
    say("empty/remove them deliberately first (that is the point of the guard). Preview with a plan:")
    run(["terraform", "init", "-input=false"], cwd=d, capture=True)
    if not a.apply:
        return run(["terraform", "plan", "-destroy", "-input=false", *tf_vars(stage, False)], cwd=d)[0]
    return run(["terraform", "destroy", "-input=false", *tf_vars(stage, False)], cwd=d)[0]


def cmd_scale(a: argparse.Namespace) -> int:
    stage = resolve_stage(a.stage)
    a.size = a.newsize
    if stage == "burrow":
        say("Vertical: buy/upgrade the machine. Horizontal: add a node with ./securax spore agent (or a 2nd/3rd server for HA: etcd is already embedded).")
        return 0
    if stage in ("seed", "sprout"):
        say("Seed/sprout size themselves to what Docker can use on every `./securax up` (see docs/securax/25). To give them more: raise Docker/WSL memory.")
        return 0
    d = tf_dir()
    write = os.path.join(d, "securax.auto.tfvars")
    write_private(write, f'size = "{a.size}"\n') if cloud_name() in ("aws", "azure") else None
    say(f"vertical scale for {stage} on {cloud_name()}: size={a.size} (written to {os.path.relpath(write, ROOT)}).")
    if stage in ("canopy", "forest"):
        say("Horizontal scale is automatic (EKS Auto Mode / GKE Autopilot / AKS autoscaler: nodes follow pods, down to zero).")
    if stage == "tree":
        say("The tree is ONE node. To scale out, graduate to canopy: ./securax grow canopy")
    return tf_run(stage, True, a.apply, a.yes, a.size)


CRON_TAG = "# securax-rhythm"


def cmd_rhythm(a: argparse.Namespace) -> int:
    """Circadian rhythm: a nightly sleep and a morning wake for the sprout stage, via your user crontab (opt-in)."""
    if not have("crontab"):
        say("crontab is not available here (on WSL: sudo apt-get install -y cron && sudo service cron start).")
        return 1
    rc, cur = run(["crontab", "-l"], capture=True)
    lines = [ln for ln in (cur if rc == 0 else "").splitlines() if CRON_TAG not in ln]
    if a.mode == "status":
        mine = [ln for ln in (cur if rc == 0 else "").splitlines() if CRON_TAG in ln]
        say("\n".join(mine) if mine else "no rhythm set (the estate stays in whatever state you left it).")
        return 0
    if a.mode == "off":
        p = subprocess.run(["crontab", "-"], input="\n".join(lines) + ("\n" if lines else ""), text=True)
        say("rhythm removed.")
        return p.returncode
    sleep_h, sleep_m = (int(x) for x in a.sleep.split(":"))
    wake_h, wake_m = (int(x) for x in a.wake.split(":"))
    sx = os.path.join(ROOT, "securax")
    lines += [f"{sleep_m} {sleep_h} * * * bash {sx} hibernate sprout --no-backup {CRON_TAG}",
              f"{wake_m} {wake_h} * * * bash {sx} grow sprout {CRON_TAG}"]
    p = subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True)
    say(f"rhythm set: sprout sleeps at {a.sleep} and wakes at {a.wake} every day (undo: ./securax rhythm off).")
    return p.returncode


def cmd_organ(a: argparse.Namespace) -> int:
    """Direct control of one organ: ./securax organ wazuh up|stop|status|down"""
    name = a.name
    organ_spec(name)
    if a.action == "up":
        return grow_organ(name)
    if a.action == "status":
        say(f"{name}: {organ_status(name)}")
        return 0
    if not os.path.isdir(organ_dir(name)):
        say(f"{name} is dormant (never grown).")
        return 0
    argv, wd = organ_compose(name, "stop" if a.action == "stop" else "down", *(["-v"] if a.action == "down" else []))
    return run(argv, cwd=wd)[0]


def cmd_burrow(a: argparse.Namespace) -> int:
    """./securax burrow status|power|test — direct control of the twin's reflexes."""
    if a.action == "status":
        return bw.twin_report()
    if a.action == "power":
        if bw.twin_status() != "awake":
            say("The twin must be awake to rehearse a power cut: ./securax grow burrow")
            return 1
        return bw.power_event()
    return 1


def cmd_spore(a: argparse.Namespace) -> int:
    """Write the installer for one real machine (server or agent). Nothing is run or contacted."""
    try:
        sp, ci = bw.write_spore(a.role, a.name, join_url=a.join or "", gpu=a.gpu, ups=a.ups, gitops=a.gitops, repo=a.repo)
    except ValueError as e:
        say(f"! {e}")
        return 2
    head(f"Spore for '{a.name}' ({a.role}) written")
    say(f"  script      : {sp}\n  cloud-init  : {ci}   (both owner-only: they contain the cluster join token)")
    say("\nUse ONE of:\n  a) fresh Ubuntu Server 24.04 LTS, then:   sudo bash <script>\n  b) put the cloud-init file on a USB labelled CIDATA (as 'user-data' plus an empty 'meta-data') and boot the installer")
    if a.gpu:
        say("  GPU: the node is labelled securax.io/gpu=nvidia; install the NVIDIA driver + container toolkit for your card first.")
    return 0


def cmd_range(a: argparse.Namespace) -> int:
    """./securax range soil|plan|install|wake|hibernate|snapshot|reset|status|prune — the dormant AD practice lab (GOAD)."""
    h = rng.host()
    lines, rec = rng.soil_report(h)
    lab = a.lab or rec or "MINILAB"
    provider = a.provider or "virtualbox"
    if a.action == "soil":
        head("Range soil test — which Active Directory lab fits here?")
        for ln in lines:
            say(ln)
        say("provider: " + rng.provider_advice(h))
        return 0
    if a.action == "plan":
        head(f"Range plan — {lab} on {provider}")
        for ln in rng.plan(lab, provider):
            say(ln)
        return 0
    if a.action == "fetch":
        say(f"GOAD pinned at {rng.cfg()['ref'][:12]} → {rng.fetch()}")
        return 0
    if a.action == "prune":
        head(f"PRUNE the range '{lab}' — destroys its VMs and disks")
        typed = f"PRUNE range {lab}" if confirm("This destroys the lab's VMs and their disks (the recipe stays).", False, typed=f"PRUNE range {lab}") else ""
        return rng.prune(lab, provider, typed, a.i_accept_cloud_cost)
    if a.action == "install":
        if lab not in rng.fitting_labs(h) and not a.force:
            say(f"! {lab} needs more RAM than this machine can spare. Fits here: {', '.join(rng.fitting_labs(h)) or 'nothing'}.  (Override with --force; the VMs may swap or fail.)")
            return 2
        for w in rng.cfg()["warnings"]:
            say("  ! " + w)
        if not confirm(f"\nInstall {lab} on {provider}? It downloads many GB of Windows images and takes hours.", a.yes):
            say("cancelled — nothing was changed.")
            return 1
    return rng.run_task(a.action, lab, provider, a.i_accept_cloud_cost)


def cmd_organ_check(a: argparse.Namespace) -> int:
    names = a.names or list(load_json("organs.json")["organs"])
    bad = 0
    for n in names:
        ok, out = organ_check_config(n)
        say(f"  {'✔' if ok else '✘'} organ {n}: pinned ref fetched, prepared, compose config valid" + ("" if ok else "\n" + out[-600:]))
        bad += 0 if ok else 1
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax lifecycle", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stages", help="show every stage and whether it is awake, hibernating or dormant").set_defaults(fn=cmd_stages)

    def add_common(p, with_organs=False, cloud=False):
        p.add_argument("stage")
        if with_organs:
            p.add_argument("--with", dest="with_", default="", help="organs to grow too: wazuh,misp,thehive or all")
        if cloud:
            p.add_argument("--apply", action="store_true", help="actually create/change cloud resources (default: plan only)")
            p.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
            p.add_argument("--size", default=None, choices=["small", "medium", "large"])
        return p

    add_common(sub.add_parser("soil", help="preflight: is the soil ready for this stage?"), with_organs=True).set_defaults(fn=cmd_soil)
    g = add_common(sub.add_parser("grow", help="wake a stage from the genome"), with_organs=True, cloud=True)
    g.add_argument("--gitops", action="store_true", help="burrow: also install Argo CD and the root app")
    g.set_defaults(fn=cmd_grow)
    h = add_common(sub.add_parser("hibernate", help="put a stage to sleep; data is kept"), cloud=True)
    h.add_argument("--no-backup", action="store_true")
    h.set_defaults(fn=cmd_hibernate)
    add_common(sub.add_parser("prune", help="destroy a stage and its data (typed confirmation)"), cloud=True).set_defaults(fn=cmd_prune)
    s = add_common(sub.add_parser("scale", help="vertical scale for a cloud stage"), cloud=True)
    s.add_argument("newsize", choices=["small", "medium", "large"])
    s.set_defaults(fn=cmd_scale)
    r = sub.add_parser("rhythm", help="nightly sleep / morning wake for sprout")
    r.add_argument("mode", choices=["on", "off", "status"])
    r.add_argument("--sleep", default="23:30")
    r.add_argument("--wake", default="06:30")
    r.set_defaults(fn=cmd_rhythm)
    t = sub.add_parser("tenant", help="forest stage: add / list / remove tenant cells")
    t.add_argument("action", choices=["add", "list", "remove"])
    t.add_argument("id", nargs="?")
    t.add_argument("--name", default="")
    t.add_argument("--tier", default="small", choices=["small", "medium", "large"])
    t.add_argument("--group", default="")
    t.set_defaults(fn=cmd_tenant)
    og = sub.add_parser("organ", help="grow / sleep one upstream organ directly")
    og.add_argument("name")
    og.add_argument("action", choices=["up", "stop", "status", "down"])
    og.set_defaults(fn=cmd_organ)
    b = sub.add_parser("burrow", help="the burrow twin: status | power (rehearse a mains failure)")
    b.add_argument("action", choices=["status", "power"])
    b.set_defaults(fn=cmd_burrow)
    sp = sub.add_parser("spore", help="write the installer for one real machine of the burrow")
    sp.add_argument("role", choices=["server", "agent"])
    sp.add_argument("--name", required=True)
    sp.add_argument("--join", default="", help="https://<server>:6443 (required for agents; a 2nd/3rd server joins the first)")
    sp.add_argument("--gpu", action="store_true")
    sp.add_argument("--ups", action="store_true", help="install NUT and the power-loss reflex hook")
    sp.add_argument("--gitops", action="store_true", help="first server only: install Argo CD + root app")
    sp.add_argument("--repo", default=bw.DEFAULT_REPO)
    sp.set_defaults(fn=cmd_spore)
    rg = sub.add_parser("range", help="dormant Active Directory practice lab (GOAD): soil | plan | install | wake | hibernate | snapshot | reset | status | prune")
    rg.add_argument("action", choices=["soil", "plan", "fetch", "install", "wake", "hibernate", "restart", "snapshot", "reset", "status", "prune"])
    rg.add_argument("--lab", default="", help="MINILAB | GOAD-Light | SCCM | GOAD (default: the biggest that fits this machine)")
    rg.add_argument("--provider", default="", help="virtualbox | vmware | proxmox | ludus | aws | azure (default virtualbox)")
    rg.add_argument("--i-accept-cloud-cost", action="store_true", dest="i_accept_cloud_cost")
    rg.add_argument("--yes", action="store_true")
    rg.add_argument("--force", action="store_true", help="install a lab that does not fit in RAM")
    rg.set_defaults(fn=cmd_range)
    oc = sub.add_parser("organ-check", help="fetch + prepare + compose-config the pinned upstream organs (no images pulled)")
    oc.add_argument("names", nargs="*")
    oc.set_defaults(fn=cmd_organ_check)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
