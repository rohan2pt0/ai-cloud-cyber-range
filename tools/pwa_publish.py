#!/usr/bin/env python3
"""Publish the Life OS and Vantage PWAs as static files, so they have a home that is not one machine (doc 130).

The Life OS (the Guiding Map) and Vantage (the CISO edition) are single-page, offline-first apps whose data lives on the device
(and in your own encrypted OneDrive copy, doc 72). They only ever needed somewhere to be LOADED from, and that was the laptop:
when it died, the app stopped. This copies the committed builds into the static site, where GitHub Pages (or any static host:
Cloudflare Pages, Netlify, S3) serves them with HTTPS, so they install on every device and update by themselves.

  python3 tools/pwa_publish.py [OUTDIR]       default: website   ->  OUTDIR/app/ (Life OS) and OUTDIR/vantage/ (Vantage)

`website/build.sh` runs it, so the Pages deploy carries the apps with no extra step. It writes build.json from the real commit,
so the service worker's cache is renamed on every release and a device picks up the new build by itself. Nothing personal is
published: the apps are already public in this repository, and a person's data never leaves their device unencrypted.
Standard library only.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GM = ROOT / "guiding-map"

# What each app needs at run time (an allowlist: tests, node_modules and build sources are never published).
LIFE_OS_FILES = ["index.html", "manifest.json", "sw.js", "features.js", "icon-192.png", "icon-512.png"]
LIFE_OS_DIRS = ["fonts", "ocr"]                  # the font licence travels with the embedded font; ocr/ is the on-device document reader
VANTAGE_FILES = ["index.html", "manifest.json", "sw.js", "icon-192.png", "icon-512.png"]


def _buildinfo() -> dict:
    spec = importlib.util.spec_from_file_location("securax_buildinfo", ROOT / "governance" / "buildinfo.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.info(ROOT)


def _copy(src_dir: pathlib.Path, dst: pathlib.Path, files: list[str], dirs: list[str]) -> list[str]:
    dst.mkdir(parents=True, exist_ok=True)
    missing = []
    for name in files:
        s = src_dir / name
        if s.is_file():
            shutil.copy2(s, dst / name)
        else:
            missing.append(name)
    for name in dirs:
        s = src_dir / name
        if s.is_dir():
            if (dst / name).exists():
                shutil.rmtree(dst / name)
            shutil.copytree(s, dst / name, ignore=shutil.ignore_patterns("node_modules", "*.map", ".DS_Store"))
        else:
            missing.append(name + "/")
    return missing


# The app's "All Apps" button opens the Command Center (hub.html), which only exists on a SecuRAX node. A static host has no node,
# so it gets this honest landing page instead of a dead link.
HUB_STUB = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>All Apps</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0d1f35;color:#eef3f8;font:16px/1.5 system-ui,sans-serif}
main{max-width:34rem;padding:1.5rem}a{color:#c9a84c}h1{font-size:1.4rem;margin:0 0 .75rem}</style></head>
<body><main><h1>All Apps lives on your own SecuRAX node</h1>
<p>This copy of the Life OS is hosted so it opens on any device, even with every machine off. The Command Center (chat, the
AI gateway, the other apps) runs on your own laptop or server.</p>
<p>Open it at that machine's address. Your Life OS data stays on this device, and in your own encrypted sync copy if you turned it on.</p>
<p><a href="index.html">&larr; Back to the Life OS</a></p></main></body></html>
"""


def publish(out: pathlib.Path) -> dict:
    """Copy both apps under `out` and return {"app": [...missing], "vantage": [...missing], "build": {...}}."""
    info = _buildinfo()
    result = {"app": _copy(GM, out / "app", LIFE_OS_FILES, LIFE_OS_DIRS),
              "vantage": _copy(GM / "vantage", out / "vantage", VANTAGE_FILES, []), "build": info}
    for sub in ("app", "vantage"):
        (out / sub / "build.json").write_text(json.dumps(info, indent=1) + "\n", "utf-8")
    (out / "app" / "hub.html").write_text(HUB_STUB, "utf-8")
    return result


def main(argv: list[str]) -> int:
    out = pathlib.Path(argv[0]) if argv else ROOT / "website"
    res = publish(out)
    bad = {k: v for k, v in res.items() if k in ("app", "vantage") and v}
    if bad:
        print(f"✘ the app build is incomplete (run `node build.js` in guiding-map/): missing {bad}")
        return 1
    print(f"published the Life OS to {out / 'app'} and Vantage to {out / 'vantage'}  (build {res['build']['label']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
