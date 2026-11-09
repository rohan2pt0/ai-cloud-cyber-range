"""Installability gate — keep the Life OS installable as a phone app on every change.

A phone can offer "Add to Home Screen" only while four things hold: the manifest names the
app and starts standalone, its icons exist on disk, the service worker installs and fetches
(offline), and the page registers that worker and links the manifest. A change that quietly
breaks one of them (a renamed icon, a dropped listener) is invisible until a phone refuses
to install — so it is checked here, from the files, with no browser.
"""
import json
import pathlib
import re

GM = pathlib.Path(__file__).resolve().parents[1]


def _load_json(name):
    try:
        return json.loads((GM / name).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise AssertionError(f"guiding-map/{name} is not valid JSON ({e}) — fix the syntax") from e


def _icon_srcs(data, size):
    # src may be "icon-192.png" or "./icon-192.png"; sizes may list several ("192x192 256x256").
    out = []
    for icon in data.get("icons", []):
        if size in str(icon.get("sizes", "")).split():
            src = str(icon.get("src", ""))
            if src.startswith("./"):
                src = src[2:]
            out.append(src)
    return out


def _icon_exists(src):
    p = (GM / src).resolve()
    return p.is_file() and GM in p.parents  # never follow a src that escapes guiding-map/


def test_manifest_names_the_app_and_starts_standalone():
    m = _load_json("manifest.json")
    for field in ("name", "short_name", "start_url"):
        assert m.get(field), f"guiding-map/manifest.json lacks '{field}' — add it, or a phone will not offer install"
    assert m.get("display") == "standalone", \
        "guiding-map/manifest.json: set \"display\": \"standalone\", or the app opens in a browser tab"


def test_manifest_icons_exist_on_disk():
    m = _load_json("manifest.json")
    for size in ("192x192", "512x512"):
        srcs = _icon_srcs(m, size)
        assert srcs, f"guiding-map/manifest.json has no {size} icon entry — add one under \"icons\""
        for src in srcs:
            assert _icon_exists(src), \
                f"guiding-map/manifest.json: icon \"src\": \"{src}\" ({size}) is missing from guiding-map/ — add the file or fix the path"


def test_hub_manifest_is_valid_and_its_icons_exist():
    if not (GM / "hub.webmanifest").exists():
        return
    m = _load_json("hub.webmanifest")
    assert m.get("icons"), "guiding-map/hub.webmanifest has no icons — a phone will not offer install"
    for icon in m["icons"]:
        src = str(icon.get("src", ""))
        if src.startswith("./"):
            src = src[2:]
        assert _icon_exists(src), \
            f"guiding-map/hub.webmanifest: icon \"src\": \"{src}\" is missing from guiding-map/ — add the file or fix the path"


def test_service_worker_installs_and_fetches():
    sw = (GM / "sw.js").read_text(encoding="utf-8")
    for event in ("install", "fetch"):
        assert re.search(r'addEventListener\(\s*["\']' + event + r'["\']', sw), \
            f'guiding-map/sw.js has no "{event}" event listener — without it the app cannot install or work offline'


def test_page_registers_the_worker_and_links_the_manifest():
    idx = (GM / "index.html").read_text(encoding="utf-8")
    assert "navigator.serviceWorker.register" in idx, \
        "guiding-map/index.html never calls navigator.serviceWorker.register — register sw.js, or nothing installs"
    assert re.search(r'<link[^>]+rel=["\']manifest["\']', idx), \
        'guiding-map/index.html does not link the manifest — add <link rel="manifest" href="manifest.json">'
