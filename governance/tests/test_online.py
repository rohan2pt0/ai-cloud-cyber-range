"""./securax online: the whole Cloudflare setup against a stand-in Cloudflare that keeps state, so a second run repairs instead of
duplicating, only the listed e-mails get in, and the settings the estate needs land in .env (mode 600). No network."""
import importlib.util
import pathlib
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("online", ROOT / "governance" / "online.py")
on = importlib.util.module_from_spec(_s)
_s.loader.exec_module(on)


class FakeCloudflare:
    """Just enough of api.cloudflare.com: zones, Access organisation, tunnels, DNS, identity providers, policies, apps."""
    def __init__(self, team=True):
        self.zone = {"id": "zone-1", "name": "example.invalid", "account": {"id": "acc-1"}}
        self.team, self.tunnels, self.dns, self.idps, self.policies, self.apps, self.calls = team, [], [], [], [], [], []

    def __call__(self, method, path, body=None):
        self.calls.append((method, path))
        base, _, q = path.partition("?")
        if base == "/zones":
            return [self.zone] if "name=example.invalid" in q else []
        if base.endswith("/access/organizations"):
            if not self.team:
                raise on.Refused("GET /access/organizations → 9999: access.api.error.not_enabled")
            return {"auth_domain": "myteam.cloudflareaccess.com"}
        if base.endswith("/cfd_tunnel"):
            if method == "POST":
                self.tunnels.append({"id": str(uuid.uuid4()), **body})
                return self.tunnels[-1]
            want = dict(x.split("=", 1) for x in q.split("&") if "=" in x).get("name")
            return [t for t in self.tunnels if t["name"] == want]                    # Cloudflare's name filter is exact
        if base.endswith("/configurations"):
            self.ingress = body["config"]["ingress"]
            return {}
        if base.endswith("/token"):
            return "tunnel-token-for-tests"
        if "/dns_records" in base:
            if method == "GET":
                want = dict(x.split("=", 1) for x in q.split("&") if "=" in x).get("name")
                return [r for r in self.dns if r["name"] == want]
            if method == "POST":
                self.dns.append({"id": str(uuid.uuid4()), **body})
            else:
                rid = base.rsplit("/", 1)[1]
                self.dns = [({**r, **body} if r["id"] == rid else r) for r in self.dns]
            return {}
        for name, store in (("identity_providers", self.idps), ("policies", self.policies), ("apps", self.apps)):
            if f"/access/{name}" in base:
                if method == "GET":
                    return list(store)
                if method == "POST":
                    store.append({"id": str(uuid.uuid4()), "aud": "aud-" + name, **body})
                    return store[-1]
                rid = base.rsplit("/", 1)[1]
                for i, x in enumerate(store):
                    if x["id"] == rid:
                        store[i] = {**x, **body}
                        return store[i]
        raise AssertionError(f"unexpected call {method} {path}")


def test_setup_builds_everything_once_and_a_second_run_repairs_without_duplicates():
    cf, out = FakeCloudflare(), []
    v = on.setup(cf, "example.invalid", ["owner@example.invalid"], say=out.append)
    assert [r["name"] for r in cf.dns] == ["hub.example.invalid", "chat.example.invalid"]
    assert all(r["proxied"] and r["content"].endswith(".cfargotunnel.com") for r in cf.dns)
    assert cf.ingress[-1] == {"service": "http_status:404"}                                  # nothing else is reachable through the tunnel
    assert {i["service"] for i in cf.ingress[:-1]} == {"http://guiding-map:80", "http://open-webui:8080"}
    assert cf.policies[0]["include"] == [{"email": {"email": "owner@example.invalid"}}] and cf.policies[0]["decision"] == "allow"
    app = cf.apps[0]
    assert app["policies"] == [{"id": cf.policies[0]["id"], "precedence": 1}] and app["allowed_idps"] == [cf.idps[0]["id"]]
    assert cf.idps[0]["type"] == "onetimepin" and app["auto_redirect_to_identity"] is True   # works before Google is added
    assert v["SYNC_ACCESS_TEAM"] == "myteam.cloudflareaccess.com" and v["SYNC_ACCESS_AUD"] == app["aud"]
    assert v["BIND_HOST"] == "127.0.0.1" and v["CF_TUNNEL_TOKEN"] == "tunnel-token-for-tests"
    cf.dns[0]["content"] = "somewhere-else.example.invalid"                                  # someone changed a record by hand
    on.setup(cf, "example.invalid", ["owner@example.invalid", "second@example.invalid"], say=out.append)
    assert len(cf.tunnels) == 1 and len(cf.dns) == 2 and len(cf.apps) == 1 and len(cf.policies) == 1 and len(cf.idps) == 1
    assert cf.dns[0]["content"].endswith(".cfargotunnel.com")                               # repaired
    assert len(cf.policies[0]["include"]) == 2                                               # the second address is now allowed


def test_google_is_added_and_the_email_code_stays_as_the_way_in_if_google_locks_you_out():
    cf = FakeCloudflare()
    on.setup(cf, "example.invalid", ["owner@example.invalid"], say=lambda *_: None)
    on.add_google(cf, "acc-1", "client-id-for-tests", "client-secret-for-tests")
    on.setup(cf, "example.invalid", ["owner@example.invalid"], say=lambda *_: None)
    google = [i for i in cf.idps if i["type"] == "google"][0]
    otp = [i for i in cf.idps if i["type"] == "onetimepin"][0]
    assert cf.apps[0]["allowed_idps"] == [google["id"], otp["id"]] and cf.apps[0]["auto_redirect_to_identity"] is False


