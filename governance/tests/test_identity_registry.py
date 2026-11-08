"""The one door (doc 132, principle `one-door`): a person signs in once, and a new feature that needs a sign-in is ONE ENTRY in
governance/identity.json, never a new login screen or a stored password. The check fails an incomplete entry, an over-broad
permission, an overdue fix date, and any new separate login (the count only goes down). Synthetic registries, no network."""
import datetime
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("fitness_identity", ROOT / "lifecycle" / "fitness.py")
ft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ft)
TODAY = datetime.date(2026, 11, 8)


def svc(**kw):
    base = {"name": "X", "provider": "microsoft", "protocol": "oauth2-pkce", "scopes": ["Files.ReadWrite.AppFolder"],
            "guest": "everything works on this device", "signed_in": "sync across devices", "login": "primary",
            "revoke": "disconnect in settings", "status": "built"}
    base.update(kw)
    return base


def reg(**services):
    return {"primary_idp": "microsoft", "idps": {"microsoft": {}, "google": {}}, "services": services}


def problems(r, baseline=4, known=frozenset({"guiding-map"})):
    return ft.identity_problems(r, set(known), baseline, TODAY)


def test_a_complete_entry_is_one_line_of_onboarding():
    assert problems(reg(drive=svc())) == []


def test_every_field_is_required_so_guest_first_is_never_skipped():
    for field in ("guest", "signed_in", "revoke", "login", "protocol", "provider", "status", "name"):
        bad = svc()
        bad.pop(field)
        assert any(field in p for p in problems(reg(x=bad))), field


def test_the_primary_identity_must_be_a_declared_one():
    r = reg(x=svc())
    r["primary_idp"] = "somebody-else"
    assert any("primary_idp" in p for p in problems(r))


def test_unknown_protocol_login_and_status_are_refused():
    assert any("protocol" in p for p in problems(reg(x=svc(protocol="password"))))     # a password is never a protocol here
    assert any("login" in p for p in problems(reg(x=svc(login="maybe"))))
    assert any("status" in p for p in problems(reg(x=svc(status="done"))))


def test_over_broad_permissions_are_refused():
    for broad in ("*", "https://mail.google.com/", "https://www.googleapis.com/auth/drive", "Files.ReadWrite.All", "Mail.ReadWrite"):
        assert any("broader" in p for p in problems(reg(x=svc(scopes=[broad])))), broad
    # the narrow ones a real feature uses are fine
    assert problems(reg(x=svc(scopes=["https://www.googleapis.com/auth/drive.appdata", "openid", "email"]))) == []


def test_a_separate_login_needs_its_fix_and_a_future_date_or_a_real_standing_reason():
    sep = dict(login="separate")
    assert any("fix" in p for p in problems(reg(x=svc(**sep))))                                           # nothing said
    assert any("fix" in p for p in problems(reg(x=svc(fix="federate it", **sep))))                         # no date
    assert any("passed" in p for p in problems(reg(x=svc(fix="federate it", by="2026-01-01", **sep))))     # overdue: pulled back into view
    assert problems(reg(x=svc(fix="federate it", by="2026-12-15", **sep))) == []
    assert any("standing" in p for p in problems(reg(x=svc(standing="no", **sep))))                        # a word is not a reason
    assert problems(reg(x=svc(standing="A personal account has its own sign-in and no company single sign-on.", **sep))) == []


def test_the_count_of_separate_logins_only_goes_down():
    ok = dict(login="separate", fix="federate it", by="2026-12-15")
    two = reg(a=svc(**ok), b=svc(**ok))
    assert problems(two, baseline=2) == []
    assert any("baseline" in p for p in problems(two, baseline=1)), "a new separate login must be a deliberate, reviewed raise"


def test_a_feature_reference_must_be_real():
    assert any("not a feature" in p for p in problems(reg(x=svc(feature="no-such-thing"))))
    assert problems(reg(x=svc(feature="guiding-map"))) == []


def test_the_real_registry_passes_and_its_friction_register_is_honest():
    r = json.loads((ROOT / "governance" / "identity.json").read_text("utf-8"))
    baseline = json.loads((ROOT / "lifecycle" / "fitness.json").read_text("utf-8"))["budgets"]["separate_logins_baseline"]
    assert ft.check_signin_declared(baseline)["ok"]
    separate = {k for k, s in r["services"].items() if s["login"] == "separate"}
    assert {"aws", "gcp", "github", "ai-provider-keys"} <= separate, "the logins that are not through the one door must be listed, not hidden"
    assert len(separate) == baseline, "lower the baseline when one is removed, so the ratchet locks"
    # every service says what works with no sign-in: guest first
    assert all(s["guest"].strip() for s in r["services"].values())


def test_the_registry_never_holds_a_secret_a_token_or_a_person():
    text = (ROOT / "governance" / "identity.json").read_text("utf-8")
    assert not re.search(r"(sk-[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{12,}|ghp_[A-Za-z0-9]{20,}|eyJ[A-Za-z0-9_-]{20,}|@[a-z0-9-]+\.(com|org|in)\b)", text)


def test_the_principle_is_core_and_in_the_builders_guide():
    princ = {p["id"]: p for p in json.loads((ROOT / "governance" / "principles.json").read_text("utf-8"))["principles"]}
    p = princ["one-door"]
    assert p["core"] is True and "guest" in p["text"].lower() and "governance/identity.json" in p["text"]
    agents = (ROOT / "AGENTS.md").read_text("utf-8")
    assert "one-door" in agents and "signin-declared" in agents
