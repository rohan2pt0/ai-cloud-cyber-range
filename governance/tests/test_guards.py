"""governance/guards.py (doc 108): the monthly failure guards. Not enough data is NOT YET, never a pass; runway and burn multiple
come from what was logged; one product or customer carrying the business fails; revenue without a payment reference fails; an
independent review is needed once revenue is material; a product past its stop test needs a decision; a platform shift not reviewed
in a quarter fails; a marketing word the code cannot prove fails. All numbers here are fake."""
import datetime as dt
import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("securax_guards_t", ROOT / "governance" / "guards.py")
gd = importlib.util.module_from_spec(_s)
_s.loader.exec_module(gd)
NOW = dt.date(2026, 10, 22)


@pytest.fixture
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    monkeypatch.setenv("SECURAX_TODAY", NOW.isoformat())

    def write(log, **plan):
        (tmp_path / "venture.json").write_text(json.dumps({"log": log, "plan": plan}))
    return write


def by(res):
    return {r["id"]: r for r in res}


def e(kind, amount, days_ago, **tags):
    return {"d": (NOW - dt.timedelta(days=days_ago)).isoformat(), "kind": kind, "amount": amount, "what": "fake", **tags}


def test_nothing_logged_is_not_yet_never_a_pass(vault):
    vault([])
    r = by(gd.check(NOW))
    for gid in ("runway", "burn-multiple", "product-share", "customer-share", "revenue-proof", "independent-review"):
        assert r[gid]["state"] == "notyet", gid


def test_runway_comes_from_cash_and_the_last_quarters_net_burn(vault):
    vault([e("money", 100000, 10), e("money", 100000, 40), e("money", 100000, 70)], cash=1200000)   # Rs 1 lakh a month net burn
    assert by(gd.check(NOW))["runway"]["state"] == "pass"                                          # 12 months
    vault([e("money", 100000, 10), e("money", 100000, 40), e("money", 100000, 70)], cash=500000)
    assert by(gd.check(NOW))["runway"]["state"] == "fail"                                          # 5 months, under half the line


def test_one_product_or_one_customer_carrying_the_business_fails(vault):
    vault([e("revenue", 90000, 5, product="readiness", customer="Fake NBFC A", ref="INV-1"),
           e("revenue", 10000, 6, product="shield", customer="Fake Firm B", ref="INV-2")])
    r = by(gd.check(NOW))
    assert r["product-share"]["state"] == "fail" and "readiness 90.0%" in r["product-share"]["value"]
    assert r["customer-share"]["state"] == "fail" and r["revenue-proof"]["state"] == "pass"


def test_revenue_without_a_payment_reference_fails(vault):
    vault([e("revenue", 50000, 5, product="readiness"), e("revenue", 50000, 6, ref="UTR-FAKE")])
    assert by(gd.check(NOW))["revenue-proof"]["state"] == "fail"


def test_an_independent_review_is_needed_once_revenue_is_material(vault):
    big = [e("revenue", 2500000, 30, ref="INV-9")]
    vault(big)
    assert by(gd.check(NOW))["independent-review"]["state"] == "fail"
    vault(big, last_independent_review="2026-04-01")
    assert by(gd.check(NOW))["independent-review"]["state"] == "pass"


def test_a_stop_test_past_its_date_and_a_stale_shift_fail(vault, monkeypatch, tmp_path):
    vault([])
    prods = tmp_path / "products.json"
    prods.write_text(json.dumps({"products": [{"id": "old-bet", "kill_if": "No sale by 2026-01-31"}]}))
    shifts = tmp_path / "shifts.json"
    shifts.write_text(json.dumps({"shifts": [{"id": "x", "reviewed": "2026-01-01"}]}))
    monkeypatch.setattr(gd, "PRODUCTS", prods)
    monkeypatch.setattr(gd, "SHIFTS", shifts)
    monkeypatch.setattr(gd, "SITE", tmp_path / "site")
    r = by(gd.check(NOW, root=tmp_path))
    assert r["stop-tests"]["state"] == "fail" and "old-bet" in r["stop-tests"]["value"]
    assert r["shift-watch"]["state"] == "fail"


def test_a_marketing_word_the_code_cannot_prove_fails(vault, monkeypatch, tmp_path):
    vault([])
    (tmp_path / "site").mkdir()
    (tmp_path / "site" / "index.html").write_text("<h1>The world's best, <b>unhackable</b> AI firewall</h1><style>a{color:#13294b}</style>")
    (tmp_path / "products.json").write_text(json.dumps({"products": []}))
    monkeypatch.setattr(gd, "SITE", tmp_path / "site")
    monkeypatch.setattr(gd, "PRODUCTS", tmp_path / "products.json")
    r = by(gd.check(NOW, root=tmp_path))["claims"]
    assert r["state"] == "fail" and "world's best" in r["why"] and "unhackable" in r["why"]


def test_the_real_estate_makes_no_unprovable_claim_today(vault):
    vault([])
    assert by(gd.check(NOW))["claims"]["state"] == "pass", by(gd.check(NOW))["claims"]["why"]


def test_debt_and_undisclosed_related_party_money_fail(vault):
    vault([e("money", 50000, 5, related="Fake Family Firm"), e("money", 10000, 6, related="Fake Own Co", disclosed="adviser e-mail")],
          debt=500000)
    r = by(gd.check(NOW))
    assert r["debt"]["state"] == "fail" and r["related-party"]["state"] == "fail" and "1 of 2" in r["related-party"]["value"]
    vault([e("money", 10000, 6, related="Fake Own Co", disclosed="adviser e-mail")])
    r = by(gd.check(NOW))
    assert r["debt"]["state"] == "pass" and r["related-party"]["state"] == "pass"


def test_a_handover_note_is_needed_and_kept_current(vault, tmp_path):
    vault([])
    assert by(gd.check(NOW))["key-person"]["state"] == "fail"
    (tmp_path / "handover.md").write_text("keys, accounts, customers, who to call (fake)")
    assert by(gd.check(dt.date.today()))["key-person"]["state"] == "pass"


def test_venture_log_keeps_the_tags_on_the_right_kind_of_entry(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    _v = importlib.util.spec_from_file_location("securax_venture_tags_t", ROOT / "governance" / "venture.py")
    v = importlib.util.module_from_spec(_v)
    _v.loader.exec_module(v)
    assert v.main(["log", "revenue", "1000", "fake", "--product", "shield", "--ref", "INV-1"]) == 0
    assert v.main(["log", "money", "500", "fake", "--related", "Fake Co", "--disclosed", "minute 3"]) == 0
    log = json.loads((tmp_path / "venture.json").read_text())["log"]
    assert log[0]["product"] == "shield" and log[0]["ref"] == "INV-1" and "related" not in log[0]
    assert log[1]["related"] == "Fake Co" and log[1]["disclosed"] == "minute 3" and "product" not in log[1]
