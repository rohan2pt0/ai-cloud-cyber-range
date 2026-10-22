"""tools/digest_check.py (doc 87): every digest pin is found, a tag that moved is reported and can be rewritten in
place, the registry's own token challenge is followed, a rate limit is waited out, and no network is used here."""
import email.message
import importlib.util
import io
import pathlib
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("securax_digest_check", ROOT / "tools" / "digest_check.py")
dc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dc)


class Resp(io.BytesIO):
    def __init__(self, body=b"", headers=None):
        super().__init__(body)
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def http_error(code, headers):
    h = email.message.Message()
    for k, v in headers.items():
        h[k] = v
    return urllib.error.HTTPError("u", code, "x", h, None)


def test_every_pinned_service_is_found_with_its_tag_and_digest():
    rows = dc.pins()
    assert len(rows) >= 13 and all(r.get("digest", "").startswith("sha256:") and r["tag"] for r in rows), rows


def test_references_split_like_docker_does():
    assert dc.split_ref("nginx") == ("registry-1.docker.io", "library/nginx")
    assert dc.split_ref("prom/prometheus") == ("registry-1.docker.io", "prom/prometheus")
    assert dc.split_ref("ghcr.io/open-webui/open-webui") == ("ghcr.io", "open-webui/open-webui")


def test_the_token_challenge_and_a_rate_limit_are_handled():
    calls, waits = [], []

    def opener(req, timeout=0):
        calls.append((req.get_method(), req.full_url, req.headers.get("Authorization", "")))
        if "token" in req.full_url:
            assert req.full_url.startswith("https://auth.example/token?") and "repository%3Alibrary%2Fnginx%3Apull" in req.full_url
            return Resp(b'{"token":"t1"}')
        if not req.headers.get("Authorization"):
            raise http_error(401, {"WWW-Authenticate": 'Bearer realm="https://auth.example/token",service="reg"'})
        if len([c for c in calls if c[0] == "HEAD"]) == 2:
            raise http_error(429, {"Retry-After": "2"})
        return Resp(headers={"Docker-Content-Digest": "sha256:" + "a" * 64})

    assert dc.current_digest("nginx", "1.30-alpine", opener, sleep=waits.append) == "sha256:" + "a" * 64
    assert waits == [2.0] and calls[-1][2] == "Bearer t1"


def test_a_moved_tag_is_reported_and_rewritten_in_place(tmp_path, monkeypatch):
    comp = tmp_path / "compose"
    comp.mkdir()
    old = "sha256:" + "1" * 64
    (comp / "docker-compose.yml").write_text(f"services:\n  web:\n    restart: always\n    image: nginx:1.30-alpine@{old}\n  other:\n    image: x:1\n")
    (comp / "digest-pins.json").write_text('{"files": {"docker-compose.yml": {"web": "faces devices"}}}')
    monkeypatch.setattr(dc, "COMPOSE", comp)
    new = "sha256:" + "2" * 64
    monkeypatch.setattr(dc, "current_digest", lambda ref, tag, opener=None: new)
    rows = dc.check()
    assert [r["state"] for r in rows] == ["moved"] and rows[0]["now"] == new
    assert dc.write(rows) == 1
    assert f"image: nginx:1.30-alpine@{new}\n" in (comp / "docker-compose.yml").read_text() and "image: x:1" in (comp / "docker-compose.yml").read_text()


def test_an_unreachable_registry_is_reported_not_failed(monkeypatch):
    def boom(ref, tag, opener=None):
        raise OSError("offline")
    monkeypatch.setattr(dc, "current_digest", boom)
    assert {r["state"] for r in dc.check()} == {"could not check"}
