#!/usr/bin/env python3
"""Publish the Life OS and Vantage PWAs as static files, so they have a home that is not one machine (doc 130).

The Life OS (the Guiding Map) and Vantage (the CISO edition) are single-page, offline-first apps whose data lives on the device
(and in your own encrypted OneDrive copy, doc 72). They only ever needed somewhere to be LOADED from, and that was the laptop:
when it died, the app stopped. This copies the committed builds into the static site, where GitHub Pages (or any static host:
Cloudflare Pages, Netlify, S3) serves them with HTTPS, so they install on every device and update by themselves.

  python3 tools/pwa_publish.py [OUTDIR]       default: website   ->  OUTDIR/app/ (Life OS), OUTDIR/vantage/ (Vantage) and
                                              OUTDIR/command/ (the Command Center door, doc 131)

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
COMMAND_FILES = ["index.html", "door.css", "door-logic.js", "door.js", "manifest.json", "sw.js"]   # its icons are the Life OS's: one copy in the repo
COMMAND_ICONS = ["icon-192.png", "icon-512.png"]


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
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b1a2e"><title>All Apps</title>
<style>
@font-face{font-family:"Instrument Serif";src:url("../command/serif.woff2") format("woff2");font-display:swap}
:root{--ink:#eef3f8;--mute:#a9b6cc;--gold:#d9b75a;--hair:rgba(217,183,90,.35);--glass:rgba(255,255,255,.055);--glassB:rgba(255,255,255,.12)}
*{box-sizing:border-box}
html{background:#07101f}
body{margin:0;min-height:100vh;color:var(--ink);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,system-ui,sans-serif;
 background:radial-gradient(1px 1px at 12% 18%,rgba(255,255,255,.7),transparent 60%),radial-gradient(1px 1px at 78% 9%,rgba(255,255,255,.55),transparent 60%),
 radial-gradient(1.2px 1.2px at 64% 31%,rgba(255,255,255,.5),transparent 60%),radial-gradient(1px 1px at 30% 46%,rgba(255,255,255,.4),transparent 60%),
 radial-gradient(1px 1px at 88% 58%,rgba(255,255,255,.45),transparent 60%),radial-gradient(1px 1px at 8% 72%,rgba(255,255,255,.35),transparent 60%),
 radial-gradient(120% 70% at 50% -10%,#1d3557 0%,#0e1f38 45%,#07101f 100%);background-attachment:fixed}
main{max-width:30rem;margin:0 auto;padding:max(2.2rem,env(safe-area-inset-top)) 1.1rem 2.5rem}
.crest{display:grid;place-items:center;margin:.4rem 0 1.1rem}
.crest img{width:84px;height:84px;border-radius:22px;box-shadow:0 0 0 1px var(--hair),0 14px 40px rgba(217,183,90,.22),0 6px 18px rgba(0,0,0,.5)}
.kick{text-align:center;font-size:.72rem;letter-spacing:.28em;text-transform:uppercase;color:var(--gold);margin:0 0 .35rem}
h1{font-family:"Instrument Serif",Georgia,serif;font-weight:400;font-size:2.35rem;line-height:1.08;text-align:center;margin:0 0 .6rem;
 background:linear-gradient(180deg,#fff 0%,#f4e7c1 55%,#d9b75a 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.lede{text-align:center;color:var(--mute);margin:0 auto 1.4rem;max-width:24rem}
.cta{display:flex;align-items:center;justify-content:center;gap:.5rem;min-height:52px;border-radius:16px;text-decoration:none;font-weight:800;color:#1a1305;
 background:linear-gradient(135deg,#7a5a14 0%,#c9a24a 20%,#f7e7a8 38%,#d4af37 52%,#9c7a26 72%,#ecd27e 90%,#b8902f 100%);
 box-shadow:inset 0 1px 0 rgba(255,255,255,.55),0 10px 28px rgba(217,183,90,.28)}
.cta:active{transform:scale(.98)}
.sub{display:block;text-align:center;color:var(--mute);font-size:.82rem;margin:.55rem 0 1.6rem}
h2{font-size:.72rem;letter-spacing:.22em;text-transform:uppercase;color:var(--mute);font-weight:700;margin:1.4rem 0 .6rem;display:flex;align-items:center;gap:.6rem}
h2::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,var(--hair),transparent)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:.65rem}
.card{position:relative;display:block;padding:.95rem .9rem;border-radius:18px;text-decoration:none;color:var(--ink);background:var(--glass);
 border:1px solid var(--glassB);box-shadow:inset 0 1px 0 rgba(255,255,255,.06);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px)}
.card b{display:block;font-size:.95rem;margin:.55rem 0 .15rem}.card span{display:block;font-size:.78rem;color:var(--mute);line-height:1.4}
.ready{border-color:var(--hair);background:linear-gradient(160deg,rgba(217,183,90,.14),rgba(255,255,255,.04))}
.ready::after{content:"Open";position:absolute;top:.8rem;inset-inline-end:.85rem;font-size:.68rem;font-weight:800;letter-spacing:.08em;color:var(--gold)}
.node::after{content:"";position:absolute;top:.85rem;inset-inline-end:.9rem;width:.5rem;height:.5rem;border-radius:50%;border:1.5px solid var(--mute)}
.card .med,.med{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;
 background:radial-gradient(120% 120% at 30% 25%,#2a3a5c,#16213b 60%,#0e172c);box-shadow:inset 0 0 0 1px rgba(217,183,90,.7)}
.med svg{width:19px;height:19px;stroke:var(--gold);fill:none;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.safe{display:flex;gap:.7rem;align-items:flex-start;margin-top:1.6rem;padding:.9rem 1rem;border-radius:16px;border:1px solid var(--glassB);background:rgba(0,0,0,.18);font-size:.84rem;color:var(--mute)}
.safe svg{flex:none;width:20px;height:20px;stroke:var(--gold);fill:none;stroke-width:1.6;margin-top:.1rem}
.back{display:flex;align-items:center;justify-content:center;min-height:48px;margin-top:1.2rem;color:var(--ink);text-decoration:none;font-weight:700;border-radius:14px;border:1px solid var(--hair)}
a:focus-visible{outline:2px solid var(--gold);outline-offset:3px}
@media (max-width:340px){.grid{grid-template-columns:1fr}}
@media (prefers-reduced-motion:no-preference){main{animation:rise .6s cubic-bezier(.2,.7,.2,1) both}@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}}
</style></head>
<body><main>
<div class="crest"><img src="icon-192.png" alt="" width="84" height="84"></div>
<p class="kick">Your estate</p>
<h1>Every app, one door</h1>
<p class="lede">This Life OS is hosted, so it opens anywhere, even with every machine off. The rest of the estate lives on your own SecuRAX node.</p>
<a class="cta" href="../command/index.html">Open my Command Center <span aria-hidden="true">&rarr;</span></a>
<span class="sub">The door finds whichever of your machines is up and opens it.</span>

<h2>Ready here</h2>
<div class="grid">
<a class="card ready" href="index.html"><span class="med"><svg viewBox="0 0 24 24"><path d="M12 3l2.2 6.8H21l-5.5 4 2.1 6.7L12 16.4 6.4 20.5l2.1-6.7L3 9.8h6.8z"/></svg></span><b>Life OS</b><span>Your goals, money, health and risks</span></a>
<a class="card ready" href="../vantage/index.html"><span class="med"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="3"/><path d="M12 3.5v3M12 17.5v3M3.5 12h3M17.5 12h3"/></svg></span><b>Vantage</b><span>The leader's view: see far, decide well</span></a>
</div>

<h2>On your node</h2>
<div class="grid">
<a class="card node" href="../command/index.html"><span class="med"><svg viewBox="0 0 24 24"><path d="M4 5h16v11H9l-5 4z"/></svg></span><b>Ask</b><span>Chat with your own AI, behind its rails</span></a>
<a class="card node" href="../command/index.html"><span class="med"><svg viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z"/></svg></span><b>Practise and defend</b><span>The cyber range, drills and hunts</span></a>
<a class="card node" href="../command/index.html"><span class="med"><svg viewBox="0 0 24 24"><path d="M5 20h14M7 20V10M12 20V10M17 20V10M4 10l8-6 8 6"/></svg></span><b>Comply and govern</b><span>Controls, evidence and regulators</span></a>
<a class="card node" href="../command/index.html"><span class="med"><svg viewBox="0 0 24 24"><path d="M3 12h4l3-7 4 14 3-7h4"/></svg></span><b>Keep it running</b><span>Health, backups and recovery</span></a>
</div>

<p class="safe"><svg viewBox="0 0 24 24"><rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg><span>Your Life OS data stays on this device, and in your own encrypted sync copy if you turned it on. Nothing here signs you in or tracks you.</span></p>
<a class="back" href="index.html">&larr;&nbsp; Back to the Life OS</a>
</main></body></html>
"""


