"""A web page from another site cannot use the gateway through your browser (doc 87). CORS only hides the answer; a simple POST
was still sent and spent your AI allowance. Command-line clients send no Origin and are unaffected; your own pages still work."""
from app.main import app
from fastapi.testclient import TestClient

c = TestClient(app)
BODY = '{"text": "hello"}'


def post(headers):
    return c.post("/v1/guardrails/inspect", content=BODY, headers={"Content-Type": "text/plain", **headers})


def test_a_foreign_page_is_refused_and_counted():
    for origin in ("https://evil.example", "null", "https://securax.localhost.evil.example", "ftp://localhost"):
        r = post({"Origin": origin})
        assert r.status_code == 403 and r.json()["error"]["type"] == "cross_site_refused", origin


def test_clients_without_origin_and_the_estates_own_pages_still_work(monkeypatch):
    monkeypatch.setenv("SECURAX_DOMAIN", "securax.localhost")
    assert post({}).status_code != 403                                                  # curl, Python, n8n: no Origin
    for origin in ("http://localhost:8088", "http://127.0.0.1:3000", "https://hub.securax.localhost"):
        assert post({"Origin": origin}).status_code != 403, origin
    # through the estate's front door, same origin: the online hub and a Tailscale name
    assert post({"Origin": "https://hub.example.invalid", "X-Forwarded-Host": "hub.example.invalid"}).status_code != 403
    assert post({"Origin": "https://laptop.tail1234.ts.net", "X-Forwarded-Host": "laptop.tail1234.ts.net"}).status_code != 403
    assert post({"Origin": "https://evil.example", "X-Forwarded-Host": "hub.example.invalid"}).status_code == 403


def test_reads_are_not_affected():
    assert c.get("/healthz", headers={"Origin": "https://evil.example"}).status_code == 200