def test_remove_never_leaves_nobody_able_to_sign_in(tmp_path, monkeypatch):
    envf = tmp_path / ".env"
    envf.write_text("ONLINE_EMAILS=owner@example.invalid\n")
    monkeypatch.setattr(on, "ENVF", envf)
    monkeypatch.delenv("ONLINE_EMAILS", raising=False)
    out = []
    assert on.main(["remove", "owner@example.invalid"], say=out.append) == 2 and "nobody" in out[0]
    assert "ONLINE_EMAILS=owner@example.invalid" in envf.read_text()


def test_plain_reasons_when_cloudflare_is_not_ready():
    for cf, dom, word in ((FakeCloudflare(), "not-mine.invalid", "not in this Cloudflare account"),
                          (FakeCloudflare(team=False), "example.invalid", "Zero Trust is not switched on")):
        try:
            on.setup(cf, dom, ["owner@example.invalid"], say=lambda *_: None)
            raise AssertionError("should have refused")
        except on.Refused as exc:
            assert word in str(exc)


def test_an_existing_non_cname_record_is_never_overwritten():
    cf = FakeCloudflare()
    cf.dns.append({"id": "r1", "type": "A", "name": "hub.example.invalid", "content": "192.0.2.10", "proxied": False})
    try:
        on.setup(cf, "example.invalid", ["owner@example.invalid"], say=lambda *_: None)
        raise AssertionError("should have refused")
    except on.Refused as exc:
        assert "already exists as a A record" in str(exc)
    assert cf.dns[0]["content"] == "192.0.2.10"


def test_cli_writes_env_private_and_marks_online(tmp_path, monkeypatch):
    envf = tmp_path / ".env"
    envf.write_text("BIND_HOST=0.0.0.0\nSECURAX_OPTIONAL=passwords\n")
    monkeypatch.setattr(on, "ENVF", envf)
    for k in ("CF_API_TOKEN", "ONLINE_EMAILS", "ONLINE_DOMAIN"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("CF_API_TOKEN", "x" * 40)
    monkeypatch.setenv("ONLINE_EMAILS", "owner@example.invalid")
    monkeypatch.setenv("ONLINE_DOMAIN", "example.invalid")
    cf, out = FakeCloudflare(), []
    monkeypatch.setattr(on, "make_api", lambda tok: cf)
    assert on.main(["setup"], say=out.append) == 0
    text = envf.read_text()
    assert "BIND_HOST=127.0.0.1" in text and "CF_TUNNEL_TOKEN=tunnel-token-for-tests" in text
    assert "SECURAX_OPTIONAL=passwords online" in text and oct(envf.stat().st_mode)[-3:] == "600"
    assert any("BIND_HOST was 0.0.0.0" in x for x in out)
    monkeypatch.setattr(on, "make_api", lambda tok: (_ for _ in ()).throw(on.Refused("boom")))
    assert on.main(["setup"], say=out.append) == 1 and "not switched online" in out[-1]


def test_beta_gets_its_own_tunnel_addresses_and_gate_and_never_touches_the_stable_ones(monkeypatch):
    cf = FakeCloudflare()
    monkeypatch.setenv("ONLINE_PREFIX", "")
    on.setup(cf, "example.invalid", ["owner@example.invalid"], say=lambda *_: None)
    monkeypatch.setenv("ONLINE_PREFIX", "beta-")
    v = on.setup(cf, "example.invalid", ["owner@example.invalid"], say=lambda *_: None)
    assert [t["name"] for t in cf.tunnels] == ["securax", "securax-beta"] and len(cf.apps) == 2
    assert sorted(r["name"] for r in cf.dns) == ["beta-chat.example.invalid", "beta-hub.example.invalid", "chat.example.invalid",
                                                 "hub.example.invalid"]
    assert {a["name"] for a in cf.apps} == {"SecuRAX", "SecuRAX beta"} and v["ONLINE_PREFIX"] == "beta-"


def test_invite_then_join_gives_a_second_machine_the_same_addresses_but_never_the_api_token(tmp_path, monkeypatch):
    first, second = tmp_path / "a.env", tmp_path / "b.env"
    first.write_text("CF_API_TOKEN=secret-api-token-for-tests\nCF_TUNNEL_TOKEN=tunnel-token-for-tests\nONLINE_DOMAIN=example.invalid\n"
                     "ONLINE_EMAILS=owner@example.invalid\nSYNC_ACCESS_TEAM=t.cloudflareaccess.com\nSYNC_ACCESS_AUD=aud\n")
    for k in on.JOIN_KEYS + ("CF_API_TOKEN",):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(on, "ENVF", first)
    out = []
    assert on.main(["invite"], say=out.append) == 0
    code = next(x for x in out if "online join" in x).split()[-1]
    monkeypatch.setattr(on, "ENVF", second)
    second.write_text("BIND_HOST=0.0.0.0\n")
    assert on.main(["join", code], say=out.append) == 0
    text = second.read_text()
    assert "CF_TUNNEL_TOKEN=tunnel-token-for-tests" in text and "SYNC_ACCESS_AUD=aud" in text and "BIND_HOST=127.0.0.1" in text
    assert "secret-api-token-for-tests" not in text and "SECURAX_OPTIONAL=online" in text
    assert on.main(["join", "not-a-code"], say=out.append) == 2
