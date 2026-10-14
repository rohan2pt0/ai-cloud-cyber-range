#!/usr/bin/env python3
"""Manage who may call the gateway: the AUTH_MODE switch, service API keys (only HASHES are stored), and a token checker for IdP setup.

    ./securax gateway-auth status
    ./securax gateway-auth enable [--mode required|optional]      turns authentication on and makes the keys the estate's own callers need
    ./securax gateway-auth disable                                back to the open laptop default
    ./securax gateway-auth key add NAME [--roles service] [--expires YYYY-MM-DD] [--data-class CLASS] [--env VAR]
    ./securax gateway-auth key list | revoke NAME | rotate NAME
    ./securax gateway-auth check-token JWT                        why would the gateway accept or refuse this token?

Humans sign in through YOUR identity provider (any OIDC provider: Keycloak, Entra ID, Okta, ...): set OIDC_ISSUER, OIDC_AUDIENCE and
OIDC_JWKS_URL (or OIDC_JWKS_FILE for an air-gapped estate) in local/compose/.env, map its roles with AUTH_ROLE_MAP, and require MFA for
privileged roles with AUTH_MFA_ROLES (default admin,auditor). Machines (Open WebUI, the CLI, n8n, Prometheus) use service keys.
Plaintext keys are shown once and kept only in the owner-only .env of the machine that needs them; the gateway sees hashes.
Standard library only.
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import pathlib
import secrets
import stat
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
ENV = ROOT / "local" / "compose" / ".env"
KEYVAR = "GATEWAY_API_KEYS_B64"


def _identity():
    spec = importlib.util.spec_from_file_location("securax_identity", ROOT / "apps" / "llm-gateway" / "app" / "identity.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod                  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


def read_env(path: pathlib.Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if path.exists():
        for ln in path.read_text("utf-8").splitlines():
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip().strip("'\"")
    return out


def set_env(path: pathlib.Path, key: str, value: str) -> None:
    lines = path.read_text("utf-8").splitlines() if path.exists() else []
    for i, ln in enumerate(lines):
        if ln.startswith(key + "="):
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", "utf-8")
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def load_keys(env: dict[str, str]) -> list[dict]:
    raw = env.get(KEYVAR, "")
    return json.loads(base64.b64decode(raw)) if raw else []


def save_keys(path: pathlib.Path, keys: list[dict]) -> None:
    set_env(path, KEYVAR, base64.b64encode(json.dumps(keys, separators=(",", ":")).encode()).decode())


def new_key() -> str:
    return "sk-sx-" + secrets.token_urlsafe(32)


def add_key(path: pathlib.Path, name: str, roles: list[str], expires: str = "", data_class: str = "", env_var: str = "") -> str:
    idn = _identity()
    bad = [r for r in roles if r not in idn.ROLES]
    if bad:
        raise SystemExit(f"unknown role(s) {bad}; choose from {list(idn.ROLES)}")
    if set(roles) & {"admin", "auditor"}:
        raise SystemExit("service keys cannot hold admin/auditor (those roles require MFA, which a machine cannot do): "
                         "sign in through your identity provider instead")
    if expires:
        time.strptime(expires, "%Y-%m-%d")
    keys = [k for k in load_keys(read_env(path)) if k["id"] != name]
    key = new_key()
    entry = {"id": name, "sha256": idn.hash_key(key), "roles": roles, "created": time.strftime("%Y-%m-%d")}
    if expires:
        entry["expires"] = expires
    if data_class:
        entry["data_class"] = data_class
    save_keys(path, keys + [entry])
    if env_var:
        set_env(path, env_var, key)
    return key


def cmd_status(a) -> int:
    env = read_env(pathlib.Path(a.env_file))
    mode = env.get("AUTH_MODE", "off")
    keys = load_keys(env)
    idp = bool(env.get("OIDC_JWKS_URL") or env.get("OIDC_JWKS_FILE") or env.get("OIDC_JWKS_JSON"))
    print(f"AUTH_MODE={mode}   identity provider configured: {'yes' if idp else 'no'}   service keys: {len(keys)}")
    if mode == "off":
        print("  ⚠ the gateway accepts anyone who can reach it (fine for one laptop; not for a regulated deployment) → ./securax gateway-auth enable")
    if mode != "off" and not idp:
        print("  ⚠ no OIDC provider yet: humans cannot sign in; only service keys work. Set OIDC_ISSUER/OIDC_AUDIENCE/OIDC_JWKS_URL in local/compose/.env")
    if idp and not env.get("OIDC_ISSUER"):
        print("  ⚠ OIDC_ISSUER is empty: tokens from any issuer holding a valid signature would be accepted. Set it.")
    for k in keys:
        exp = k.get("expires", "never")
        flag = "  ⚠ no expiry" if exp == "never" else ""
        print(f"  key {k['id']:<14} roles={','.join(k['roles']):<10} created={k.get('created', '?')} expires={exp}{flag}")
    return 0


def cmd_enable(a) -> int:
    env_path = pathlib.Path(a.env_file)
    env = read_env(env_path)
    made = []
    for name, var in (("openwebui", "WEBUI_GATEWAY_KEY"), ("securax-cli", "GATEWAY_API_KEY")):
        if not any(k["id"] == name for k in load_keys(read_env(env_path))) or not env.get(var):
            add_key(env_path, name, ["service"], expires=a.expires, env_var=var)
            made.append(name)
    set_env(env_path, "AUTH_MODE", a.mode)
    print(f"✔ AUTH_MODE={a.mode}. Service keys created for: {', '.join(made) or '(already present)'} — stored in {env_path} (owner-only).")
    print("  Restart to apply:  ./securax down && ./securax up")
    print("  Next: point humans at your identity provider (OIDC_*), require MFA for admin/auditor, and give n8n/Prometheus their own keys:")
    print("        ./securax gateway-auth key add n8n --roles service --expires 2027-06-30")
    return 0


def cmd_disable(a) -> int:
    set_env(pathlib.Path(a.env_file), "AUTH_MODE", "off")
    print("AUTH_MODE=off (open). Restart to apply:  ./securax down && ./securax up")
    return 0


def cmd_key(a) -> int:
    env_path = pathlib.Path(a.env_file)
    if a.action == "add":
        key = add_key(env_path, a.name, [r for r in a.roles.split(",") if r], a.expires, a.data_class, a.env)
        print(f"key for {a.name}:\n  {key}\nShown once — only its hash is stored. Restart the gateway to load it.")
    elif a.action == "list":
        return cmd_status(a)
    elif a.action == "revoke":
        keys = load_keys(read_env(env_path))
        left = [k for k in keys if k["id"] != a.name]
        if len(left) == len(keys):
            print(f"no key named {a.name}")
            return 1
        save_keys(env_path, left)
        print(f"revoked {a.name}. Restart the gateway to apply.")
    elif a.action == "rotate":
        old = next((k for k in load_keys(read_env(env_path)) if k["id"] == a.name), None)
        if not old:
            print(f"no key named {a.name}")
            return 1
        key = add_key(env_path, a.name, old["roles"], old.get("expires", ""), old.get("data_class", ""), a.env)
        print(f"rotated {a.name}; the old key stops working after a gateway restart:\n  {key}")
    return 0


def cmd_check(a) -> int:
    idn = _identity()
    env = {**os.environ, **read_env(pathlib.Path(a.env_file))}
    cfg = idn.Config.from_env({**env, "AUTH_MODE": env.get("AUTH_MODE", "off") if env.get("AUTH_MODE", "off") != "off" else "optional"})
    try:
        i = idn.verify_jwt(a.token, cfg)
    except idn.AuthError as e:
        print(f"REFUSED ({e.code}): {e.message}")
        return 1
    auth = idn.Authenticator(cfg)
    print(f"ACCEPTED: subject={i.subject} roles={list(i.roles)} mfa={i.mfa} issuer={i.issuer}")
    for ep in ("chat", "inspect", "metrics"):
        try:
            auth.authorize(i, ep)
            print(f"  {ep:<8} allowed")
        except idn.AuthError as e:
            print(f"  {ep:<8} refused: {e.code}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--env-file", default=str(ENV))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    en = sub.add_parser("enable")
    en.add_argument("--mode", choices=["required", "optional"], default="required")
    en.add_argument("--expires", default="", help="expiry for the machine keys created, YYYY-MM-DD")
    sub.add_parser("disable")
    k = sub.add_parser("key")
    k.add_argument("action", choices=["add", "list", "revoke", "rotate"])
    k.add_argument("name", nargs="?", default="")
    k.add_argument("--roles", default="service")
    k.add_argument("--expires", default="")
    k.add_argument("--data-class", default="")
    k.add_argument("--env", default="", help="also write the plaintext key to this variable in the owner-only .env")
    ct = sub.add_parser("check-token")
    ct.add_argument("token")
    a = ap.parse_args(argv)
    if a.cmd == "key" and a.action in ("add", "revoke", "rotate") and not a.name:
        ap.error("key add|revoke|rotate needs NAME")
    return {"status": cmd_status, "enable": cmd_enable, "disable": cmd_disable, "key": cmd_key, "check-token": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
