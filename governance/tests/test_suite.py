"""The suite (doc 97): every feature is declared with an edition and platform services; a service claimed as built is proven
by files that exist; the open core holds (identity and export open and free, the first edition stands only on open
services, commercial code has no evidence in the public repository); editions nest; and a datasheet sells only what is built."""
import copy
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("suite", ROOT / "governance" / "suite.py")
su = importlib.util.module_from_spec(_s)
_s.loader.exec_module(su)


def test_the_suite_is_sound_and_every_feature_is_declared():
    assert su.check() == []
    assert set(su.load()["components"]) == set(su.features())


def test_an_undeclared_feature_fails():
    feats = dict(su.features())
    feats["brand-new"] = {"id": "brand-new", "name": "Brand new"}
    assert any("brand-new is not declared" in e for e in su.check(feats=feats))


def test_a_claim_without_its_files_fails():
    s = copy.deepcopy(su.load())
    s["services"]["audit"]["evidence"] = ["governance/does_not_exist.py"]
    assert any("does not exist" in e for e in su.check(s))
    s = copy.deepcopy(su.load())
    s["services"]["tenancy"]["status"] = "built"
    s["services"]["tenancy"]["evidence"] = []
    assert any("names the files" in e for e in su.check(s))


def test_the_open_core_holds():
    s = copy.deepcopy(su.load())
    s["services"]["identity"]["open"] = False          # an SSO tax
    errs = " ".join(su.check(s))
    assert "identity must be open" in errs and "closed" in errs
    s = copy.deepcopy(su.load())
    s["services"]["scim"]["evidence"] = ["governance/suite.py"]   # commercial code in the public repo
    assert any("private repository" in e for e in su.check(s))


def test_editions_nest_and_name_their_gaps():
    s = copy.deepcopy(su.load())
    s["editions"][2]["requires"] = ["identity"]         # business without what pro has
    assert any("must include everything" in e for e in su.check(s))
    s = copy.deepcopy(su.load())
    s["services"]["rbac"].pop("target")
    assert any("target date" in e for e in su.check(s))


def test_readiness_follows_what_is_built():
    s = su.load()
    a = su.analyse(s)
    eds = {e["id"]: e for e in a["editions"]}
    assert eds["community"]["sellable"] and eds["community"]["ready"] == 100
    assert not eds["enterprise"]["sellable"] and "scim" in eds["enterprise"]["blocked_by"]
    t = copy.deepcopy(s)
    for v in t["services"].values():
        v["status"] = "built"
    assert all(e["sellable"] for e in su.analyse(t)["editions"])


def test_a_datasheet_sells_only_what_is_built(capsys):
    assert su.main(["sheet", "enterprise"]) == 0
    out = capsys.readouterr().out
    inc, way = out.split("## On the way")[0], out.split("## On the way")[1].split("## Every component")[0]
    assert "SCIM" in way and "SCIM" not in inc and "Identity" in inc
    assert "open-core promise" in out and "No SSO tax" in out
    assert su.main(["sheet", "nonsense"]) == 2
