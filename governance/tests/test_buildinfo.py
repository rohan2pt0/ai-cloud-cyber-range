"""The build label changes with every commit by itself, so nobody has to bump a number to see which code is running."""
import importlib.util
import pathlib
import subprocess

_s = importlib.util.spec_from_file_location("buildinfo", pathlib.Path(__file__).resolve().parent.parent / "buildinfo.py")
bi = importlib.util.module_from_spec(_s)
_s.loader.exec_module(bi)
GM = pathlib.Path(__file__).resolve().parents[2] / "guiding-map"


def test_describe_and_label():
    assert bi.parse_describe("v0.1.0-74-g21006c7") == (74, "21006c7")
    assert bi.parse_describe("21006c7") == (None, "")
    assert bi.label("0.1.0", 74, "21006c7") == "v0.1.0+74 · 21006c7"
    assert bi.label("0.1.0", 0, "abc1234") == "v0.1.0 · abc1234"
    assert bi.label("0.1.0", None, "") == "v0.1.0"


def test_a_new_commit_changes_the_label_without_touching_VERSION(tmp_path):
    g = lambda *a: subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True, capture_output=True)
    g("init", "-q")
    (tmp_path / "VERSION").write_text("1.2.3\n")
    g("add", "."), g("commit", "-qm", "r"), g("tag", "v1.2.3")
    first = bi.info(tmp_path)
    assert first["changes"] == 0 and first["label"].startswith("v1.2.3 · ")
    (tmp_path / "x").write_text("x")
    g("add", "."), g("commit", "-qm", "c")
    second = bi.info(tmp_path)
    assert second["changes"] == 1 and second["commit"] != first["commit"] and second["label"].startswith("v1.2.3+1 · ")


def test_the_life_os_reads_the_build_and_its_offline_cache_follows_it():
    ops, sw = (GM / "ops.js").read_text(), (GM / "sw.js").read_text()
    assert 'fetch("build.json"' in ops and '"sw.js?b="' in ops        # badge + service worker follow the running build
    assert 'searchParams.get("b")' in sw
    assert "v14." not in sw, "a hand-bumped cache version is back: it is derived from the build now"
