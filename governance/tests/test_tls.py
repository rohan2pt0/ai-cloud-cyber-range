"""Encryption in transit: the CA can only vouch for local/private names, the certificate really verifies, the edge config and the
port table agree, no plain web port is published when the edge is on, and a real TLS handshake enforces modern protocols."""
import importlib.util
import json
import pathlib
import re
import shutil
import socket
import ssl
import subprocess
import sys
import threading

import pytest

G = pathlib.Path(__file__).resolve().parent.parent
ROOT = G.parent
spec = importlib.util.spec_from_file_location("securax_tls", G / "tls.py")
tls = importlib.util.module_from_spec(spec)
sys.modules["securax_tls"] = tls
spec.loader.exec_module(tls)

needs_openssl = pytest.mark.skipif(not shutil.which("openssl"), reason="openssl not installed")


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_TLS_DIR", str(tmp_path / "tls"))
    monkeypatch.setattr(tls, "ENVF", tmp_path / ".env")
    return tmp_path / "tls"


@needs_openssl
def test_issued_certificate_verifies_against_the_ca_and_lists_names(store):
    res = tls.ensure(["100.101.102.103"])
    r = subprocess.run(["openssl", "verify", "-CAfile", str(store / "ca.crt"), str(store / "server.crt")], capture_output=True, text=True)
    assert r.returncode == 0 and "OK" in r.stdout
    assert {"localhost", "127.0.0.1", "100.101.102.103"} <= set(res["cert"]["names"])
    assert 300 < res["cert"]["days_left"] <= 397


@needs_openssl
def test_private_keys_are_owner_only_and_the_ca_key_is_never_world_readable(store):
    tls.ensure()
    for f in ("ca.key", "server.key"):
        assert (store / f).stat().st_mode & 0o077 == 0, f
    assert (store.stat().st_mode & 0o077) == 0


@needs_openssl
def test_ca_is_name_constrained_and_a_public_name_is_refused(store):
    res = tls.ensure(["evil.example.com", "192.168.1.20"])
    assert "evil.example.com" in res["refused"] and "192.168.1.20" in res["cert"]["names"]
    txt = subprocess.run(["openssl", "x509", "-in", str(store / "ca.crt"), "-noout", "-ext", "nameConstraints,basicConstraints"],
                         capture_output=True, text=True).stdout
    assert "CA:TRUE, pathlen:0" in txt and "DNS:localhost" in txt and "DNS:.ts.net" in txt and "IP:100.64.0.0" in txt
    assert "critical" in txt


@needs_openssl
def test_a_certificate_for_a_public_name_signed_by_this_ca_is_rejected_by_openssl(store, tmp_path):
    """The point of name constraints: even a leaked CA key cannot vouch for a real website."""
    tls.ensure()
    ext = tmp_path / "ext.cnf"
    ext.write_text("subjectAltName=DNS:www.bank.example\nextendedKeyUsage=serverAuth\n")
    subprocess.run(["openssl", "req", "-new", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes", "-keyout", str(tmp_path / "k"),
                    "-out", str(tmp_path / "c"), "-subj", "/CN=www.bank.example"], capture_output=True, check=True)
    subprocess.run(["openssl", "x509", "-req", "-in", str(tmp_path / "c"), "-CA", str(store / "ca.crt"), "-CAkey", str(store / "ca.key"),
                    "-CAcreateserial", "-days", "30", "-extfile", str(ext), "-out", str(tmp_path / "forged.crt")], capture_output=True, check=True)
    r = subprocess.run(["openssl", "verify", "-CAfile", str(store / "ca.crt"), str(tmp_path / "forged.crt")], capture_output=True, text=True)
    assert r.returncode != 0 and "permitted subtree violation" in (r.stdout + r.stderr)


