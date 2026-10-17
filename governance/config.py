#!/usr/bin/env python3
"""Configuration, not code: brand values and optional integrations come from two small files, never from the source.

    ./securax config show                 the values in use and where each came from (brand.env, or your environment)
    ./securax config check                validate both files, and fail if a brand value is hardwired in code
    ./securax config enabled <name>       exit 0 when an integration is switched on (used by `go` and scripts)
    ./securax config render FILE...       replace {{KEY}} placeholders in FILEs with the values (the site build uses it)
    eval "$(python3 governance/config.py env)"   export the values into a shell script

brand.env        KEY=value lines; an environment variable with the same name wins. Every value is optional.
integrations.txt one optional integration per line (comments after #). Missing file = everything on (the old behaviour).
Standard library only. Exit codes: 0 ok, 1 a problem was found, 2 bad usage.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRAND_FILE = ROOT / "brand.env"
INTEGRATIONS_FILE = ROOT / "integrations.txt"
KNOWN = {"tailscale", "ntfy", "webhook", "cron", "regwatch", "backup", "cloudflare-pages", "github", "tls"}
NEUTRAL = {"BRAND_NAME": "", "PRODUCT_NAME": "SecuRAX", "SITE_DOMAIN": "", "CONTACT_EMAIL": "", "REPO_SLUG": "", "IMAGE_REGISTRY": ""}
# Values that must never be written into code: the brand-specific ones (PRODUCT_NAME is the product, so it may appear).
GUARDED = ("BRAND_NAME", "SITE_DOMAIN", "CONTACT_EMAIL")
# Vendor names that must stay "good to have": they may be named in docs and in brand/integration files, not in code paths.
VENDOR_WORDS = ("namecheap", "godaddy", "hostinger")
# Where a literal is allowed: legal and human text, the two config files, the history, and this checker itself.
ALLOWED = re.compile(r"(^|/)(LICENSE|MAINTAINERS\.md|CHANGELOG\.md|brand\.env|integrations\.txt)$|\.md$|^docs/|^vendor/|"
                     r"^governance/config\.py$|^governance/tests/test_config\.py$")
CODE = re.compile(r"\.(py|sh|js|mjs|html|css|ya?ml|json|toml|tf|cmd|bat|conf|txt)$|(^|/)(securax|_headers|Dockerfile)$")
_LINE = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$")


def load(path: pathlib.Path | None = None, environ: dict | None = None) -> dict[str, tuple[str, str]]:
    """{KEY: (value, source)}; source is 'environment', 'brand.env' or 'default'."""
    environ = os.environ if environ is None else environ
    out = {k: (v, "default") for k, v in NEUTRAL.items()}
    try:
        for line in (path or BRAND_FILE).read_text("utf-8").splitlines():
            m = _LINE.match(line.split(" #")[0])
            if m:
                out[m.group(1)] = (m.group(2).strip().strip('"').strip("'"), "brand.env")
    except OSError:
        pass
    for k in list(out):
        if environ.get(k):
            out[k] = (environ[k], "environment")
    return out


def values(**kw) -> dict[str, str]:
    return {k: v for k, (v, _) in load(**kw).items()}


def integrations(path: pathlib.Path | None = None) -> set[str] | None:
    """The switched-on integrations, or None when there is no integrations.txt (then everything is on)."""
    try:
        text = (path or INTEGRATIONS_FILE).read_text("utf-8")
    except OSError:
        return None
    return {ln.split("#")[0].strip().lower() for ln in text.splitlines() if ln.split("#")[0].strip()}


def enabled(name: str, path: pathlib.Path | None = None) -> bool:
    on = integrations(path)
    return on is None or name.lower() in on


def render(text: str, vals: dict[str, str]) -> str:
    return re.sub(r"\{\{\s*([A-Z][A-Z0-9_]*)\s*\}\}", lambda m: vals.get(m.group(1), m.group(0)), text)


def problems(vals: dict[str, str], files: list[str], read=lambda p: (ROOT / p).read_text("utf-8", "ignore"),
             on: set[str] | None = None) -> list[str]:
    out = []
    if vals.get("CONTACT_EMAIL") and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", vals["CONTACT_EMAIL"]):
        out.append(f"brand.env: CONTACT_EMAIL is not an e-mail address: {vals['CONTACT_EMAIL']!r}")
    if vals.get("SITE_DOMAIN") and not re.fullmatch(r"(?=.{1,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,63}", vals["SITE_DOMAIN"].lower()):
        out.append(f"brand.env: SITE_DOMAIN is not a domain name (no https://, no path): {vals['SITE_DOMAIN']!r}")
    if vals.get("REPO_SLUG") and not re.fullmatch(r"[\w.-]+/[\w.-]+", vals["REPO_SLUG"]):
        out.append(f"brand.env: REPO_SLUG must look like owner/repo: {vals['REPO_SLUG']!r}")
    for name in sorted((on or set()) - KNOWN):
        out.append(f"integrations.txt: unknown integration {name!r} (known: {', '.join(sorted(KNOWN))})")
    needles = [(k, vals[k]) for k in GUARDED if vals.get(k) and len(vals[k]) >= 4] + [("vendor", w) for w in VENDOR_WORDS]
    for f in files:
        if ALLOWED.search(f) or not CODE.search(f):
            continue
        low = read(f).lower()
        for k, v in needles:
            if v.lower() in low:
                out.append(f"{f}: hardwired {k} {v!r}; use {{{{{k}}}}} or read it from brand.env" if k != "vendor"
                           else f"{f}: names the vendor {v!r} in code; keep vendors optional (integrations.txt / docs)")
    return out


def tracked_files() -> list[str]:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        return []


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "show"
    if cmd == "show":
        for k, (v, src) in load().items():
            print(f"{k:<15} {v or '(not set)':<45} from {src}")
        on = integrations()
        print("\nintegrations: " + ("all (no integrations.txt)" if on is None else ", ".join(sorted(on)) or "none"))
        return 0
    if cmd == "check":
        probs = problems(values(), tracked_files(), on=integrations() or set())
        for p in probs:
            print("✗ " + p)
        print("✔ configuration is clean: no brand value is hardwired in code" if not probs else f"{len(probs)} problem(s)")
        return 1 if probs else 0
    if cmd == "env":
        import shlex
        for k, v in values().items():
            print(f"export {k}={shlex.quote(v)}")
        return 0
    if cmd == "enabled" and len(argv) == 2:
        return 0 if enabled(argv[1]) else 1
    if cmd == "render" and len(argv) >= 2:
        vals = values()
        for f in argv[1:]:
            p = pathlib.Path(f)
            p.write_text(render(p.read_text("utf-8"), vals), "utf-8")
        print(f"rendered {len(argv) - 1} file(s)")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
