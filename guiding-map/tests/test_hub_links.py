"""The Command Center's cards must point somewhere the CURRENT device can reach: plain ports on localhost, per-service names behind the
TLS edge, and the laptop's own Tailscale name (doc 58) on a phone. A ts.net visit used to get https://chat.securax.localhost/ links."""
import json
import pathlib
import re
import shutil
import subprocess

import pytest

HUB = pathlib.Path(__file__).resolve().parent.parent / "hub.html"
STUB = r"""
const els = {}, cards = [], fetched = [];
function el(id){ return els[id] || (els[id] = {id, textContent:"", innerHTML:"", appendChild(c){ cards.push(c); }}); }
global.location = LOC;
global.document = {getElementById: el, querySelector(){ return null; }, createElement(){ return {}; }};
global.fetch = (u) => { fetched.push(u); return new Promise(()=>{}); };
global.setInterval = () => 0;
eval(SCRIPT);
console.log(JSON.stringify({links: cards.map(c => c.href), fetched}));
"""


def run(protocol: str, hostname: str) -> dict:
    script = re.findall(r"<script>(.*?)</script>", HUB.read_text(encoding="utf-8"), re.S)[-1]
    js = STUB.replace("LOC", json.dumps({"protocol": protocol, "hostname": hostname})).replace("SCRIPT", json.dumps(script))
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=30, check=True)
    return json.loads(out.stdout)


pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="node not installed")


def test_tailscale_visit_links_to_the_same_name_and_hides_unpublished_services():
    r = run("https:", "rc.tail678ad5.ts.net")
    assert r["links"][:2] == ["https://rc.tail678ad5.ts.net/", "https://rc.tail678ad5.ts.net:10000/"]
    assert not any("securax.localhost" in u or ":3001" in u or ":5678" in u for u in r["links"])
    assert "/healthz" in r["fetched"] and "/version" in r["fetched"]        # gateway rides the same origin


def test_localhost_keeps_plain_ports():
    r = run("http:", "localhost")
    assert "http://localhost:3000/" in r["links"] and "http://localhost:8080/healthz" in r["fetched"]


def test_tls_edge_keeps_service_names():
    r = run("https:", "hub.securax.localhost")
    assert "https://chat.securax.localhost/" in r["links"] and "https://api.securax.localhost/healthz" in r["fetched"]