@needs_openssl
def test_ensure_is_idempotent_and_reissues_when_a_name_is_added(store):
    first = tls.ensure()
    serial1 = subprocess.run(["openssl", "x509", "-in", str(store / "server.crt"), "-noout", "-serial"], capture_output=True, text=True).stdout
    again = tls.ensure()
    serial2 = subprocess.run(["openssl", "x509", "-in", str(store / "server.crt"), "-noout", "-serial"], capture_output=True, text=True).stdout
    assert serial1 == serial2 and first["cert"]["names"] == again["cert"]["names"]
    tls.ensure(["10.9.8.7"])
    serial3 = subprocess.run(["openssl", "x509", "-in", str(store / "server.crt"), "-noout", "-serial"], capture_output=True, text=True).stdout
    assert serial3 != serial2 and "10.9.8.7" in tls.cert_info(store / "server.crt")["names"]


@needs_openssl
def test_a_live_handshake_is_tls12_or_better_and_the_wrong_name_is_refused(store):
    tls.ensure()
    sctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    sctx.minimum_version = ssl.TLSVersion.TLSv1_2
    sctx.load_cert_chain(store / "server.crt", store / "server.key")
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(5)
    port = srv.getsockname()[1]

    def serve():
        for _ in range(3):
            try:
                c, _ = srv.accept()
                with sctx.wrap_socket(c, server_side=True) as t:
                    t.recv(10)
            except (ssl.SSLError, OSError):
                pass
    threading.Thread(target=serve, daemon=True).start()
    ok = tls.probe("hub.securax.localhost", store / "ca.crt", port=port)
    assert ok["ok"] and ok["tls"] in ("TLSv1.2", "TLSv1.3")
    bad = tls.probe("www.bank.example", store / "ca.crt", port=port)
    assert not bad["ok"]
    srv.close()


def test_generated_edge_config_has_one_block_per_name_and_is_modern():
    conf = tls.render_edge_conf("securax.example.in")
    for _label, name, svc, port, _plain in tls.ENDPOINTS:
        assert f"server_name {name}.securax.example.in;" in conf, name
        assert f"set $up http://{svc}:{port};" in conf, svc
    assert re.findall(r"listen (\d+)", conf).count("443") == len(tls.ENDPOINTS) + 1        # one block per name + the default (421) block
    assert "listen 80 default_server;" in conf and "return 301 https://$host$request_uri;" in conf
    assert "return 421;" in conf                                                           # an unknown name / a raw IP gets no service
    assert "ssl_protocols TLSv1.2 TLSv1.3;" in conf and "ssl_session_tickets off;" in conf
    assert not re.search(r"TLSv1\.1|SSLv|RC4|3DES|\bMD5\b|EXPORT", conf)
    assert "Strict-Transport-Security" not in conf.replace("# NOT set", "").replace("NOT set on purpose: HSTS", "")
    assert not re.search(r"listen (?!80\b|443\b|9443\b|9444\b)\d+", conf)                 # no other port: 443 by name + the two device ports


def test_domain_validation_and_default(monkeypatch):
    assert tls.valid_domain("securax.localhost") and tls.valid_domain("securax.example.in") and not tls.valid_domain("bad_domain") and not tls.valid_domain("x")
    assert not tls.valid_domain("a.b;rm -rf /") and not tls.valid_domain("host name.com")
    monkeypatch.setenv("SECURAX_DOMAIN", "evil;domain")
    assert tls.domain() == tls.DEFAULT_DOMAIN


