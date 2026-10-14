"""The blast-radius map: it must cover every tracked file, name real journeys, and compute downstream impact."""
import importlib.util
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("impact", REPO / "lifecycle" / "impact.py")
im = importlib.util.module_from_spec(spec)
sys.modules["impact"] = im
spec.loader.exec_module(im)

M = {"components": {"a": {"paths": ["src/a/**", "*.cfg"], "guarded_by": ["j1"], "affects": ["b"]}, "b": {"paths": ["src/b/**"], "guarded_by": [], "affects": ["c"]},
                    "c": {"paths": ["src/c/x.py"], "guarded_by": ["j2"], "affects": []}}, "ignore": ["docs/**", "*.md"]}


def test_the_real_map_covers_every_tracked_file_and_names_real_journeys():
    assert im.problems(im.load(), im.tracked(REPO), REPO) == []


def test_patterns():
    assert im.matches("src/a/deep/f.py", "src/a/**") and not im.matches("src/ab/f.py", "src/a/**")
    assert im.matches("x/y/setup.cfg", "*.cfg") and im.matches("src/c/x.py", "src/c/x.py") and not im.matches("src/c/y.py", "src/c/x.py")


def test_unowned_files_and_unknown_journeys_are_reported():
    probs = im.problems(M, ["src/a/f.py", "stray.txt", "docs/x.md"], REPO)
    assert any("stray.txt" in p for p in probs) and not any("docs/x.md" in p for p in probs)
    assert any("'j1'" in p and "does not exist" in p for p in probs)


def test_downstream_closure_and_journeys_and_blind_spots():
    r = im.analyse(["src/a/f.py"], M)
    assert r["touches"] == {"a": 1} and r["also_affected"] == ["b", "c"] and r["run_journeys"] == ["j1", "j2"] and r["blind_spots"] == []
    r = im.analyse(["src/b/f.py", "README.md", "stray.bin"], M)
    assert r["blind_spots"] == ["b"] and r["also_affected"] == ["c"] and r["unowned_files"] == ["stray.bin"]


def test_a_change_to_the_gateway_names_the_journeys_that_prove_it():
    r = im.analyse(["apps/llm-gateway/app/main.py"], im.load())
    assert "gateway" in r["touches"] and {"gateway_identity", "purple_loop"} <= set(r["run_journeys"]) and "router" in r["also_affected"]