def publish(out: pathlib.Path) -> dict:
    """Copy both apps under `out` and return {"app": [...missing], "vantage": [...missing], "build": {...}}."""
    info = _buildinfo()
    result = {"app": _copy(GM, out / "app", LIFE_OS_FILES, LIFE_OS_DIRS),
              "vantage": _copy(GM / "vantage", out / "vantage", VANTAGE_FILES, []),
              "command": _copy(GM / "command", out / "command", COMMAND_FILES, []), "build": info}
    for icon in COMMAND_ICONS:
        if (GM / icon).is_file():
            shutil.copy2(GM / icon, out / "command" / icon)
        else:
            result["command"].append(icon)
    font = ROOT / "guiding-map" / "fonts" / "InstrumentSerif-Regular.woff2"   # the door's serif: one copy in the repo
    if font.is_file():
        shutil.copy2(font, out / "command" / "serif.woff2")
    else:
        result["command"].append("serif.woff2")
    for sub in ("app", "vantage", "command"):
        (out / sub / "build.json").write_text(json.dumps(info, indent=1) + "\n", "utf-8")
    (out / "app" / "hub.html").write_text(HUB_STUB, "utf-8")
    return result


def main(argv: list[str]) -> int:
    out = pathlib.Path(argv[0]) if argv else ROOT / "website"
    res = publish(out)
    bad = {k: v for k, v in res.items() if k in ("app", "vantage", "command") and v}
    if bad:
        print(f"✘ the app build is incomplete (run `node build.js` in guiding-map/): missing {bad}")
        return 1
    print(f"published the Life OS to {out / 'app'}, Vantage to {out / 'vantage'} and the Command Center door to {out / 'command'}  (build {res['build']['label']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