def test_overlay_publishes_only_the_edge_and_one_loopback_gateway_port():
    if not shutil.which("docker"):
        pytest.skip("docker not installed")
    env = ROOT / "local" / "compose" / ".env.example"
    out = subprocess.run(["docker", "compose", "--env-file", str(env), "-f", str(ROOT / "local/compose/docker-compose.yml"),
                          "-f", str(ROOT / "local/compose/tls.yml"), "--profile", "ai", "config", "--format", "json"],
                         capture_output=True, text=True, env={"PATH": "/usr/bin:/usr/local/bin:/bin", "TLS_DIR": "/tmp"})
    if out.returncode:
        pytest.skip("docker compose could not render: " + out.stderr[:120])
    svc = json.loads(out.stdout)["services"]
    published = {n: [(p.get("host_ip"), int(p["published"])) for p in s.get("ports", [])] for n, s in svc.items() if s.get("ports")}
    assert set(published) == {"tls-edge", "gateway"}
    assert published["gateway"] == [("127.0.0.1", 8080)]
    assert sorted(p for _, p in published["tls-edge"]) == [80, 443, 9443, 9444]          # ONE name-routed HTTPS port (+ redirect) + 2 device ports
    assert all(ip == "127.0.0.1" for ip, p in published["tls-edge"] if p in (9443, 9444))  # device ports: loopback only, for tailscale serve
    assert not any(ip in (None, "", "0.0.0.0") for ip, _ in published["tls-edge"])          # never wide open by default


def test_base_compose_binds_every_published_port_to_loopback_by_default():
    txt = (ROOT / "local" / "compose" / "docker-compose.yml").read_text()
    for m in re.finditer(r'ports:\s*\["([^"]+)"\]', txt):
        spec_ = m.group(1)
        assert spec_.startswith("${BIND_HOST:-127.0.0.1}:") or spec_.startswith("${SYNC_BIND:-127.0.0.1}:"), f"{spec_} would listen on every interface"


def test_name_permission_rules():
    assert tls.permitted("localhost") and tls.permitted("a.b.ts.net") and tls.permitted("gateway.securax.internal")
    assert tls.permitted("10.1.2.3") and tls.permitted("100.101.1.1") and tls.permitted("127.0.0.1") and tls.permitted("::1")
    assert not tls.permitted("example.com") and not tls.permitted("8.8.8.8") and not tls.permitted("100.0.0.1")
    assert tls.permitted("RC", hostname="rc") and not tls.permitted("RC")


def test_on_off_edit_only_the_two_keys_and_keep_everything_else(store):
    tls.ENVF.write_text("GEMINI_API_KEY=abc\nCOMPOSE_FILE=old\n")
    import os
    if shutil.which("openssl"):
        tls.cmd_on([], None, False)
        env = tls.read_env()
        assert env["COMPOSE_FILE"] == tls.TLS_COMPOSE and env["TLS_DIR"] == str(store) and env["GEMINI_API_KEY"] == "abc"
        assert env["SECURAX_DOMAIN"] == tls.DEFAULT_DOMAIN
        assert tls.tls_is_on()
        tls.cmd_off()
        assert "COMPOSE_FILE" not in tls.read_env() and tls.read_env()["GEMINI_API_KEY"] == "abc"
        assert (tls.ENVF.stat().st_mode & 0o077) == 0
    assert os.path.exists(tls.ENVF)


def test_hub_and_ask_links_follow_the_page_scheme():
    hub = (ROOT / "guiding-map" / "hub.html").read_text()
    ops = (ROOT / "guiding-map" / "ops.js").read_text()
    assert 'location.protocol === "https:"' in hub and 'web("chat",3000)' in hub and 'gw("/healthz")' in hub
    assert 'estateUrl("chat", 3000)' in ops and 'location.protocol === "https:"' in ops


@needs_openssl
def test_wildcard_domain_is_covered_and_a_foreign_domain_needs_a_new_authority(store):
    res = tls.ensure(None, dom="securax.localhost")
    assert {"securax.localhost", "*.securax.localhost"} <= set(res["cert"]["names"])
    with pytest.raises(SystemExit) as e:
        tls.ensure(None, dom="securax.example.in")
    assert "--new-ca" in str(e.value)
    res = tls.ensure(None, dom="securax.example.in", new_ca=True)
    assert "*.securax.example.in" in res["cert"]["names"] and tls.ca_domains(store) == ["securax.example.in"]
    r = subprocess.run(["openssl", "verify", "-CAfile", str(store / "ca.crt"), str(store / "server.crt")], capture_output=True, text=True)
    assert r.returncode == 0
    txt = subprocess.run(["openssl", "x509", "-in", str(store / "ca.crt"), "-noout", "-ext", "nameConstraints"], capture_output=True, text=True).stdout
    assert "DNS:securax.example.in" in txt


