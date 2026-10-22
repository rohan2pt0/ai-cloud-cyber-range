"""The chaos runner (doc 101): the same seed gives the same plan; it never starts on an estate that is not normal; every
fault is reverted even when the check blows up; it stops after the first fault the estate does not recover from; and the
plan-only command changes nothing."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("securax_chaos_t", ROOT / "lifecycle" / "chaos.py")
ch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ch)
CAT = {"a": {"what": "A breaks", "service": "sa", "inject": ["kill"], "revert": ["start"], "slo_s": 30},
       "b": {"what": "B breaks", "service": "sb", "inject": ["pause"], "revert": ["unpause"], "slo_s": 30},
       "c": {"what": "C breaks", "service": "sc", "inject": ["kill"], "revert": ["start"], "slo_s": 30}}


class Clock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


def test_the_same_seed_gives_the_same_plan_and_another_seed_varies():
    assert ch.plan(7, 2, CAT) == ch.plan(7, 2, CAT) and len(ch.plan(7, 9, CAT)) == 3
    assert len({tuple(ch.plan(s, 2, CAT)) for s in range(20)}) > 1


def test_an_estate_that_is_not_normal_is_never_broken_further():
    acts = []
    res = ch.run(1, 2, measure=lambda: {"gateway ready": False}, act=lambda a, s: acts.append(a), recover=lambda: None, catalog=CAT)
    assert res["aborted"] and acts == [] and res["results"] == []


def test_each_fault_is_injected_then_reverted_and_recovery_is_timed():
    clk, acts, state = Clock(), [], {"up": True}

    def act(args, svc):
        acts.append((args[0], svc))
        state["up"] = args[0] in ("start", "unpause")

    res = ch.run(3, 3, measure=lambda: {"x": state["up"]}, act=act, recover=lambda: state.update(up=True),
                 clock=clk.now, sleep=clk.sleep, catalog=CAT, settle_s=1)
    assert [r["ok"] for r in res["results"]] == [True, True, True] and res["seed"] == 3
    assert all(r["noticed"] for r in res["results"])                   # the break really showed before recovery
    assert len(acts) == 6 and all(acts[i][0] in ("start", "unpause") for i in range(1, 6, 2))


def test_a_check_that_blows_up_still_reverts_and_stops_the_experiment():
    clk, acts, calls = Clock(), [], {"n": 0}

    def measure():
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("probe crashed")
        return {"x": True}

    res = ch.run(5, 3, measure=measure, act=lambda a, s: acts.append(a[0]), recover=lambda: None,
                 clock=clk.now, sleep=clk.sleep, catalog=CAT, settle_s=1)
    assert len(res["results"]) == 1 and not res["results"][0]["ok"] and "probe crashed" in res["results"][0]["why"]
    assert acts[-1] in ("start", "unpause")


def test_no_recovery_within_the_limit_fails_and_stops():
    clk, acts = Clock(), []
    res = ch.run(2, 3, measure=lambda: {"x": not acts or acts[-1] != "kill" and acts[-1] != "pause"},
                 act=lambda a, s: acts.append(a[0]), recover=lambda: None, clock=clk.now, sleep=clk.sleep, catalog=CAT, settle_s=1)
    assert len(res["results"]) == 1 and not res["results"][0]["ok"] and "still not normal" in res["results"][0]["why"]
    assert acts[-1] in ("start", "unpause")


def test_the_plan_only_command_changes_nothing(capsys, monkeypatch):
    monkeypatch.setattr(ch, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not run")))
    assert ch.main(["--seed", "11", "--faults", "2"]) == 0
    out = capsys.readouterr().out
    assert "nothing is changed" in out and "./securax chaos --run --seed 11" in out
