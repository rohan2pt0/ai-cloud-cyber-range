"""Offline tests for the AI-history importer. Fixtures are synthetic, shaped like each vendor's export."""
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("kimp", Path(__file__).resolve().parents[1] / "importer.py")
K = importlib.util.module_from_spec(_spec)
sys.modules["kimp"] = K
_spec.loader.exec_module(K)

CLAUDE = [{
    "uuid": "c-1", "name": "Zero trust plan", "created_at": "2025-03-01T10:00:00Z", "updated_at": "2025-03-02T10:00:00Z",
    "chat_messages": [
        {"sender": "human", "text": "Draft a zero trust plan", "content": [{"type": "text", "text": "Draft a zero trust plan"}]},
        {"sender": "assistant", "text": "", "content": [{"type": "text", "text": "Phase 1: identity."},
                                                        {"type": "tool_use", "name": "x"}]},
    ]},
    {"uuid": "c-empty", "name": "", "created_at": "2025-03-03T10:00:00Z", "chat_messages": []},
]
CLAUDE_PROJECTS = [{"uuid": "p-1", "name": "CISO playbook", "description": "board pack", "prompt_template": "Be direct.",
                    "created_at": "2025-01-01T00:00:00Z", "docs": [{"filename": "kpi.md", "content": "MTTD < 1h"}]}]
CHATGPT = [{
    "title": "SOC metrics", "create_time": 1735689600.0, "update_time": 1735690000.0, "conversation_id": "g-1",
    "current_node": "n4",
    "mapping": {
        "n0": {"id": "n0", "message": None, "parent": None, "children": ["n1"]},
        "n1": {"id": "n1", "parent": "n0", "children": ["n2", "n2b"],
               "message": {"author": {"role": "system"}, "content": {"content_type": "text", "parts": ["sys"]}}},
        "n2": {"id": "n2", "parent": "n1", "children": ["n3"],
               "message": {"author": {"role": "user"}, "content": {"content_type": "text", "parts": ["Which SOC KPIs?"]}}},
        "n2b": {"id": "n2b", "parent": "n1", "children": [],
                "message": {"author": {"role": "user"}, "content": {"content_type": "text", "parts": ["ABANDONED BRANCH"]}}},
        "n3": {"id": "n3", "parent": "n2", "children": ["n4"],
               "message": {"author": {"role": "assistant"}, "content": {"content_type": "thoughts", "thoughts": []}}},
        "n4": {"id": "n4", "parent": "n3", "children": [],
               "message": {"author": {"role": "assistant"}, "content": {"content_type": "text", "parts": ["MTTD and MTTR."]}}},
    }}]
DEEPSEEK = [{
    "id": "d-1", "title": "RBI circular", "inserted_at": "2025-02-01T08:00:00+08:00", "updated_at": "2025-02-01T09:00:00+08:00",
    "mapping": {
        "root": {"id": "root", "parent": None, "children": ["1"], "message": None},
        "1": {"id": "1", "parent": "root", "children": ["2"],
              "message": {"fragments": [{"type": "REQUEST", "content": "Summarise the RBI circular"}]}},
        "2": {"id": "2", "parent": "1", "children": [],
              "message": {"fragments": [{"type": "THINK", "content": "hidden reasoning"},
                                        {"type": "RESPONSE", "content": "It covers incident reporting."}]}},
    }}]
GEMINI = [
    {"header": "Gemini Apps", "title": "Prompted second question", "time": "2025-04-01T12:00:00.000Z",
     "safeHtmlItem": [{"html": "<p>Second <b>answer</b></p>"}]},
    {"header": "Gemini Apps", "title": "Prompted first question", "time": "2025-04-01T09:00:00.000Z",
     "safeHtmlItem": [{"html": "<p>First answer &amp; more</p>"}]},
    {"header": "Gemini Apps", "title": "Changed a setting", "time": "2025-04-01T08:00:00.000Z"},
]


def _zip(tmp: Path, name: str, members: dict) -> Path:
    z = tmp / name
    with zipfile.ZipFile(z, "w") as f:
        for n, data in members.items():
            f.writestr(n, json.dumps(data))
    return z


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    monkeypatch.setenv("SECURAX_KNOWLEDGE_DIR", str(v))
    return v


def test_detects_each_vendor():
    assert K.detect("conversations.json", CLAUDE) == "claude"
    assert K.detect("projects.json", CLAUDE_PROJECTS) == "claude-projects"
    assert K.detect("conversations.json", CHATGPT) == "chatgpt"
    assert K.detect("conversations.json", DEEPSEEK) == "deepseek"
    assert K.detect("Takeout/My Activity/Gemini Apps/MyActivity.json", GEMINI) == "gemini"
    assert K.detect("users.json", [{"uuid": "x", "email": "a@b"}]) is None
    assert K.detect("x.json", {}) is None


