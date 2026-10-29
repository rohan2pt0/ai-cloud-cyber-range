"""`./securax catchup` and saved prompts: the brief is built from the estate's own state, the 'act today' ground truth is
always shown, the AI summary is only an aid (skipped with no gateway, never hides a real item), and saved prompts fill
their variables. These keep the AI-UX honest and offline-first."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cu = _load("catchup", "governance/catchup.py")
pz = _load("personas_t", "agents/personas.py")


def test_structured_brief_shows_the_act_today_ground_truth():
    s = {"act": [{"area": "Findings", "title": "F-1 overdue since 2026-01-01", "fix": "./securax findings"}],
         "later": [], "nudges": [], "next": None, "rhythm": {"known": False}, "errors": []}
    out = cu.structured_brief(s)
    assert "Act today (1)" in out and "F-1 overdue" in out and "./securax findings" in out


def test_a_clear_red_list_says_so_plainly():
    s = {"act": [], "later": [], "nudges": [], "next": None, "rhythm": {"known": False}, "errors": []}
    assert "nothing overdue" in cu.structured_brief(s)


def test_ai_summary_is_skipped_without_a_gateway_and_never_replaces_the_facts(monkeypatch):
    monkeypatch.delenv("GATEWAY_URL", raising=False)
    s = {"act": [{"area": "Risks", "title": "R-2 treatment overdue", "fix": "./securax risks overdue"}],
         "later": [], "nudges": [], "next": None, "rhythm": {"known": False}, "errors": []}
    assert cu.ai_summary(s) is None
    rendered = cu.render(s)
    assert "R-2 treatment overdue" in rendered            # the ground truth is present whether or not a model spoke


def test_gather_is_offline_and_never_crashes():
    s = cu.gather(now=1_793_000_000.0)
    assert isinstance(s.get("act"), list) and isinstance(s.get("later"), list) and isinstance(s.get("errors"), list)


def test_saved_prompt_fills_its_variables_and_appends_extra():
    body = pz.render_prompt("standup", "ship the ZTMM PR")
    import datetime
    assert datetime.date.today().isoformat() in body and "ship the ZTMM PR" in body and "{date}" not in body


def test_unknown_saved_prompt_is_rejected_clearly():
    try:
        pz.render_prompt("does-not-exist")
        raise AssertionError("expected KeyError")
    except KeyError as e:
        assert "unknown prompt" in str(e)
