"""evidence pack: useful to an auditor, and provably free of prompts and secrets."""
import importlib.util
import json
import pathlib
import tarfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
spec = importlib.util.spec_from_file_location("ev", HERE.parent / "evidence.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)

LOG = [
    'gateway-1 | {"req_id":"1","principal":"p","decision":"block","stage":"input","findings":[{"rule":"PI-001","detail":"SECRET-PROMPT-TEXT"}]}',
    'gateway-1 | {"req_id":"2","principal":"p","decision":"allow","model":"bank-assistant","latency_ms":5,"findings":[]}',
    'gateway-1 | {"req_id":"3","decision":"upstream_error","error":"boom api-key-leak-abc"}',
    "gateway-1 | not json at all",
]


def test_audit_summary_counts_but_drops_free_text():
    s = ev.summarize_audit(LOG)
    assert s["events"] == 3 and s["decisions"] == {"block": 1, "allow": 1, "upstream_error": 1}
    assert s["rules_triggered"] == {"PI-001": 1} and s["models_used"] == {"bank-assistant": 1}
    assert "SECRET-PROMPT-TEXT" not in json.dumps(s) and "api-key-leak-abc" not in json.dumps(s)


def test_pack_contains_no_keys_and_is_checksummed(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "gateway_log").write_text("\n".join(LOG))
    (raw / "readyz").write_text("ok READY")
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=sk-VERY-SECRET-VALUE-123\nGEMINI_API_KEY=AIza-ANOTHER-SECRET-456\nLLAMA_GUARD_URL=\n")
    data, report = ev.build(str(raw), str(env), root=str(REPO))
    out = tmp_path / "pack.tar.gz"
    ev.write_pack(str(out), data, report)
    with tarfile.open(out) as t:
        blob = b"".join(t.extractfile(m).read() for m in t.getmembers()).decode()
        names = {m.name for m in t.getmembers()}
    assert names == {"evidence.json", "evidence.md", "SHA256SUMS"}
    for secret in ("sk-VERY-SECRET-VALUE-123", "AIza-ANOTHER-SECRET-456", "SECRET-PROMPT-TEXT"):
        assert secret not in blob
    assert "openai" in data["ai_providers_enabled"] and data["detector_llama_guard"].startswith("OFF")


def test_files_that_hold_keys_or_user_data_are_git_ignored():
    gi = (REPO / ".gitignore").read_text()
    lines = {ln.strip() for ln in gi.splitlines()}
    for must in ("backups/", "evidence/", ".env", "watch.log"):
        assert must in lines, f"{must} must be git-ignored (backups contain API keys)"
