#!/usr/bin/env python3
"""ONE switch for a regulated deployment: sign-in required + data residency + the strict cockpit profile.

    ./securax regulated on [--jurisdiction IN] [--enforce]     turns on gateway sign-in, data residency (monitor first; --enforce to block/reroute), strict cockpit
    ./securax regulated off                                    back to the open laptop defaults
    ./securax regulated status

A laptop stays open by default (too much security up front defeats the point of a personal tool). A regulated entity should not have to know four
commands and three files: this does them in order, tells you what it did, and what is still yours (your identity provider settings, your cloud
attestations). Nothing is changed until you restart the estate: `./securax down && ./securax up`. Standard library only.
"""
from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


def _mod(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("action", choices=["on", "off", "status"])
    ap.add_argument("--jurisdiction", default="IN")
    ap.add_argument("--enforce", action="store_true", help="enforce residency now (default: monitor, which logs what it would do and changes nothing)")
    ap.add_argument("--env-file", default="")
    a = ap.parse_args(argv)
    ga, rs = _mod("securax_gwauth", "gateway_auth.py"), _mod("securax_residency_cli", "residency.py")
    env = pathlib.Path(a.env_file or ga.ENV)
    if a.action == "status":
        e = ga.read_env(env)
        print(f"profile={e.get('SECURAX_PROFILE', 'personal')}  sign-in={e.get('AUTH_MODE', 'off')}  residency={e.get('RESIDENCY_MODE', 'off')}")
        return 0
    if a.action == "off":
        ga.set_env(env, "SECURAX_PROFILE", "personal")
        ga.set_env(env, "AUTH_MODE", "off")
        ga.set_env(env, "RESIDENCY_MODE", "off")
        print("Back to the open laptop defaults. Restart:  ./securax down && ./securax up")
        return 0
    ga.set_env(env, "SECURAX_PROFILE", "regulated")
    print("1/3 profile: regulated (the cockpit now treats open sign-in and missing residency as red)")
    ga.main(["--env-file", str(env), "enable"])
    print("2/3 sign-in required (service keys created for the estate's own tools)")
    rs.main(["--env-file", str(env), "enable", "--jurisdiction", a.jurisdiction] + ([] if a.enforce else ["--monitor"]))
    print(f"3/3 data residency for {a.jurisdiction}: {'ENFORCED' if a.enforce else 'MONITOR (logs what it would do; enforce when you are happy: ./securax regulated on --enforce)'}")
    print("\nStill yours: (a) point humans at your identity provider (OIDC_ISSUER / OIDC_AUDIENCE / OIDC_JWKS_URL in local/compose/.env, MFA for admin/auditor),")
    print("             (b) record cloud attestations before waking a cloud stage:  ./securax residency attest <cloud> --ref '<reference>',")
    print("             (c) wire  ./securax incident due  to your alerting.   Then restart:  ./securax down && ./securax up")
    return 0


if __name__ == "__main__":
    sys.exit(main())
