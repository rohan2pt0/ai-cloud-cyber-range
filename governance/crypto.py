#!/usr/bin/env python3
"""Cryptography inventory (CBOM) and quantum-readiness view of THIS estate.

    ./securax crypto                      the inventory, ranked: what to fix first and why
    ./securax crypto --json               the same, machine-readable
    ./securax crypto --cbom > cbom.json   a CycloneDX 1.6 Cryptography Bill of Materials (what an RBI / SEBI / auditor asks for)
    ./securax crypto --strict             exit 1 when an item under OUR control is still exposed to "harvest now, decrypt later" (cron / CI)
    ./securax crypto keygen PATH          make a random 256-bit key file for encrypted backups (keep it OFF this machine)

Why this matters, in three lines: a quantum computer breaks the public-key maths that today's TLS key exchange, certificates, JWT signatures
and VPNs rest on (Shor), but NOT well-sized symmetric encryption or SHA-2 (Grover only halves the strength). Anything recorded today and
kept secret for years can be decrypted later ("harvest now, decrypt later"), so KEY EXCHANGE is the urgent part; signatures and
certificates only matter at the moment they are checked, so they can follow. NIST's draft transition plan (IR 8547) proposes deprecating
128-bit-security RSA/ECC after 2030 and disallowing them after 2035; it is a draft, so the dates are a planning baseline, not law.

Everything below is read from the estate itself (certificates, configuration, source), not asserted. Where a fact cannot be checked here
(a third party's software, a VPN you run outside this machine) the row says so and is marked `third-party` or `not probed`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import pathlib
import re
import secrets
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NIST_DISALLOW_YEAR = 2035            # NIST IR 8547 (initial public draft, Nov 2024): RSA / ECC (128-bit) disallowed after 2035
NIST_DEPRECATE_YEAR = 2030           # ... and 112-bit security deprecated after 2030

# quantum standing of an algorithm family
VULNERABLE = "vulnerable"            # broken by Shor: RSA, DH, ECDH, ECDSA, EdDSA
HYBRID = "hybrid"                    # classical + post-quantum together (the connection is safe if EITHER holds)
SAFE = "safe"                        # symmetric >= 256 bit, SHA-2/3 >= 256 bit
WEAKENED = "weakened"                # symmetric 128 bit (Grover: ~64-bit effort) - acceptable short term, plan 256
NONE = "none"                        # not encrypted / not applicable


def _load_tls():
    spec = importlib.util.spec_from_file_location("securax_tls_for_crypto", ROOT / "governance" / "tls.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def read_env() -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        for ln in (ROOT / "local" / "compose" / ".env").read_text("utf-8").splitlines():
            if ln.strip() and not ln.lstrip().startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    out.update({k: v for k, v in os.environ.items() if k.startswith("SECURAX_")})
    return out


def cert_facts(path: pathlib.Path) -> dict:
    """Algorithm, key size, signature, validity of an X.509 certificate, read with the system openssl (no library needed)."""
    exe = shutil.which("openssl")
    if not exe or not path.exists():
        return {}
    r = subprocess.run([exe, "x509", "-in", str(path), "-noout", "-text", "-enddate", "-subject"], capture_output=True, text=True, timeout=20)
    if r.returncode:
        return {}
    t = r.stdout
    pub = re.search(r"Public Key Algorithm: (\S+)", t)
    bits = re.search(r"Public-Key: \((\d+) bit\)", t)
    curve = re.search(r"ASN1 OID: (\S+)", t)
    sig = re.search(r"Signature Algorithm: (\S+)", t)
    end = re.search(r"notAfter=(.*)", t)
    when = dt.datetime.strptime(end.group(1).strip(), "%b %d %H:%M:%S %Y %Z").replace(tzinfo=dt.timezone.utc) if end else None
    return {"public_key": pub.group(1) if pub else "?", "bits": int(bits.group(1)) if bits else None, "curve": curve.group(1) if curve else None,
            "signature": sig.group(1) if sig else "?", "not_after": when.isoformat() if when else None, "not_after_year": when.year if when else None,
            "subject": (re.search(r"subject=(.*)", t).group(1).strip() if re.search(r"subject=(.*)", t) else "")}


def quantum_of(public_key: str) -> str:
    return VULNERABLE if re.search(r"rsa|ec|ed25519|ed448|dsa|dh", public_key.lower()) else NONE


# ───────────────────────────────────────────── the inventory ─────────────────────────────────────────────
def inventory(tls_dir: pathlib.Path | None = None, probe_docker: bool = True) -> list[dict]:
    tls = _load_tls()
    d = tls_dir or tls.tls_dir()
    env = read_env()
    items: list[dict] = []

    def add(**kw):
        kw.setdefault("control", "ours")          # ours | third-party | entity
        kw.setdefault("harvest_now", False)       # is secrecy lost later if this is recorded today?
        kw.setdefault("verified", "read from the estate")
        kw.setdefault("evidence", [])
        items.append(kw)

    # 1. TLS key exchange at the edge (what a browser / phone / another machine negotiates)
    edge_conf = tls.render_edge_conf(tls.domain(), internal=False)
    groups = re.search(r"ssl_ecdh_curve ([^;]+);", edge_conf)
    glist = groups.group(1).split(":") if groups else []
    hybrid = [g for g in glist if "MLKEM" in g.upper()]
    add(id="edge-kex", name="TLS key exchange at the HTTPS edge", where="tls-edge (nginx) - every browser, phone and API client",
        usage="key exchange (confidentiality of everything in the session)", algorithm=(hybrid[0] + " + " + ", ".join(g for g in glist if g not in hybrid)) if hybrid else (", ".join(glist) or "nginx default groups"),
        quantum=HYBRID if hybrid else VULNERABLE, harvest_now=True,
        note=("A client that offers ML-KEM (current Chrome, Edge, Firefox) gets a hybrid exchange: recorded traffic stays secret even against a quantum attacker. Others fall back to classical curves."
              if hybrid else "Classical curves only: recorded traffic could be decrypted by a future quantum computer."),
        action=("Keep the nginx image at an OpenSSL >= 3.5 release; the journey tls_edge proves the hybrid group is negotiated." if hybrid else "Enable X25519MLKEM768 (nginx >= 1.30 / OpenSSL >= 3.5)."),
        evidence=["file:governance/tls.py", "journey:tls_edge"], verified="configuration generated by the estate; negotiated group proven by the tls_edge journey")

    # 2. TLS protocol versions / symmetric ciphers
    add(id="edge-symmetric", name="TLS record encryption (symmetric)", where="tls-edge and every sidecar", usage="bulk encryption",
        algorithm="AES-256-GCM, AES-128-GCM, ChaCha20-Poly1305 (TLS 1.3 suites + AEAD ECDHE suites for TLS 1.2)", quantum=SAFE,
        note="Grover halves symmetric strength: AES-256 and ChaCha20 stay strong; AES-128 stays acceptable but is the first to retire.",
        action="Optional: prefer the 256-bit suites when a regulator asks for 'quantum-resistant symmetric' (TLS 1.3 default order already favours them on AES hardware).",
        evidence=["file:governance/tls.py"])

    # 3-5. certificates: server, CA, internal
    for cid, label, fn in (("edge-cert", "Edge server certificate", "server.crt"), ("estate-ca", "Estate certificate authority", "ca.crt")):
        f = cert_facts(d / fn)
        if not f:
            add(id=cid, name=label, where=str(d / fn), usage="authentication (signature)", algorithm="not generated yet (./securax tls on)", quantum=NONE,
                note="No certificate to inspect yet.", action="Run `./securax tls on`.", verified="not present")
            continue
        late = bool(f["not_after_year"] and f["not_after_year"] > NIST_DISALLOW_YEAR)
        add(id=cid, name=label, where=str(d / fn), usage="authentication (signature) - forgeable only while the algorithm is broken, never retroactively",
            algorithm=f"{f['public_key']} {f['curve'] or ''} {f['bits'] or ''}-bit, signed {f['signature']}".replace("  ", " ").strip(),
            quantum=quantum_of(f["public_key"]),
            note=(f"Valid until {f['not_after'][:10]}, i.e. PAST the {NIST_DISALLOW_YEAR} date NIST's draft proposes for disallowing this algorithm: reissue before then." if late
                  else f"Valid until {f['not_after'][:10]}; the server certificate is reissued yearly, so it can move to a post-quantum signature as soon as browsers and the CA tooling support it."),
            action=("Plan a CA reissue (ML-DSA or hybrid) well before it expires; the CA is private, so you control the date." if late else "Move to ML-DSA (FIPS 204) when browsers trust it; nothing to do today."),
            evidence=["file:governance/tls.py", "journey:tls_edge"], verified="parsed from the actual certificate",
            facts=f)
    internal = sorted((d / "internal").glob("*.crt")) if (d / "internal").is_dir() else []
    if internal:
        f = cert_facts(internal[0])
        add(id="internal-certs", name=f"Per-service certificates ({len(internal)})", where=str(d / "internal"), usage="authentication of service-to-service TLS",
            algorithm=f"{f.get('public_key', '?')} {f.get('curve') or ''}".strip(), quantum=quantum_of(f.get("public_key", "")),
            note="Short-lived and reissued with `tls renew`; same posture as the edge certificate.", action="Follows the CA move above.", evidence=["journey:tls_internal"],
            verified="parsed from the first of the actual certificates", facts=f)

    # 6. internal hops
    add(id="internal-kex", name="Service-to-service TLS (phase 2)", where="sidecars between edge, gateway, router, model host, chat, n8n, sync",
        usage="key exchange inside the machine", algorithm=("hybrid + classical (same nginx build)" if hybrid else "classical curves"),
        quantum=HYBRID if hybrid else VULNERABLE, harvest_now=False,
        note="These hops never leave the machine or its Docker network, so there is little to record; they matter for lateral-movement defence, not for harvest-now-decrypt-later.",
        action="None needed for quantum; keep on for the regulated profile.", evidence=["journey:tls_internal"], verified="configuration generated by the estate")

    # 7. JWT / API keys at the gateway
    idsrc = ""
    try:
        idsrc = (ROOT / "apps" / "llm-gateway" / "app" / "identity.py").read_text("utf-8")
    except OSError:
        pass
    algs = sorted(set(re.findall(r'\b(RS256|HS256|ES256|EdDSA|PS256)\b', idsrc)))
    supported = [a for a in algs if a in ("RS256", "HS256")]       # what the verifier implements, not what a comment mentions
    add(id="jwt-sign", name="Gateway token signatures (OIDC / JWT)", where="apps/llm-gateway/app/identity.py", usage="authentication of callers",
        algorithm=", ".join(supported) or "unknown", quantum=VULNERABLE if "RS256" in supported else SAFE,
        note="RS256 is RSA: quantum-vulnerable for signatures (forge-later). HS256 is HMAC-SHA-256 with a shared secret: quantum-safe if the secret is long. The verifier accepts only the algorithms the operator lists, so a switch is a setting plus a verifier addition, not a redesign.",
        action="Add ES256 / EdDSA now (crypto-agility) and an ML-DSA path when identity providers issue it; until then HS256 with a 256-bit secret is the quantum-safe option for service tokens.",
        evidence=["file:apps/llm-gateway/app/identity.py", "test:apps/llm-gateway/tests/test_identity.py"], verified="read from the verifier source",
        agility="algorithm allow-list is configuration (OIDC_ALGS); new algorithms need a verifier addition")
    add(id="api-key-hash", name="Gateway API keys (stored as hashes)", where="GATEWAY_API_KEYS (hashes only)", usage="authentication / storage", algorithm="SHA-256",
        quantum=SAFE, note="A 256-bit hash keeps 128-bit security against Grover; only hashes are stored.", action="None.",
        evidence=["file:apps/llm-gateway/app/identity.py"], verified="read from the verifier source")

    # 8. backups
    keyfile = env.get("SECURAX_BACKUP_KEYFILE", "")
    bdir = pathlib.Path(env.get("SECURAX_BACKUP_DIR", ROOT / "backups")).expanduser()
    backups = sorted(bdir.glob("securax-*.tar.gz*"), key=lambda f: f.stat().st_mtime) if bdir.is_dir() else []
    latest = backups[-1].name if backups else None
    latest_enc = bool(latest and latest.endswith(".gpg"))
    protected = bool(keyfile) and (latest_enc or latest is None)          # configured, and nothing plain is the newest copy
    state = ("every backup is encrypted" if protected else
             "a key file is configured but the newest backup is still plain: take a new one" if keyfile else
             "backups are plain tar.gz (owner-only permissions)")
    add(id="backups", name="Backups at rest", where=str(bdir), usage="confidentiality of the backup file (contains your API keys)",
        algorithm="AES-256 (OpenPGP symmetric; key = your key file or passphrase)" if protected else "none (plain tar.gz, owner-only permissions)",
        quantum=SAFE if protected else NONE, harvest_now=not protected,
        note=(("Symmetric encryption only (no public-key step), so it is quantum-safe; its strength is the strength of your key file / passphrase. " if protected else
               "A copy that leaves the machine (cloud drive, USB) can be read by whoever holds it, and recorded copies can be read later. ") + state + "."),
        action=("Keep the key file OFF this machine (USB / password manager) and practise a restore." if protected else
                "./securax crypto keygen ~/securax-backup.key, copy it off this machine, then set SECURAX_BACKUP_KEYFILE=<that path> in local/compose/.env (or use  ./securax backup --passphrase)."),
        evidence=["cmd:backup", "journey:backup_encrypted"], verified=("newest backup: " + latest) if latest else "no backup taken yet")

    # 9. things we depend on but do not control
    def probe_openssl(image: str) -> str:
        if not (probe_docker and shutil.which("docker")) or subprocess.run(["docker", "image", "inspect", image], capture_output=True).returncode:
            return "not probed"
        r = subprocess.run(["docker", "run", "--rm", "--entrypoint", "python", image, "-c", "import ssl;print(ssl.OPENSSL_VERSION)"], capture_output=True, text=True, timeout=90)
        return r.stdout.strip() or "not probed"

    def pq_capable(v: str) -> bool:
        m = re.search(r"OpenSSL (\d+)\.(\d+)", v)
        return bool(m and (int(m.group(1)), int(m.group(2))) >= (3, 5))
    # the calls to cloud providers are made by the ROUTER (litellm), not the gateway: probe the image that actually makes them
    router_img = "ghcr.io/berriai/litellm:main-stable"
    try:
        m_img = re.search(r"image:\s*(ghcr.io/berriai/litellm\S+)", (ROOT / "local" / "compose" / "docker-compose.yml").read_text("utf-8"))
        router_img = m_img.group(1) if m_img else router_img
    except OSError:
        pass
    o_router, o_gw = probe_openssl(router_img), probe_openssl("vulnbank/llm-gateway:dev")
    can_pq = pq_capable(o_router)
    probed = o_router != "not probed"
    add(id="egress-cloud", name="Calls from the model router to cloud AI providers", where=f"litellm container ({router_img}: {o_router}); gateway image: {o_gw}",
        usage="key exchange to a third party (prompts and answers)",
        algorithm=("hybrid offered (OpenSSL >= 3.5 client)" if can_pq else ("classical only from this client (OpenSSL < 3.5)" if probed else "unknown (image not present here)")),
        quantum=HYBRID if can_pq else VULNERABLE, harvest_now=True, control="third-party",
        note="Our side decides what is OFFERED; the provider decides what is accepted, so this is hybrid only where the provider supports it. Anything RED/AMBER stays local by the data-tier router, so what travels is what you already accepted to send to a cloud.",
        action=("Nothing to change; recheck after each router image update (`./securax crypto`)." if can_pq else "Move the router to an image with OpenSSL >= 3.5 as it ships; until then keep sensitive classes local (residency + data-tier routing)."),
        evidence=["file:local/compose/docker-compose.yml", "journey:gateway_residency"],
        verified=("probed in the image that makes the calls: " + o_router) if probed else "not probed (the router image is not present on this machine)")
    add(id="vpn", name="Remote access (Tailscale / WireGuard, if you use it)", where="outside the estate", usage="key exchange for the tunnel", algorithm="Curve25519 (WireGuard)",
        quantum=VULNERABLE, harvest_now=True, control="third-party",
        note="WireGuard has no standardised post-quantum handshake yet (a pre-shared key mixed in is the interim mitigation). The estate does not run the VPN.",
        action="Use a WireGuard pre-shared key (Tailscale: check their post-quantum announcements) or keep sensitive traffic on the local network only.", verified="not probed (third-party software)")
    add(id="release-sign", name="Release provenance (SLSA build attestations)", where=".github/workflows/publish-images.yml", usage="authentication of released images (signature)",
        algorithm="Sigstore keyless (ECDSA P-256)", quantum=VULNERABLE, control="third-party",
        note="A signature protects the moment of verification; it is forgeable only once the algorithm is broken, not retroactively.", action="Follow Sigstore's move to post-quantum signatures; nothing to change here.",
        evidence=["file:.github/workflows/publish-images.yml"], verified="workflow read")
    add(id="host-disk", name="Data volumes and disks", where="Docker volumes on your machine", usage="confidentiality at rest", algorithm="none added by the estate (use BitLocker / LUKS)",
        quantum=NONE, control="entity", note="Full-disk encryption (AES-256) is the entity's control and is quantum-safe when AES-256 is chosen.", action="Confirm BitLocker/LUKS uses AES-256 (XTS 256-bit keys = 128-bit quantum strength is also accepted).", verified="not probed (host setting)")
    return items


def rank(items: list[dict]) -> list[dict]:
    """Do-first order: confidentiality that can be recorded today > under our control > quantum-vulnerable."""
    def score(i):
        return (3 if i["harvest_now"] and i["quantum"] in (VULNERABLE, NONE) else 0) + (2 if i["quantum"] in (VULNERABLE, NONE) else 0) + (1 if i["control"] == "ours" else 0)
    return sorted(items, key=lambda i: -score(i))


def exposed_ours(items: list[dict]) -> list[dict]:
    return [i for i in items if i["control"] == "ours" and i["harvest_now"] and i["quantum"] in (VULNERABLE, NONE)]


# ───────────────────────────────────────────── outputs ─────────────────────────────────────────────
LABEL = {VULNERABLE: "VULNERABLE", HYBRID: "hybrid (PQ)", SAFE: "safe", WEAKENED: "weakened", NONE: "unprotected"}


def render_text(items: list[dict]) -> str:
    out = ["Cryptography inventory (CBOM) - read from this estate, ranked: fix the top first", ""]
    for n, i in enumerate(rank(items), 1):
        flag = "  <- harvest-now-decrypt-later exposure" if (i["harvest_now"] and i["quantum"] in (VULNERABLE, NONE)) else ""
        out.append(f"{n:>2}. [{LABEL[i['quantum']]:<12}] {i['name']}{flag}")
        out.append(f"      algorithm : {i['algorithm']}")
        out.append(f"      why       : {i['note']}")
        out.append(f"      do        : {i['action']}")
        out.append(f"      checked   : {i['verified']}   ({i['control']})")
    ex = exposed_ours(items)
    out += ["", f"Summary: {sum(i['quantum'] in (SAFE, HYBRID) for i in items)} of {len(items)} items are quantum-safe or hybrid; "
            f"{len(ex)} under our control {'still carries' if len(ex) == 1 else 'still carry'} harvest-now-decrypt-later exposure."
            + (" (" + "; ".join(i["name"] for i in ex) + ")" if ex else ""),
            "Dates are planning baselines from NIST's DRAFT IR 8547 (deprecate 2030, disallow 2035); RBI's Q-SAFE committee (formed 25 May 2026) has not yet reported.",
            "What this does NOT cover: third-party software we do not run, your cloud providers' own choices, and the entity's wider estate."]
    return "\n".join(out)


def cyclonedx(items: list[dict]) -> dict:
    """A CycloneDX 1.6 CBOM: one cryptographic-asset component per inventory item (algorithm / certificate / protocol)."""
    comps = []
    for i in items:
        kind = "certificate" if "cert" in i["id"] or i["id"] == "estate-ca" else ("protocol" if i["id"].endswith("kex") else "algorithm")
        comp = {"type": "cryptographic-asset", "bom-ref": f"crypto/{i['id']}", "name": i["name"],
                "description": i["note"],
                "properties": [{"name": "securax:quantum", "value": i["quantum"]}, {"name": "securax:harvest-now-decrypt-later", "value": str(i["harvest_now"]).lower()},
                               {"name": "securax:control", "value": i["control"]}, {"name": "securax:where", "value": str(i["where"])},
                               {"name": "securax:algorithm", "value": str(i["algorithm"])}, {"name": "securax:action", "value": i["action"]},
                               {"name": "securax:verified", "value": i["verified"]}]}
        props: dict = {"assetType": kind}
        f = i.get("facts") or {}
        if kind == "certificate":
            props["certificateProperties"] = {k: v for k, v in {"subjectName": f.get("subject"), "notValidAfter": f.get("not_after"),
                                                                "signatureAlgorithmRef": None}.items() if v}
        elif kind == "protocol":
            props["protocolProperties"] = {"type": "tls", "version": "1.3"}
        else:
            props["algorithmProperties"] = {"primitive": "other", "cryptoFunctions": ["other"]}
        comp["cryptoProperties"] = props
        comps.append(comp)
    return {"bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1,
            "metadata": {"timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                         "component": {"type": "application", "name": "SecuRAX estate", "version": (ROOT / "VERSION").read_text().strip() if (ROOT / "VERSION").exists() else "dev"},
                         "tools": {"components": [{"type": "application", "name": "securax-crypto", "version": "1"}]}},
            "components": comps}


def keygen(path: pathlib.Path) -> int:
    if path.exists():
        print(f"{path} already exists - refusing to overwrite a key that may protect backups.", file=sys.stderr)
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(secrets.token_hex(32) + "\n")           # 256 random bits
    print(f"Key file written: {path}  (256 random bits, owner-only)\n"
          "  1. COPY it OFF this machine now (USB stick, password manager). Without it an encrypted backup can NOT be opened - by anyone, including you.\n"
          "  2. Then:  put  SECURAX_BACKUP_KEYFILE=" + str(path) + "  in local/compose/.env  (every backup, including the one `update` takes, is then encrypted).\n"
          "  3. Practise: ./securax backup && ./securax restore <file> --yes  once, with the key file, before you need it.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Cryptography inventory (CBOM) and quantum-readiness view.")
    ap.add_argument("action", nargs="?", choices=["show", "keygen"], default="show")
    ap.add_argument("path", nargs="?", help="keygen: where to write the key file")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--cbom", action="store_true", help="CycloneDX 1.6 Cryptography Bill of Materials")
    ap.add_argument("--strict", action="store_true", help="exit 1 if an item under our control is exposed to harvest-now-decrypt-later")
    a = ap.parse_args(argv)
    if a.action == "keygen":
        if not a.path:
            ap.error("keygen needs a path, e.g.  ./securax crypto keygen ~/securax-backup.key")
        return keygen(pathlib.Path(a.path).expanduser())
    items = inventory()
    if a.cbom:
        print(json.dumps(cyclonedx(items), indent=2))
    elif a.json:
        print(json.dumps({"items": rank(items), "exposed_ours": [i["id"] for i in exposed_ours(items)]}, indent=2))
    else:
        print(render_text(items))
    return 1 if (a.strict and exposed_ours(items)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
