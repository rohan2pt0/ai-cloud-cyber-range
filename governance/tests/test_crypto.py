"""Cryptography inventory (CBOM): it reads the estate, ranks what matters for a quantum adversary, emits a valid CycloneDX shape, and the
encrypted-backup construction it recommends really encrypts, detects tampering and refuses a wrong key."""
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

G = pathlib.Path(__file__).resolve().parent.parent
ROOT = G.parent
spec = importlib.util.spec_from_file_location("securax_crypto", G / "crypto.py")
cr = importlib.util.module_from_spec(spec)
sys.modules["securax_crypto"] = cr
spec.loader.exec_module(cr)

needs_openssl = pytest.mark.skipif(not shutil.which("openssl"), reason="openssl not installed")
needs_gpg = pytest.mark.skipif(not shutil.which("gpg"), reason="gpg not installed")


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_TLS_DIR", str(tmp_path / "tls"))
    cfg = {"SECURAX_BACKUP_DIR": str(tmp_path / "backups")}
    monkeypatch.setattr(cr, "read_env", lambda: dict(cfg))
    return cfg


def by_id(items):
    return {i["id"]: i for i in items}


def test_inventory_has_unique_ids_and_every_row_says_why_and_what_to_do(env):
    items = cr.inventory(probe_docker=False)
    assert len({i["id"] for i in items}) == len(items) >= 10
    for i in items:
        assert i["quantum"] in (cr.VULNERABLE, cr.HYBRID, cr.SAFE, cr.WEAKENED, cr.NONE)
        assert i["note"] and i["action"] and i["verified"] and i["control"] in ("ours", "third-party", "entity")


def test_the_edge_key_exchange_is_hybrid_and_is_read_from_the_real_configuration(env, monkeypatch):
    assert by_id(cr.inventory(probe_docker=False))["edge-kex"]["quantum"] == cr.HYBRID
    tls = cr._load_tls()
    monkeypatch.setattr(cr, "_load_tls", lambda: type("T", (), {"tls_dir": staticmethod(tls.tls_dir), "domain": staticmethod(tls.domain),
                                                                   "render_edge_conf": staticmethod(lambda d, internal=False: "ssl_ecdh_curve X25519:prime256v1;")}))
    kex = by_id(cr.inventory(probe_docker=False))["edge-kex"]
    assert kex["quantum"] == cr.VULNERABLE and kex["harvest_now"]                     # a regression to classical-only is reported, not hidden


@needs_openssl
def test_certificates_are_parsed_from_the_actual_files_and_a_ca_that_outlives_2035_is_flagged(env):
    tls = cr._load_tls()
    tls.ensure()
    items = by_id(cr.inventory(probe_docker=False))
    ca, srv = items["estate-ca"], items["edge-cert"]
    assert "ecPublicKey" in ca["facts"]["public_key"] and ca["facts"]["bits"] == 256 and ca["quantum"] == cr.VULNERABLE
    assert srv["quantum"] == cr.VULNERABLE
    late = ca["facts"]["not_after_year"] > cr.NIST_DISALLOW_YEAR
    assert late == ("PAST the 2035" in ca["note"])
    assert not srv["harvest_now"] and not ca["harvest_now"]                          # signatures are not a harvest-now exposure


def test_missing_certificates_are_reported_as_not_generated_not_invented(env):
    items = by_id(cr.inventory(probe_docker=False))
    assert "not generated yet" in items["edge-cert"]["algorithm"] and items["edge-cert"]["verified"] == "not present"


def test_gateway_signature_algorithms_are_read_from_the_verifier_source(env):
    jwt = by_id(cr.inventory(probe_docker=False))["jwt-sign"]
    assert "RS256" in jwt["algorithm"] and "HS256" in jwt["algorithm"] and jwt["quantum"] == cr.VULNERABLE


def test_backup_exposure_follows_the_newest_file_not_just_the_setting(env, tmp_path):
    b = tmp_path / "backups"
    exposed = lambda: "backups" in [i["id"] for i in cr.exposed_ours(cr.inventory(probe_docker=False))]   # noqa: E731
    assert exposed()                                                                  # nothing configured
    env["SECURAX_BACKUP_KEYFILE"] = str(tmp_path / "k")
    assert not exposed()                                                              # configured, no backup yet
    b.mkdir()
    (b / "securax-20260101-000000.tar.gz").write_bytes(b"x")
    assert exposed()                                                                  # configured, but the newest copy is still plain
    import os
    import time
    f = b / "securax-20260102-000000.tar.gz.gpg"
    f.write_bytes(b"y")
    os.utime(f, (time.time() + 5, time.time() + 5))
    assert not exposed()                                                              # newest is encrypted


def test_strict_exits_1_only_while_something_ours_is_exposed(env, monkeypatch, capsys):
    monkeypatch.setattr(cr, "inventory", lambda **k: [dict(id="a", name="A", where="w", usage="u", algorithm="x", quantum=cr.VULNERABLE, harvest_now=True, control="ours",
                                                           note="n", action="a", verified="v", evidence=[])])
    assert cr.main(["--strict"]) == 1 and cr.main([]) == 0
    capsys.readouterr()


