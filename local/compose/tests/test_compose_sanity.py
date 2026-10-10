"""Compose sanity gate (Poka-yoke) — catch deploy-blocking blunders in CI, no Docker needed.

The one that took the estate down on Docker Desktop / WSL2: a bind mount nested *inside*
another read-only bind mount (Docker can't create the mountpoint on a read-only fs). This test
fails the build if any service mounts one host path at a target that lives inside another of its
own mount targets, and checks a few other "won't start" footguns.
"""
import pathlib
import re

import yaml

COMPOSE = pathlib.Path(__file__).resolve().parents[1] / "docker-compose.yml"


def _targets(volumes):
    """Return the in-container target path of each short-form bind/volume mount."""
    out = []
    for v in volumes or []:
        if isinstance(v, str):
            parts = v.split(":")
            if len(parts) >= 2:
                out.append(parts[1])
        elif isinstance(v, dict) and v.get("target"):
            out.append(v["target"])
    return out


def test_no_nested_bind_mounts():
    data = yaml.safe_load(COMPOSE.read_text())
    offenders = []
    for name, svc in (data.get("services") or {}).items():
        targets = _targets(svc.get("volumes"))
        for a in targets:
            for b in targets:
                if a != b and b.rstrip("/").startswith(a.rstrip("/") + "/"):
                    offenders.append(f"{name}: '{b}' is nested inside mount '{a}'")
    assert not offenders, (
        "Nested bind mounts fail on Docker Desktop/WSL2 (read-only mountpoint). "
        "Mount at a sibling path and alias in the server config instead:\n  " + "\n  ".join(offenders))


def test_guiding_map_serves_portal_without_nesting():
    data = yaml.safe_load(COMPOSE.read_text())
    gm = data["services"]["guiding-map"]
    targets = _targets(gm.get("volumes"))
    assert "/srv/portal" in targets, "portal must be mounted at a sibling path, not inside the html mount"
    assert any("default.conf" in t for t in targets), "guiding-map needs the nginx alias config mounted"


def test_build_fields_are_strings_or_mappings():
    # Docker refuses `build:` that is neither a string path nor a mapping (a real error the user hit).
    data = yaml.safe_load(COMPOSE.read_text())
    for name, svc in (data.get("services") or {}).items():
        if "build" in svc:
            assert isinstance(svc["build"], (str, dict)), f"{name}.build must be a string or mapping"


def test_optional_feature_envs_never_block_startup():
    """An OPTIONAL service must not use a mandatory `${VAR:?...}` env: one missing value in a
    user's old .env would make `compose up` fail for the WHOLE stack. Optional features must
    degrade (fail-closed in the service), not refuse to start. Core secrets may stay mandatory."""
    raw = COMPOSE.read_text()
    core_required = {"POSTGRES_PASSWORD", "GRAFANA_PASSWORD", "MM_DB_PASSWORD"}
    offenders = re.findall(r"\$\{([A-Z0-9_]+):\?", raw)
    bad = [v for v in offenders if v not in core_required]
    assert not bad, f"optional-feature envs must use ':-' not ':?' (would block the stack): {bad}"


# Debian/Ubuntu base images (python:*-slim etc.) ship these system accounts already;
# `useradd <name>` on one fails with "user already exists" (exit 9) and breaks the image
# build. The real one that bit us: a service user literally named `sync`.
_RESERVED_SYSTEM_USERS = {
    "root", "daemon", "bin", "sys", "sync", "games", "man", "lp", "mail", "news",
    "uucp", "proxy", "www-data", "backup", "list", "irc", "gnats", "nobody",
    "messagebus", "sshd", "operator", "ftp", "systemd-network",
}


def test_dockerfiles_dont_reuse_reserved_system_users():
    repo = pathlib.Path(__file__).resolve().parents[3]
    offenders = []
    for df in repo.rglob("Dockerfile"):
        if "node_modules" in df.parts:
            continue
        for ln in df.read_text().splitlines():
            if "useradd" not in ln:
                continue
            # The username is the last bare (non-flag, non-value) token on the line.
            head = ln.split("&&")[0].replace("\\", "")
            toks = [t for t in re.split(r"\s+", head.strip()) if t and not t.startswith("-")]
            name = toks[-1] if toks else ""
            if name in _RESERVED_SYSTEM_USERS:
                offenders.append(f"{df.relative_to(repo)}: useradd '{name}' collides with a base-image system account")
    assert not offenders, "rename the service user (build fails with 'already exists'):\n  " + "\n  ".join(offenders)
