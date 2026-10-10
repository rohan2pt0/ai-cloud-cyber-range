import importlib.util, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("gi", ROOT / "intel" / "global_intel.py")
gi = importlib.util.module_from_spec(spec); sys.modules["gi"] = gi; spec.loader.exec_module(gi)

CCSP = ROOT / "intel" / "examples" / "ccsp-reddit-top.json"
PROFILE = ROOT / "intel" / "examples" / "profile.json"
OPPS = ROOT / "intel" / "examples" / "opportunities.json"


def test_replicate_surfaces_the_real_consensus():
    # The CCSP sample must rank the two things the community keeps repeating on top.
    items = gi.load_items(str(CCSP))
    ranked = gi.extract_consensus(items, vocabulary=["Pete Zerger", "LEARNZAPP", "Sybex", "Mike Chapple"],
                                  mode="replicate")
    top2 = {r["name"] for r in ranked[:2]}
    assert top2 == {"Pete Zerger", "LEARNZAPP"}, ranked
    assert ranked[0]["distinct_sources"] >= 2 and ranked[0]["confidence"] == "high"


def test_two_regimes_weight_oppositely():
    # Old item: proven in replicate (Lindy up), penalised in edge (stale). New item: reverse.
    old_r = gi.signal_weight(score=100, rank=1, age_days=1000, mode="replicate")
    old_e = gi.signal_weight(score=100, rank=1, age_days=1000, mode="edge")
    new_e = gi.signal_weight(score=100, rank=1, age_days=10, mode="edge")
    assert old_r > old_e        # age helps replicate, hurts edge
    assert new_e > old_e        # fresh beats stale in edge mode


def test_consensus_strength_flags_thin_data():
    thin = gi.extract_consensus([{"source": "x", "rank": 1, "score": 5, "text": "Pete Zerger"}],
                                vocabulary=["Pete Zerger"])
    s = gi.consensus_strength(thin, n_items=1)
    assert s["verdict"].startswith("thin")


def test_capability_fit_prefers_my_edge():
    profile = gi.load_items  # noqa: just to ensure import; real load below
    import json
    profile = json.loads(PROFILE.read_text())
    opps = json.loads(OPPS.read_text())
    fits = sorted((gi.capability_fit(o, profile) for o in opps), key=lambda x: x["fit"], reverse=True)
    # The generic Warikoo-style play must NOT win; a BFSI/cyber play should.
    assert "finance influencer" not in fits[0]["name"].lower()
    assert fits[0]["fit"] >= 0.45 and fits[0]["unfair_advantage"]
    # The high-capital, high-risk, out-of-domain option should be weak with blockers.
    warikoo = next(f for f in fits if "influencer" in f["name"].lower())
    assert warikoo["verdict"] == "weak fit" and warikoo["blockers"]


def test_timing_identifies_commoditised_vs_rising():
    rising = gi.commoditization_stage([1, 2, 3, 6, 10, 18])
    saturated = gi.commoditization_stage([90, 95, 100, 98, 99, 97])
    assert rising["stage"] in ("early adopters", "early majority", "innovators")
    assert saturated["stage"] in ("late majority", "laggard / declining")
    assert rising["estimate"] is True


def test_decide_is_grounded_and_has_worst_case():
    items = gi.load_items(str(CCSP))
    out = gi.decide("Pass CCSP", items, mode="replicate",
                    vocabulary=["Pete Zerger", "LEARNZAPP", "Sybex"])
    assert "provided" in out["grounding"]          # never claims invented data
    assert out["worst_case"]["barbell"]            # always a downside plan
    assert out["consensus"][0]["name"] in ("Pete Zerger", "LEARNZAPP")