@needs_openssl
def test_a_second_run_with_a_wildcard_does_not_reissue(store):
    tls.ensure()
    s1 = subprocess.run(["openssl", "x509", "-in", str(store / "server.crt"), "-noout", "-serial"], capture_output=True, text=True).stdout
    tls.ensure()
    s2 = subprocess.run(["openssl", "x509", "-in", str(store / "server.crt"), "-noout", "-serial"], capture_output=True, text=True).stdout
    assert s1 == s2


def test_gateway_cors_allows_only_the_configured_domain(monkeypatch):
    import importlib
    sys.path.insert(0, str(ROOT / "apps" / "llm-gateway"))
    monkeypatch.setenv("SECURAX_DOMAIN", "securax.example.in")
    monkeypatch.setenv("UPSTREAM_URL", "mock")
    import app.main as m
    from fastapi.testclient import TestClient
    importlib.reload(m)
    c = TestClient(m.app)
    ok = c.options("/healthz", headers={"Origin": "https://hub.securax.example.in", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "https://hub.securax.example.in"
    for bad in ("https://evil.example.com", "https://securax.example.in.evil.com", "http://hub.securax.example.in"):
        r = c.options("/healthz", headers={"Origin": bad, "Access-Control-Request-Method": "GET"})
        assert "access-control-allow-origin" not in r.headers, bad
    assert c.options("/healthz", headers={"Origin": "http://localhost:8088", "Access-Control-Request-Method": "GET"}).headers.get("access-control-allow-origin") == "http://localhost:8088"


# ───────────────────────────── phase 2: internal sidecars ─────────────────────────────
def test_internal_edge_verifies_every_upstream_and_never_uses_plain_http_for_a_sidecar_service():
    conf = tls.render_edge_conf("securax.localhost", internal=True)
    assert "proxy_ssl_verify on;" in conf and "proxy_ssl_trusted_certificate /etc/tls/ca.crt;" in conf
    covered = {s for s, _p, _l in tls.INTERNAL}
    for _label, _name, svc, port, _plain in tls.ENDPOINTS:
        if svc in covered:
            assert f"https://{svc}.securax.internal:{tls.SIDECAR_PORT}" in conf
            assert f"http://{svc}:{port}" not in conf
    assert "server_name api.securax.localhost localhost 127.0.0.1;" in conf   # the CLI's own https://localhost


def test_phase_one_edge_is_unchanged_when_internal_is_off():
    conf = tls.render_edge_conf("securax.localhost", internal=False)
    assert "proxy_ssl_verify" not in conf and ".securax.internal" not in conf


def test_sidecar_conf_terminates_tls_and_forwards_to_loopback_only():
    s = tls.sidecar_conf("litellm", 4000)
    assert f"listen {tls.SIDECAR_PORT} ssl;" in s and "/etc/tls/litellm.crt" in s
    assert "proxy_pass http://127.0.0.1:4000;" in s and "TLSv1.1" not in s and "ssl_session_tickets off" in s


def _compose_config():
    if not shutil.which("docker"):
        pytest.skip("docker not installed")
    env = {**__import__("os").environ, "COMPOSE_FILE": tls.TLS_COMPOSE_INTERNAL, "TLS_DIR": "/tmp/tls", "BIND_HOST": "127.0.0.1"}
    r = subprocess.run(["docker", "compose", "--profile", "ai", "config", "--format", "json"], cwd=ROOT / "local" / "compose", env=env, capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip(f"compose config unavailable: {r.stderr[-200:]}")
    return json.loads(r.stdout)["services"]


def test_internal_overlay_publishes_nothing_per_service_and_sidecars_share_the_service_network():
    svcs = _compose_config()
    for svc, _port, loop in tls.INTERNAL:
        if not loop:
            continue
        assert not svcs[svc].get("ports"), f"{svc} still publishes a port"
        sc = svcs[f"{svc}-tls"]
        assert sc["network_mode"] == f"service:{svc}"
    assert [p["published"] for p in svcs["tls-edge"]["ports"]] and all(p["published"] in ("443", "80", "9443", "9444") for p in svcs["tls-edge"]["ports"])


# ───────────────────────────── stopped services, probes, links (the reported incident) ─────────────────────────────
@pytest.mark.parametrize("internal", [False, True])
def test_the_command_center_gets_a_same_origin_status_probe_for_every_other_service(internal):
    conf = tls.render_edge_conf("securax.localhost", internal=internal)
    hub = conf[conf.index("server_name hub."):conf.index("# Chat")]
    for _label, name, _svc, _port, _plain in tls.ENDPOINTS:
        if name != "hub":
            assert f"location = /_up/{name} " in hub
    assert "/_up/hub" not in hub


def test_a_stopped_optional_service_gets_a_plain_english_page_with_the_exact_command():
    conf = tls.render_edge_conf("securax.localhost")
    docs = conf[conf.index("server_name docs."):conf.index("# Automation")]
    assert "error_page 502 503 504 /_down;" in docs and "./securax start docs" in docs and "is not running" in docs
    flows = conf[conf.index("server_name flows."):conf.index("# Sync service")]
    assert "./securax start flows" in flows
    assert "_down" not in conf[conf.index("server_name hub."):conf.index("# Chat")].replace("/_up/", "")   # the probe must see the raw 502


def test_every_hub_card_that_is_an_endpoint_uses_the_name_table():
    hub = (ROOT / "guiding-map" / "hub.html").read_text("utf-8")
    assert 'url:"http://"+H+":8088' not in hub                      # a hard-coded port is exactly what broke the Command Center behind the edge
    for _label, name, _svc, _port, plain in tls.ENDPOINTS:
        if name in ("hub", "chat", "docs", "flows"):
            assert f'web("{name}",{plain})' in hub


# ───────────────────────────── a fixed page must not look unchanged after an update ─────────────────────────────
def test_the_command_center_is_always_revalidated_not_kept_by_heuristic_caching():
    assert 'add_header Cache-Control "no-cache" always;' in (ROOT / "local" / "compose" / "guiding-map.conf").read_text("utf-8")
    assert 'add_header Cache-Control "no-cache" always;' in tls.render_edge_conf("securax.localhost", internal=True)    # the edge's own static hub
    assert 'cache: "no-cache"' in (ROOT / "guiding-map" / "sw.js").read_text("utf-8")


def test_no_launcher_or_setup_script_still_opens_the_plain_http_port_that_https_unpublishes():
    for f in ("START-HERE-Windows.bat", "local/scripts/wsl-setup.sh", "WINDOWS-QUICKSTART.md"):
        txt = (ROOT / f).read_text("utf-8")
        assert not re.search(r"(start \"\" |Opening your Command Center: |DONE\. Command Center: )http://localhost:8088", txt), f


def test_device_ports_serve_the_app_same_origin_and_chat_for_tailscale():
    conf = tls.render_edge_conf("securax.localhost")
    app = conf[conf.index("listen 9443 ssl"):conf.index("listen 9444 ssl")]
    assert "server_name _;" in app and "location /sync" in app and "location /v1/" in app and "location = /version" in app
    assert "http://open-webui:8080" in conf[conf.index("listen 9444 ssl"):]
    internal = tls.render_edge_conf("securax.localhost", internal=True)
    assert "gateway.securax.internal" in internal[internal.index("listen 9443 ssl"):]          # internal TLS still applies on device ports
