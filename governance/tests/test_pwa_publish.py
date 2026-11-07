"""The Life OS and Vantage are published as static files (doc 130), so they open on any device with no machine of yours running.
The point of the test: the published copy must work from a SUBPATH (GitHub Pages serves a project at /<repo>/app/), install and
update by itself, and never carry tests or build sources. No network, no browser (the real-browser proof is in the PR)."""
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("pwa_publish", ROOT / "tools" / "pwa_publish.py")
pp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pp)


def _publish(tmp_path):
    res = pp.publish(tmp_path)
    assert res["app"] == [] and res["vantage"] == [], f"incomplete build: {res}"
    return res


def test_both_apps_are_published_with_everything_they_need(tmp_path):
    _publish(tmp_path)
    for name in ("index.html", "manifest.json", "sw.js", "icon-192.png", "icon-512.png", "build.json"):
        assert (tmp_path / "app" / name).is_file(), f"app/{name}"
        assert (tmp_path / "vantage" / name).is_file(), f"vantage/{name}"
    assert (tmp_path / "app" / "features.js").is_file()
    assert (tmp_path / "app" / "fonts").is_dir() and (tmp_path / "app" / "ocr").is_dir()


def test_nothing_that_is_not_the_app_is_published(tmp_path):
    _publish(tmp_path)
    published = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()}
    names = {pathlib.PurePosixPath(f).name for f in published}
    for bad in ("build.js", "package.json", "package-lock.json", "ops.js", ".env"):
        assert bad not in names, f"{bad} must not be published"            # exact names: build.json IS published, build.js is not
    for bad_dir in ("node_modules", "tests"):
        assert not any(bad_dir in pathlib.PurePosixPath(f).parts for f in published), f"{bad_dir}/ must not be published"


def test_the_build_json_carries_the_real_commit_so_devices_update_themselves(tmp_path):
    res = _publish(tmp_path)
    for sub in ("app", "vantage"):
        b = json.loads((tmp_path / sub / "build.json").read_text("utf-8"))
        assert b["commit"] and re.fullmatch(r"[0-9a-f]{7,}", b["commit"]), b
        assert b == res["build"]
    # the service worker names its cache after this, so a new commit installs a new worker and drops the old cache
    assert "searchParams.get(\"b\")" in (tmp_path / "app" / "sw.js").read_text("utf-8")


def test_the_published_apps_work_from_a_subpath(tmp_path):
    """GitHub Pages serves a project site at /<repo>/app/, so nothing may point at the site root."""
    _publish(tmp_path)
    for sub in ("app", "vantage"):
        html = (tmp_path / sub / "index.html").read_text("utf-8")
        rooted = re.findall(r'(?:src|href)="(/[^"]*)"', html)
        assert not rooted, f"{sub}/index.html has root-absolute references that break under a subpath: {rooted[:3]}"
        m = json.loads((tmp_path / sub / "manifest.json").read_text("utf-8"))
        assert not m["start_url"].startswith("/") and not m.get("scope", "./").startswith("/"), m
        for icon in m["icons"]:
            assert not icon["src"].startswith("/"), icon
            assert (tmp_path / sub / icon["src"]).is_file(), f"{sub}: manifest icon {icon['src']} missing"


def test_the_offline_shell_is_all_there(tmp_path):
    """Every file the service worker precaches must be published, except the Command Center's own manifest (a node-only file;
    the worker tolerates a miss by design)."""
    _publish(tmp_path)
    sw = (tmp_path / "app" / "sw.js").read_text("utf-8")
    shell = re.findall(r'"\./([^"]*)"', sw.split("const SHELL = [")[1].split("];")[0])
    missing = [f for f in shell if f and not (tmp_path / "app" / f).exists()]
    assert set(missing) <= {"hub.webmanifest"}, f"the offline shell names files that are not published: {missing}"


def test_all_apps_has_an_honest_landing_page_not_a_dead_link(tmp_path):
    """The app's All Apps button opens hub.html (the Command Center), which only a SecuRAX node has: a static host serves a
    landing page that says so and links back."""
    _publish(tmp_path)
    stub = (tmp_path / "app" / "hub.html").read_text("utf-8")
    assert "your own SecuRAX node" in stub and 'href="index.html"' in stub


def test_an_incomplete_app_build_is_refused(tmp_path, monkeypatch):
    # an empty guiding-map (no `node build.js` yet) must fail the build, never publish a broken app
    monkeypatch.setattr(pp, "GM", tmp_path / "empty-guiding-map")
    (tmp_path / "empty-guiding-map" / "vantage").mkdir(parents=True)
    assert pp.main([str(tmp_path / "site")]) == 1


def test_the_build_script_publishes_the_apps_and_git_ignores_the_output():
    build = (ROOT / "website" / "build.sh").read_text("utf-8")
    assert "tools/pwa_publish.py website" in build
    assert build.index("pwa_publish.py") < build.index("linkcheck.py"), "publish before the link check, so the check covers it"
    ignore = (ROOT / ".gitignore").read_text("utf-8")
    assert "website/app/" in ignore and "website/vantage/" in ignore, "generated apps must stay out of git"
    docs = (ROOT / ".github" / "workflows" / "docs.yml").read_text("utf-8")
    assert docs.count('"guiding-map/**"') == 2, "a PWA change must republish the site (pull_request and push)"
