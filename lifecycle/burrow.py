#!/usr/bin/env python3
"""The BURROW — stage 2a: your own hardware running k3s, rehearsed first on a Docker twin.

Nature's pattern: an animal digs the burrow before it needs it, and it is the same burrow in every season.
  * burrow.json is the single definition. The REAL machines (./securax spore) and the TWIN (this file) both read it.
  * The twin is 1 server + 2 agents as privileged containers running the real k3s. It proves, with no hardware:
    the nodes join, a GPU-labelled workload lands only on the GPU node, a power cut drains and snapshots,
    hibernation keeps the cluster's memory, and waking restores it.
  * Hardware is a SPORE: a cloud-init file or a shell script that turns a fresh Ubuntu box into a node.

Standard library only. Imported by lifecycle.py; its output (kubeconfig, token) lives in ~/.securax/burrow.
"""
from __future__ import annotations

import json
import os
import secrets
import shlex
import subprocess
import textwrap
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HOME_DIR = os.environ.get("SECURAX_HOME_DIR") or os.path.join(os.path.expanduser("~"), ".securax")
BURROW_DIR = os.path.join(HOME_DIR, "burrow")
PREFIX = "securax-burrow"
NETWORK = f"{PREFIX}-net"
DEFAULT_REPO = "https://github.com/rohan2pt0/ai-cloud-cyber-range.git"


def cfg() -> dict:
    with open(os.path.join(HERE, "burrow.json"), encoding="utf-8") as f:
        return json.load(f)


def say(msg: str = "") -> None:
    print(msg, flush=True)


