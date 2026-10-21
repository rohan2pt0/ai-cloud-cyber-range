"""One place that says where a person opens each part of the estate (doc 99): https://NAME.<domain> with names on, the plain
http://localhost:PORT only while they are off. The shell's web_url() does the same. Never print a raw localhost:PORT
for a person to open: call web_url() instead (fitness `no-raw-addresses` fails a new one)."""
from __future__ import annotations

import os
import pathlib

ENVF = pathlib.Path(__file__).resolve().parent.parent / "local" / "compose" / ".env"


def _env() -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        for ln in ENVF.read_text("utf-8").splitlines():
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def names_on(env: dict[str, str] | None = None) -> bool:
    return "tls.yml" in (env if env is not None else _env()).get("COMPOSE_FILE", "")


def web_url(name: str, port: int, path: str = "/", env: dict[str, str] | None = None) -> str:
    env = env if env is not None else _env()
    if names_on(env):
        dom = os.environ.get("SECURAX_DOMAIN") or env.get("SECURAX_DOMAIN") or "securax.localhost"
        return f"https://{name}.{dom}{path}"
    return f"http://localhost:{port}{path}"