def test_chatgpt_follows_the_visible_branch_and_skips_system_and_thoughts():
    [c] = K.parse_chatgpt(CHATGPT)
    assert c.turns == [("user", "Which SOC KPIs?"), ("assistant", "MTTD and MTTR.")]


def test_deepseek_drops_reasoning_fragments():
    [c] = K.parse_deepseek(DEEPSEEK)
    assert c.turns == [("user", "Summarise the RBI circular"), ("assistant", "It covers incident reporting.")]


def test_gemini_groups_by_day_oldest_first_and_strips_html():
    [c] = K.parse_gemini(GEMINI)
    assert [t[1] for t in c.turns] == ["first question", "First answer & more", "second question", "Second answer"]
    assert c.created.hour == 9


def test_claude_projects_keep_instructions_and_knowledge():
    [p] = K.parse_claude_projects(CLAUDE_PROJECTS)
    text = "\n".join(t for _, t in p.turns)
    assert "Be direct." in text and "MTTD < 1h" in text and p.kind == "project"


def test_full_import_is_idempotent_and_writes_index(tmp_path, vault):
    z = _zip(tmp_path, "claude.zip", {"conversations.json": CLAUDE, "projects.json": CLAUDE_PROJECTS, "users.json": [{"uuid": "u"}]})
    s = K.import_paths([z], vault)
    assert (s["new"], s["empty"]) == (2, 1)
    files = sorted((vault / "out" / "claude").glob("*.md"))
    assert len(files) == 2 and files[0].name.startswith("2025-01-01-project-ciso-playbook-")
    md = next(f for f in files if "zero-trust" in f.name).read_text()
    assert "**You:**\nDraft a zero trust plan" in md and "**Claude:**\nPhase 1: identity." in md
    assert "Zero trust plan" in (vault / "out" / "INDEX.md").read_text()
    again = K.import_paths([z], vault)
    assert (again["new"], again["updated"], again["unchanged"]) == (0, 0, 2)


def test_secrets_and_critical_ids_are_redacted_but_email_kept(tmp_path, vault):
    leak = [{**CLAUDE[0], "uuid": "c-leak", "chat_messages": [
        {"sender": "human", "content": [{"type": "text", "text":
            "key sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123 card 4111 1111 1111 1111 pan ABCPE1234F "
            "password: hunter2secret mail me@example.com"}]}]}]
    s = K.import_paths([_zip(tmp_path, "c.zip", {"conversations.json": leak})], vault)
    md = next((vault / "out" / "claude").glob("*.md")).read_text()
    for gone in ("sk-ant-api03", "4111 1111", "ABCPE1234F", "hunter2secret"):
        assert gone not in md
    assert "me@example.com" in md and s["redactions"] >= 4


def test_flag_terms_route_to_review_folder(tmp_path, vault):
    vault.mkdir(parents=True)
    (vault / "flag-terms.txt").write_text("# employer\nzero TRUST\n")
    s = K.import_paths([_zip(tmp_path, "c.zip", {"conversations.json": CLAUDE})], vault)
    assert s["flagged"] == 1
    assert list((vault / "flagged" / "claude").glob("*.md")) and not list((vault / "out" / "claude").glob("*zero*"))
    assert "⚑" in (vault / "out" / "INDEX.md").read_text()


def test_inbox_cli_and_unrecognised_file(tmp_path, vault, capsys):
    assert K.main(["import"]) == 0 and "Drop your export" in capsys.readouterr().out
    _zip(vault / "inbox", "chatgpt.zip", {"conversations.json": CHATGPT})
    (vault / "inbox" / "deepseek.json").write_text(json.dumps(DEEPSEEK))
    assert K.main(["import"]) == 0
    out = capsys.readouterr().out
    assert "2 new" in out
    assert K.main(["import", "--quiet"]) == 0 and capsys.readouterr().out == ""
    assert K.main(["status"]) == 0 and "ChatGPT" in capsys.readouterr().out
    junk = _zip(tmp_path, "junk.zip", {"other.json": {"a": 1}})
    assert K.main(["import", str(junk)]) == 1


def test_title_change_keeps_one_copy(tmp_path, vault):
    K.import_paths([_zip(tmp_path, "a.zip", {"conversations.json": CLAUDE})], vault)
    renamed = [{**CLAUDE[0], "name": "Zero trust roadmap"}]
    s = K.import_paths([_zip(tmp_path, "b.zip", {"conversations.json": renamed})], vault)
    assert s["updated"] == 1
    assert [f.name for f in (vault / "out" / "claude").glob("*.md")] == [
        next(f.name for f in (vault / "out" / "claude").glob("*roadmap*"))]
