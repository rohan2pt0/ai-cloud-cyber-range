"""Every service in the estate refuses privilege gain through setuid programs, and none runs an image that changes under you
(doc 87). A new service that forgets either fails here, not in production. The services other devices or the internet can reach
are also pinned by digest; their list lives in local/compose/digest-pins.json."""
import json
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
COMPOSE = ROOT / "local/compose"
PINNED = re.compile(r"^[^@\s]+:[^@\s]+@sha256:[0-9a-f]{64}$")   # name:tag@sha256:<64 hex> (the tag stays, for readers)


class _ComposeLoader(yaml.SafeLoader):
    """Safe YAML plus Compose's own merge tags (`!override`, `!reset`), read as the plain value they carry."""


for _tag in ("!override", "!reset"):
    _ComposeLoader.add_constructor(_tag, lambda loader, node: loader.construct_sequence(node) if isinstance(node, yaml.SequenceNode)
                                   else loader.construct_mapping(node) if isinstance(node, yaml.MappingNode) else loader.construct_scalar(node))


def _services(fname):
    return yaml.load((COMPOSE / fname).read_text(), Loader=_ComposeLoader)["services"]   # noqa: S506 (a SafeLoader subclass)


def _digest_pins():
    return json.loads((COMPOSE / "digest-pins.json").read_text())["files"]


def test_internet_and_device_facing_images_are_pinned_by_digest():
    pins = _digest_pins()
    assert pins, "digest-pins.json lists no services"
    for fname, names in pins.items():
        services = _services(fname)
        for name in names:
            assert name in services, f"{fname}: {name} is listed in digest-pins.json but is not a service any more"
            image = str(services[name].get("image", ""))
            assert PINNED.match(image), f"{fname}: {name} image {image!r} must be name:tag@sha256:<digest> (doc 87)"


def test_every_service_published_beyond_loopback_is_digest_pinned():
    # A new service that takes BIND_HOST (other devices can reach it) must join the digest list, not slip past it.
    pins = _digest_pins()
    for fname in ("docker-compose.yml", "tls.yml", "stage-sprout.yml"):
        services = _services(fname)
        for name, svc in services.items():
            if "build" in svc or "image" not in svc:
                continue                                    # our own images are built here (Dependabot keeps their base images current)
            if any("BIND_HOST" in str(p) for p in svc.get("ports") or []):
                assert name in pins.get(fname, {}), f"{fname}: {name} is published on BIND_HOST; add it to digest-pins.json"


def test_the_digest_pin_check_refuses_a_bare_tag():
    assert PINNED.match("nginx:1.30-alpine@sha256:" + "a" * 64)
    assert not PINNED.match("nginx:1.30-alpine")
    assert not PINNED.match("nginx@sha256:" + "a" * 64)            # the tag must stay, so a reader knows the version
    assert not PINNED.match("nginx:1.30-alpine@sha256:" + "a" * 63)


def test_every_service_sets_no_new_privileges_and_no_image_is_latest():
    files = [ROOT / "local/compose/docker-compose.yml"]
    for f in files:
        services = yaml.safe_load(f.read_text())["services"]
        for name, svc in services.items():
            assert any("no-new-privileges" in x for x in svc.get("security_opt", [])), f"{f.name}: {name} lacks no-new-privileges"
            image = str(svc.get("image", ""))
            assert not image.endswith(":latest") and (":" in image.split("/")[-1] or "build" in svc), f"{f.name}: {name} image {image!r}"


def test_only_the_scanner_touches_the_docker_socket_and_it_does_not_stay_running():
    services = yaml.safe_load((ROOT / "local/compose/docker-compose.yml").read_text())["services"]
    holders = [n for n, s in services.items() if any("docker.sock" in str(v) for v in s.get("volumes", []))]
    assert holders == ["trivy"], holders
    t = services["trivy"]
    assert t.get("restart") == "no" and "sleep infinity" not in " ".join(t.get("entrypoint", []))


def test_the_estate_runs_one_nginx_line():
    # The Command Center's web server stayed on nginx 1.27 while the edge moved to 1.30, so the cockpit's "oldest running
    # software" stayed red for a year-old image. One line for every nginx: raising one raises all.
    found = {}
    for f in sorted(COMPOSE.glob("*.yml")):
        for m in re.finditer(r"image:\s*nginx:([^@\s]+)", f.read_text()):
            found.setdefault(m.group(1), []).append(f.name)
    assert len(found) == 1, f"more than one nginx line in the estate: {found}"