def test_cbom_is_a_cyclonedx_16_document_with_one_crypto_asset_per_row(env):
    d = cr.cyclonedx(cr.inventory(probe_docker=False))
    assert d["bomFormat"] == "CycloneDX" and d["specVersion"] == "1.6"
    refs = [c["bom-ref"] for c in d["components"]]
    assert len(refs) == len(set(refs)) and all(c["type"] == "cryptographic-asset" and c["cryptoProperties"]["assetType"] in ("algorithm", "certificate", "protocol") for c in d["components"])
    json.dumps(d)


def test_keygen_writes_256_random_bits_owner_only_and_never_overwrites(tmp_path):
    k = tmp_path / "sub" / "k.key"
    assert cr.keygen(k) == 0
    assert re.fullmatch(r"[0-9a-f]{64}", k.read_text().strip()) and k.stat().st_mode & 0o077 == 0
    first = k.read_text()
    assert cr.keygen(k) == 1 and k.read_text() == first


@needs_gpg
def test_the_backup_construction_encrypts_detects_tampering_and_refuses_a_wrong_key(tmp_path):
    """Uses the EXACT gpg options from the securax script, so a change there is tested here."""
    opts = re.search(r'^GPGSYM="([^"]+)"', (ROOT / "securax").read_text(), re.M).group(1).split()
    home = tmp_path / "gh"
    home.mkdir(mode=0o700)
    env = {"GNUPGHOME": str(home), "PATH": "/usr/bin:/bin:/usr/local/bin"}
    key, wrong = tmp_path / "k", tmp_path / "w"
    key.write_text("a" * 64 + "\n")
    wrong.write_text("b" * 64 + "\n")
    plain = tmp_path / "p.tar.gz"
    plain.write_bytes(b"\x1f\x8b" + b"secret-api-key-material" * 50)
    enc = tmp_path / "p.gpg"
    run = lambda *a: subprocess.run(["gpg", *opts, *a], capture_output=True, env=env)   # noqa: E731
    assert run("--passphrase-file", str(key), "--symmetric", "-o", str(enc), str(plain)).returncode == 0
    blob = enc.read_bytes()
    assert b"secret-api-key-material" not in blob and blob[:2] != b"\x1f\x8b"
    assert "cipher 9" in subprocess.run(["gpg", "--batch", "--list-packets", str(enc)], capture_output=True, text=True, env=env).stdout + \
        subprocess.run(["gpg", "--batch", "--list-packets", str(enc)], capture_output=True, text=True, env=env).stderr
    out = tmp_path / "o"
    assert run("--passphrase-file", str(key), "-d", "-o", str(out), str(enc)).returncode == 0 and out.read_bytes() == plain.read_bytes()
    assert run("--passphrase-file", str(wrong), "-d", "-o", str(tmp_path / "o2"), str(enc)).returncode != 0
    bad = bytearray(blob)
    bad[-20] ^= 1
    (tmp_path / "t.gpg").write_bytes(bytes(bad))
    assert run("--passphrase-file", str(key), "-d", "-o", str(tmp_path / "o3"), str(tmp_path / "t.gpg")).returncode != 0
    subprocess.run(["gpgconf", "--kill", "gpg-agent"], env=env, capture_output=True)


# ───────────────────────────── the plain-English view ─────────────────────────────
def test_the_plain_view_says_what_needs_you_and_the_one_command_to_run(env):
    out = cr.render_simple(cr.inventory(probe_docker=False))
    assert "NEEDS YOU NOW" in out and "./securax protect" in out and "PROTECT-BACKUPS-Windows.bat" in out
    assert "ALREADY PROTECTED" in out and "CAN WAIT" in out and "OUTSIDE SECURAX" in out
    assert "CBOM" not in out and "harvest-now" not in out                       # no jargon in the default view


def test_nothing_is_reported_as_needing_you_once_backups_are_locked(env, tmp_path):
    env["SECURAX_BACKUP_KEYFILE"] = str(tmp_path / "k")
    out = cr.render_simple(cr.inventory(probe_docker=False))
    assert "NOTHING NEEDS YOU RIGHT NOW" in out and "Your backups are encrypted." in out


def test_every_inventory_row_lands_in_exactly_one_plain_bucket(env):
    items = cr.inventory(probe_docker=False)
    assert {cr.bucket(i) for i in items} <= {"done", "now", "later", "outside"}
    assert cr.render_simple(items)
    for i in items:
        if cr.bucket(i) == "now":
            assert cr.NOW.get(i["id"]), f"{i['id']} needs a plain-English line in NOW"


def test_full_view_still_has_the_technical_table_and_strict_still_exits_1(env, capsys):
    assert cr.main(["--full"]) == 0 and "Cryptography inventory (CBOM)" in capsys.readouterr().out
    assert cr.main(["--strict"]) == 1
    capsys.readouterr()
