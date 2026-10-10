import importlib.util, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("en", ROOT/"assistant"/"enhance.py")
en=importlib.util.module_from_spec(spec); sys.modules["en"]=en; spec.loader.exec_module(en)

def test_intent_detection():
    assert en.detect_intent("summarise this report")=="summarise"
    assert en.detect_intent("should I pick A or B?")=="decide"
    assert en.detect_intent("draft an email to my boss")=="draft"
    assert en.detect_intent("what is zero trust?")=="explain"
    assert en.detect_intent("random musing")=="general"

def test_enhance_adds_contract_and_format():
    r=en.enhance("summarise this")
    sys_msg=r["messages"][0]["content"]
    assert "never invent" in sys_msg.lower() or "never guess" in sys_msg.lower()
    assert "not certain" in sys_msg.lower()           # anti-hallucination
    assert r["intent"]=="summarise" and len(r["followups"])>=3

def test_red_tier_adds_sensitivity_note():
    r=en.enhance("summarise customer Aadhaar 2345 6789 0123 details")
    assert r["data_tier"]=="Red"
    assert "never leave" in r["messages"][0]["content"].lower() or "sensitive" in r["messages"][0]["content"].lower()

def test_context_grounding():
    r=en.enhance("what does it say?", context="The repo rate is held at 6.5%.")
    assert "answer only from this" in r["messages"][1]["content"].lower()

def test_feedback(tmp_path, monkeypatch):
    monkeypatch.setattr(en,"FEEDBACK_LOG",tmp_path/"f.jsonl")
    en.record_feedback("q","a","up"); en.record_feedback("q2","a2","up")
    s=en.feedback_stats(); assert s["total"]==2 and s["up"]==2 and s["satisfaction"]==1.0
