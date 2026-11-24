"""The sandbox runs in parallel shards (sandbox/run.py --shard i/N, the e2e workflow's matrix). Splitting must never drop
or double a journey: every journey runs in exactly one shard, for any N, and the aggregate `sandbox` check fails when
any shard did not pass."""
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _run_py():
    spec = importlib.util.spec_from_file_location("sbx_run_shards", ROOT / "sandbox" / "run.py")
    sys.path.insert(0, str(ROOT / "sandbox"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R = _run_py()
ALL = list(R.JOURNEYS)


@pytest.mark.parametrize("n", range(1, 7))
def test_the_shards_partition_every_journey_for_n_1_to_6(n):
    seconds, groups = R.load_timings()
    shards = R.shard_plan(ALL, n, seconds, groups)
    assert len(shards) == n
    flat = [x for s in shards for x in s]
    assert sorted(flat) == sorted(ALL) and len(flat) == len(set(flat)), "a journey was dropped or doubled"
    for s in shards:                                   # each shard keeps run.py's own order
        assert s == [x for x in ALL if x in s]


@pytest.mark.parametrize("n", range(1, 7))
def test_unknown_journeys_groups_and_an_empty_timings_file_still_partition(n):
    names = ALL + ["brand_new_a", "brand_new_b"]
    for seconds, groups in (({}, []), ({"fresh_install": 900}, [["tls_edge", "tls_internal", "no_such_journey"]])):
        shards = R.shard_plan(names, n, seconds, groups)
        flat = [x for s in shards for x in s]
        assert sorted(flat) == sorted(names) and len(flat) == len(set(flat))
        for g in groups:
            homes = {i for i, s in enumerate(shards) for x in g if x in s}
            assert len(homes) <= 1, "a group was split across shards"


def test_a_new_journey_goes_to_the_lightest_shard():
    shards = R.shard_plan(["a", "b", "c", "new"], 2, {"a": 300, "b": 100, "c": 100})
    assert "new" in shards[1] and shards[0] == ["a"]


def test_the_committed_timings_know_every_journey_and_balance_four_shards():
    seconds, groups = R.load_timings()
    assert set(seconds) == set(ALL), "refresh sandbox/timings.json: " + ", ".join(sorted(set(seconds) ^ set(ALL)))
    loads = [sum(seconds[x] for x in s) for s in R.shard_plan(ALL, 4, seconds, groups)]
    assert max(loads) <= max(max(seconds.values()), sum(loads) / 4) * 1.15


def test_the_plan_cli_names_one_shard_to_save_the_model_cache():
    got = [json.loads(subprocess.run([sys.executable, str(ROOT / "sandbox" / "run.py"), "--shard", f"{i}/4", "--plan"],
                                     capture_output=True, text=True, check=True).stdout) for i in range(1, 5)]
    assert sorted(x for g in got for x in g["journeys"].split(",") if x) == sorted(ALL)
    assert sum(g["saves_models"] for g in got) == 1
    bad = subprocess.run([sys.executable, str(ROOT / "sandbox" / "run.py"), "--shard", "5/4", "--plan"], capture_output=True, text=True)
    assert bad.returncode == 2


def test_the_workflow_runs_the_shards_and_one_sandbox_check_needs_them_all():
    doc = yaml.safe_load((ROOT / ".github" / "workflows" / "e2e.yml").read_text("utf-8"))
    jobs = doc["jobs"]
    shard = jobs["shard"]
    assert shard["strategy"]["fail-fast"] is False
    total = shard["strategy"]["matrix"]["total"]
    assert sorted(shard["strategy"]["matrix"]["shard"]) == list(range(1, total[0] + 1))
    agg = jobs["sandbox"]
    assert agg.get("name", "sandbox") == "sandbox" and agg["needs"] == "shard" and "always()" in agg["if"]
    gate = "\n".join(s.get("run", "") for s in agg["steps"])
    assert re.search(r'needs\.shard\.result \}\}" = success', gate), "the aggregate must pass ONLY when every shard succeeded"
    assert jobs["nightly-alarm"]["needs"] == "sandbox"