def sh(argv: list[str], inp: str | None = None, timeout: int | None = 120) -> tuple[int, str]:
    try:
        p = subprocess.run(argv, input=inp, text=True, timeout=timeout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        return 127, f"{argv[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, "timed out"
    return p.returncode, p.stdout or ""


def write_private(path: str, text: str, mode: int = 0o600) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.chmod(path, mode)


def token() -> str:
    """The cluster join token: random, generated once, owner-only. Nodes (real or twin) need it to join."""
    path = os.path.join(BURROW_DIR, "token")
    if not os.path.exists(path):
        write_private(path, secrets.token_urlsafe(32))
    return open(path, encoding="utf-8").read().strip()


# ───────────────────────────────────────────── rendered scripts (shared by hardware and twin) ─────────────────────────────────────────────
def power_hook() -> str:
    """POSIX sh run by the UPS monitor when mains power fails and the battery is low (and by the twin to rehearse it).
    Graceful drain → etcd snapshot → stop. Never fails the shutdown: every step is best-effort."""
    p = cfg()["power"]
    return textwrap.dedent(f"""\
        #!/bin/sh
        # securax-power-hibernate: the burrow's reflex when the lights go out.
        K="${{SECURAX_KUBECTL:-k3s kubectl}}"
        log() {{ echo "[securax-power] $*"; }}
        log "mains lost: draining workloads so nothing is cut mid-write"
        ME="node/$(hostname)"
        for n in $($K get nodes -o name 2>/dev/null | grep -vx "$ME"); do
          $K drain "$n" --ignore-daemonsets --delete-emptydir-data --force --timeout={p['drain_timeout']} || true
        done
        $K drain "$ME" --ignore-daemonsets --delete-emptydir-data --force --timeout={p['drain_timeout']} || true
        log "snapshotting the cluster's memory (etcd)"
        ${{SECURAX_K3S:-k3s}} etcd-snapshot save --name {p['snapshot_name']} || log "snapshot skipped (not a server node)"
        log "stopping k3s"
        ${{SECURAX_POWER_FINAL:-systemctl stop k3s}} || true
        """)


def k3s_flags(role: str, gpu: bool, join_url: str = "") -> list[str]:
    """The flags a node starts k3s with. THE one place both the hardware installer and the twin take them from."""
    c = cfg()
    flags = list(c["server_args"] if role == "server" else c["agent_args"])
    if role == "server" and join_url:
        flags = [f for f in flags if f != "--cluster-init"] + ["--server", join_url]
    if gpu:
        flags += ["--node-label", c["gpu_label"]]
    return flags


def install_script(role: str, name: str, join_url: str = "", gpu: bool = False, ups: bool = False, gitops: bool = False,
                   repo: str = DEFAULT_REPO, tok: str | None = None) -> str:
    """The spore: a bash script that turns a fresh Ubuntu/Debian machine into a burrow node. Idempotent."""
    if role not in ("server", "agent"):
        raise ValueError("role must be server or agent")
    if role == "agent" and not join_url:
        raise ValueError("an agent needs --join https://<server>:6443")
    c = cfg()
    flags = " ".join(shlex.quote(f) for f in k3s_flags(role, gpu, join_url if role == "server" else ""))
    exec_role = "server" if role == "server" else "agent"
    url_env = f"K3S_URL={shlex.quote(join_url)} " if role == "agent" else ""
    hook = power_hook().replace("'", "'\\''")
    lines = [
        "#!/usr/bin/env bash",
        f"# SecuRAX burrow node '{name}' ({role}) — generated by ./securax spore. Safe to run twice.",
        "set -euo pipefail",
        'if [ "$(id -u)" != 0 ]; then echo "run as root: sudo bash $0"; exit 1; fi',
        "export DEBIAN_FRONTEND=noninteractive",
        f"hostnamectl set-hostname {shlex.quote(name)} || true",
        "apt-get update -qq && apt-get install -y -qq curl ca-certificates" + (" nut" if ups else ""),
        "",
        "# 1. the reflex for power loss",
        "mkdir -p /usr/local/sbin /etc/securax",
        f"printf '%s\\n' '{hook}' > /usr/local/sbin/securax-power-hibernate",
        "chmod 0755 /usr/local/sbin/securax-power-hibernate",
    ]
    if ups:
        lines += [
            "cat > /etc/securax/upsmon.snippet <<'EOF'",
            "# Merge into /etc/nut/upsmon.conf after your UPS driver works (see: upsc <ups>@localhost):",
            'SHUTDOWNCMD "/usr/local/sbin/securax-power-hibernate"',
            "EOF",
            'echo "UPS: finish NUT setup (nut-scanner -U), then merge /etc/securax/upsmon.snippet — untested without your UPS model."',
        ]
    if gpu:
        lines += [
            "",
            "# 2. GPU: the node is labelled, but the driver and container toolkit are YOUR choice (they depend on the card).",
            'command -v nvidia-smi >/dev/null || echo "! no NVIDIA driver yet: install it, then: sudo systemctl restart k3s-agent k3s"',
        ]
    lines += [
        "",
        f"# {'3' if gpu else '2'}. k3s, pinned",
        "if ! command -v k3s >/dev/null 2>&1; then",
        "  K3S_INSTALLER=$(mktemp)",
        f"  curl -fsSL {shlex.quote(c['k3s_installer']['url'])} -o \"$K3S_INSTALLER\"",
        f"  echo {shlex.quote(c['k3s_installer']['sha256'] + '  ')}\"$K3S_INSTALLER\" | sha256sum -c - >/dev/null || {{ echo 'k3s installer does not match its pinned hash: refusing to run it'; exit 1; }}",
        f"  INSTALL_K3S_VERSION={shlex.quote(c['k3s_version'])} K3S_TOKEN={shlex.quote(tok or token())} {url_env}\\",
        f"    sh \"$K3S_INSTALLER\" {exec_role} --node-name {shlex.quote(name)} {flags}",
        "  rm -f \"$K3S_INSTALLER\"",
        "fi",
        f"systemctl enable --now {'k3s' if role == 'server' else 'k3s-agent'}",
    ]
    if gitops and role == "server" and not join_url:
        lines += [
            "",
            "# GitOps: Argo CD pulls the platform from git, exactly as on the tree and canopy stages.",
            "export KUBECONFIG=/etc/rancher/k3s/k3s.yaml",
            "for i in $(seq 1 60); do k3s kubectl get nodes >/dev/null 2>&1 && break; sleep 5; done",
            "k3s kubectl create namespace argocd --dry-run=client -o yaml | k3s kubectl apply -f -",
            "k3s kubectl apply --server-side -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.5/manifests/install.yaml",
            "cat <<'EOF' | k3s kubectl apply -f -",
            "apiVersion: argoproj.io/v1alpha1",
            "kind: Application",
            "metadata: { name: securax-root, namespace: argocd }",
            "spec:",
            "  project: default",
            f"  source: {{ repoURL: {repo}, targetRevision: main, path: gitops/bootstrap }}",
            "  destination: { server: https://kubernetes.default.svc, namespace: argocd }",
            "  syncPolicy: { automated: { prune: true, selfHeal: true } }",
            "EOF",
        ]
    lines += ["", f'echo "node {name} is up. {"Join more nodes with: https://<this-ip>:6443 and the token in ~/.securax/burrow/token" if role == "server" else "It joins the cluster in a minute."}"', ""]
    return "\n".join(lines)


def cloud_init(script: str, name: str) -> str:
    """Wrap the installer in cloud-init user-data (Ubuntu autoinstall / NoCloud USB seed / any cloud)."""
    body = textwrap.indent(script, "      ")
    return ("#cloud-config\n"
            f"hostname: {name}\n"
            "write_files:\n"
            "  - path: /usr/local/sbin/securax-install-node\n"
            "    permissions: '0700'\n"
            "    content: |\n"
            f"{body}\n"
            "runcmd:\n"
            "  - [ /usr/local/sbin/securax-install-node ]\n")


def write_spore(role: str, name: str, **kw) -> tuple[str, str]:
    script = install_script(role, name, **kw)
    d = os.path.join(BURROW_DIR, "spore")
    sp, ci = os.path.join(d, f"{name}.install.sh"), os.path.join(d, f"{name}.user-data")
    write_private(sp, script, 0o700)
    write_private(ci, cloud_init(script, name), 0o600)
    return sp, ci


# ───────────────────────────────────────────── the twin ─────────────────────────────────────────────
def twin_nodes() -> list[dict]:
    return cfg()["twin"]["nodes"]


def cname(node: str) -> str:
    return f"{PREFIX}-{node}"


def server_name() -> str:
    return cname(next(n["name"] for n in twin_nodes() if n["role"] == "server"))


def container_state(name: str) -> str:
    rc, out = sh(["docker", "inspect", "-f", "{{.State.Running}}", name], timeout=30)
    return "missing" if rc != 0 else ("running" if out.strip() == "true" else "stopped")


def twin_status() -> str:
    """dormant (nothing exists) | hibernating (containers stopped, cluster memory kept) | partial | awake"""
    states = [container_state(cname(n["name"])) for n in twin_nodes()]
    if all(s == "missing" for s in states):
        return "dormant"
    if all(s == "running" for s in states):
        return "awake"
    if all(s in ("stopped", "missing") for s in states):
        return "hibernating"
    return "partial"


def kubectl(*args: str, inp: str | None = None, timeout: int = 60) -> tuple[int, str]:
    argv = ["docker", "exec", *(["-i"] if inp is not None else []), server_name(), "kubectl", *args]
    return sh(argv, inp=inp, timeout=timeout)


def nodes() -> dict[str, dict]:
    """name → {ready, labels}. Empty while the API is not up yet."""
    rc, out = kubectl("get", "nodes", "-o", "json")
    if rc != 0:
        return {}
    try:
        items = json.loads(out)["items"]
    except (ValueError, KeyError):
        return {}
    res = {}
    for it in items:
        conds = {c["type"]: c["status"] for c in it["status"].get("conditions", [])}
        res[it["metadata"]["name"]] = {"ready": conds.get("Ready") == "True", "labels": it["metadata"].get("labels", {}),
                                       "unschedulable": bool(it["spec"].get("unschedulable"))}
    return res


def wait(pred, seconds: int, what: str) -> bool:
    end = time.time() + float(os.environ.get("SECURAX_BURROW_WAIT", seconds))
    while time.time() < end:
        if pred():
            return True
        time.sleep(3)
    say(f"  ! timed out waiting for {what}")
    return False


def host_ca_bundle() -> str:
    """The CA bundle the nodes should trust: yours first, then the host's. Behind a TLS-inspecting proxy (common in banks
    and corporate networks) containerd cannot pull images unless it trusts the proxy's CA — the same fix real nodes need."""
    for cand in (os.environ.get("SECURAX_BURROW_CA"), os.environ.get("SSL_CERT_FILE"), "/etc/ssl/certs/ca-certificates.crt"):
        if cand and os.path.isfile(cand):
            return cand
    return ""


def _create(node: dict) -> int:
    c = cfg()
    name = cname(node["name"])
    argv = ["docker", "run", "-d", "--name", name, "--hostname", node["name"], "--privileged", "--network", NETWORK,
            "--tmpfs", "/run", "--tmpfs", "/var/run", "-v", f"{name}:/var/lib/rancher/k3s", "-e", f"K3S_TOKEN={token()}",
            "--label", "securax.burrow=twin"]
    ca = host_ca_bundle()
    if ca:
        argv += ["-v", f"{os.path.abspath(ca)}:/etc/ssl/certs/ca-certificates.crt:ro"]
    if node["role"] == "server":
        argv += ["-p", f"127.0.0.1:{c['twin']['api_host_port']}:6443"]
        flags = k3s_flags("server", node.get("gpu", False)) + c["twin"]["extra_args"] + ["--tls-san", "127.0.0.1", "--node-name", node["name"]]
        argv += [c["image"], "server", *flags]
    else:
        argv += ["-e", f"K3S_URL=https://{server_name()}:6443"]
        argv += [c["image"], "agent", "--node-name", node["name"], *c["twin"]["extra_args"], *k3s_flags("agent", node.get("gpu", False))]
    rc, out = sh(argv, timeout=600)
    if rc != 0:
        say(out[-600:])
    return rc


def export_kubeconfig() -> str:
    rc, out = sh(["docker", "exec", server_name(), "cat", "/etc/rancher/k3s/k3s.yaml"], timeout=30)
    if rc != 0:
        return ""
    port = cfg()["twin"]["api_host_port"]
    path = os.path.join(BURROW_DIR, "kubeconfig")
    write_private(path, out.replace("https://127.0.0.1:6443", f"https://127.0.0.1:{port}").replace("default", "securax-burrow-twin"))
    return path


def twin_up(gitops: bool = False) -> int:
    """Create (first time) or wake (later) the twin. Safe to run repeatedly."""
    if sh(["docker", "info"], timeout=30)[0] != 0:
        say("Docker is not running. Start Docker Desktop (or the docker service) and retry.")
        return 1
    sh(["docker", "network", "create", NETWORK], timeout=30)
    first = twin_status() == "dormant"
    order = sorted(twin_nodes(), key=lambda n: n["role"] != "server")           # server first, then agents
    say(f"{'Digging' if first else 'Waking'} the burrow twin ({len(order)} nodes, real k3s {cfg()['k3s_version']}) …")
    for node in order:
        st = container_state(cname(node["name"]))
        rc = _create(node) if st == "missing" else (0 if st == "running" else sh(["docker", "start", cname(node["name"])])[0])
        if rc != 0:
            return rc
        if node["role"] == "server" and not wait(lambda: kubectl("get", "--raw", "/readyz")[0] == 0, 180, "the API server"):
            return 1
    want = {n["name"] for n in twin_nodes()}
    if not wait(lambda: want <= {k for k, v in nodes().items() if v["ready"]}, 240, "all nodes Ready"):
        return 1
    for n in nodes():                                                           # undo the power-event cordon, if any
        kubectl("uncordon", n)
    kc = export_kubeconfig()
    say(f"  {len(want)} nodes Ready. kubeconfig: {kc}   (KUBECONFIG={kc} kubectl get nodes)")
    if gitops:
        return twin_gitops()
    return 0


def twin_gitops() -> int:
    """Hand the twin to GitOps exactly as the tree/canopy stages do: Argo CD + the root app."""
    argocd = os.environ.get("SECURAX_ARGOCD_VERSION", "v3.5.5")
    kubectl("create", "namespace", "argocd")
    rc, out = kubectl("apply", "--server-side", "-n", "argocd", "-f",
                      f"https://raw.githubusercontent.com/argoproj/argo-cd/{argocd}/manifests/install.yaml", timeout=600)
    if rc != 0:
        say("! could not install Argo CD (needs internet from the node):\n" + out[-400:])
        return rc
    root = open(os.path.join(HERE, "..", "gitops", "root-app.yaml"), encoding="utf-8").read()
    rc, out = kubectl("apply", "-f", "-", inp=root)
    say("  Argo CD installed; root app applied: the platform now grows itself from git.")
    return rc


def power_event() -> int:
    """Rehearse a mains failure: run the SAME reflex the real nodes get, inside the server container."""
    say("Power event: drain → snapshot → stop (the same script the UPS runs on hardware) …")
    rc, out = sh(["docker", "exec", "-e", "SECURAX_POWER_FINAL=true", "-e", "SECURAX_KUBECTL=kubectl", server_name(), "sh", "-c", power_hook()],
                 timeout=300)
    say(textwrap.indent(out.strip(), "  "))
    return rc


def snapshots() -> list[str]:
    rc, out = sh(["docker", "exec", server_name(), "ls", "/var/lib/rancher/k3s/server/db/snapshots"], timeout=30)
    return out.split() if rc == 0 else []


def newest_snapshot() -> str:
    """Name of the newest etcd snapshot in the server's volume (works while the twin is stopped: reads the volume, not the container)."""
    rc, out = sh(["docker", "run", "--rm", "-v", f"{server_name()}:/v:ro", "--entrypoint", "ls", cfg()["image"], "-t", "/v/server/db/snapshots"], timeout=120)
    names = [n for n in out.split() if n] if rc == 0 else []
    return names[0] if names else ""


def twin_restore(snapshot: str = "") -> int:
    """DISASTER RECOVERY: rewind the control plane to an etcd snapshot (default: the newest). Every node must be stopped first.
    Runs `k3s server --cluster-reset` in a throwaway container that shares the server's data volume; ~10 s on the twin."""
    snapshot = snapshot or newest_snapshot()
    if not snapshot:
        say("There is no etcd snapshot to restore from (take one: ./securax burrow power, or hibernate the burrow).")
        return 1
    if any(container_state(cname(n["name"])) == "running" for n in twin_nodes()):
        say("Stop the burrow first (./securax hibernate burrow): a cluster cannot be rewound while its nodes are running.")
        return 1
    c = cfg()
    node = next(n["name"] for n in twin_nodes() if n["role"] == "server")
    say(f"Restoring the control plane from snapshot {snapshot} …")
    rc, out = sh(["docker", "run", "--rm", "--privileged", "--network", NETWORK, "-e", f"K3S_TOKEN={token()}", "-v", f"{server_name()}:/var/lib/rancher/k3s",
                  "--tmpfs", "/run", "--tmpfs", "/var/run", c["image"], "server", "--cluster-reset",
                  f"--cluster-reset-restore-path=/var/lib/rancher/k3s/server/db/snapshots/{snapshot}", "--node-name", node, "--secrets-encryption"], timeout=600)
    ok = "has been reset" in out
    say("  restored." if ok else "  restore FAILED:\n" + out[-600:])
    return 0 if ok else 1


def twin_stop(power: bool = True) -> int:
    """Hibernate: the reflex first (drain + snapshot), then stop every node. Volumes — the cluster's memory — stay."""
    if twin_status() == "dormant":
        say("The burrow twin is dormant (never dug).")
        return 0
    if power and container_state(server_name()) == "running":
        power_event()
    for node in sorted(twin_nodes(), key=lambda n: n["role"] == "server"):      # agents first, server last
        sh(["docker", "stop", "-t", "20", cname(node["name"])], timeout=120)
    say("The burrow twin is hibernating. Wake it with  ./securax grow burrow")
    return 0


def twin_down() -> int:
    """Apoptosis: remove containers, volumes, network and the join token."""
    for node in twin_nodes():
        sh(["docker", "rm", "-f", cname(node["name"])], timeout=60)
        sh(["docker", "volume", "rm", "-f", cname(node["name"])], timeout=60)
    sh(["docker", "network", "rm", NETWORK], timeout=30)
    for f in ("token", "kubeconfig"):
        try:
            os.remove(os.path.join(BURROW_DIR, f))
        except OSError:
            pass
    say("The burrow twin was removed (containers, volumes, token).")
    return 0


def twin_report() -> int:
    st = twin_status()
    say(f"burrow twin: {st}")
    if st == "awake":
        for n, v in sorted(nodes().items()):
            gpu = " · GPU" if cfg()["gpu_label"] in [f"{k}={x}" for k, x in v["labels"].items()] else ""
            say(f"  {'●' if v['ready'] else '○'} {n:<8} {'Ready' if v['ready'] else 'NotReady'}{' (cordoned)' if v['unschedulable'] else ''}{gpu}")
        snaps = snapshots()
        say(f"  etcd snapshots: {len(snaps)}")
    return 0
