"""Compose sanity gate (Poka-yoke) — catch deploy-blocking blunders in CI, no Docker needed.

The one that took the estate down on Docker Desktop / WSL2: a bind mount nested *inside*
another read-only bind mount (Docker can't create the mountpoint on a read-only fs). This test
fails the build if any service mounts one host path at a target that lives inside another of its
own mount targets, and checks a few other "won't start" footguns.
"""
import pathlib
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
