"""New features are noticed (doc 95, section 8): every feature carries the day it shipped; every generated page lists the latest
additions (a fixed count, so pages never go stale by themselves); the Command Center marks a feature New for 30 days; and the
weekly progress message names what is new so a person tries it."""
import importlib.util
import json
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _mod(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


fs = _mod("features_sync", "tools/features_sync.py")
pg = _mod("progress_mod", "governance/progress.py")


def test_every_feature_says_when_it_shipped():
    data = fs.load()
    assert all(len(f["added"]) == 10 for f in data["features"])
    bad = json.loads(json.dumps(data))
    bad["features"][0].pop("added")
    assert any("needs 'added'" in p for p in fs.problems(bad))


def test_pages_list_the_latest_additions_newest_first():
    data = fs.load()
    top = fs.latest(data)
    assert len(top) == 5 and [f["added"] for f in top] == sorted((f["added"] for f in top), reverse=True)
    for block in (fs.block_docs(data), fs.block_readme(data)):
        assert "New in the estate" in block and top[0]["name"] in block
    assert "NEW IN THE ESTATE" in fs.listing(data)


def test_the_command_center_marks_new_features_at_view_time():
    hub = (ROOT / "guiding-map" / "hub.html").read_text()
    assert "function isNew" in hub and 'class="lt new"' in hub and 'id="whatsnew"' in hub
    assert '"added"' in fs.hub_js(fs.load())


def test_the_weekly_message_names_what_is_new():
    later = time.mktime(time.strptime("2099-01-01", "%Y-%m-%d"))
    assert pg.new_features(later) == []                         # nothing is new forever
    now = time.time()
    fresh = pg.new_features(now)
    newest = max(f["added"] for f in fs.load()["features"])
    if newest >= time.strftime("%Y-%m-%d", time.gmtime(now - 30 * 86400)):
        assert fresh and fresh[0]["added"] == newest
        p = {"rhythm": {}, "stronger": {"drills_passed": 0, "failures_recovered": 0}, "next": None, "nudges": [], "new": fresh}
        assert "New: " in pg.short(p)
