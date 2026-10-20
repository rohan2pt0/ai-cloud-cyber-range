"""Every service in the estate refuses privilege gain through setuid programs, and none runs an image that changes under you
(doc 87). A new service that forgets either fails here, not in production."""
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]


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
