"""Offline threat-intel snapshots: refresh is safe, parsing is memory-flat, enrichment works with no network at all."""
import importlib.util
import json
import pathlib
import time

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("offline", REPO / "lifecycle" / "offline.py")
off = importlib.util.module_from_spec(spec)
spec.loader.exec_module(off)
enrich = off.enrich


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HOME_DIR", str(tmp_path / "home"))
    return tmp_path


def stix(tmp_path):
    objs = [
        {"type": "x-mitre-collection", "x_mitre_version": "99.9"},
        {"type": "attack-pattern", "name": "Exploit Public-Facing Application", "kill_chain_phases": [{"kill_chain_name": "mitre-attack", "phase_name": "initial-access"}],
         "external_references": [{"source_name": "mitre-attack", "external_id": "T1190"}]},
        {"type": "attack-pattern", "name": 'Tricky } "name" ] , {', "kill_chain_phases": [{"kill_chain_name": "mitre-attack", "phase_name": "execution"}, {"kill_chain_name": "other", "phase_name": "x"}],
         "external_references": [{"source_name": "mitre-attack", "external_id": "T1059.001"}]},
        {"type": "attack-pattern", "name": "Old", "revoked": True, "external_references": [{"source_name": "mitre-attack", "external_id": "T0001"}]},
        {"type": "attack-pattern", "name": "Deprecated", "x_mitre_deprecated": True, "external_references": [{"source_name": "mitre-attack", "external_id": "T0002"}]},
        {"type": "malware", "name": "not a technique"},
    ]
    p = tmp_path / "enterprise.json"
    p.write_text(json.dumps({"type": "bundle", "id": "x", "objects": objs}, indent=2))
    return p


def kev(tmp_path):
    vs = [{"cveID": "CVE-2024-3400", "vendorProject": "Palo Alto", "product": "PAN-OS", "vulnerabilityName": "Command Injection", "dateAdded": "2024-04-12",
           "dueDate": "2024-04-19", "knownRansomwareCampaignUse": "Known"},
          {"cveID": "CVE-2023-0001", "vendorProject": "V", "product": "P", "vulnerabilityName": "N", "dateAdded": "2023-01-01", "dueDate": "2023-01-22", "knownRansomwareCampaignUse": "Unknown"}]
    p = tmp_path / "kev.json"
    p.write_text(json.dumps({"catalogVersion": "1", "vulnerabilities": vs}))
    return p


@pytest.mark.parametrize("chunk", [1, 7, 64, 1 << 20])
def test_streaming_parser_survives_any_chunk_boundary_and_hostile_strings(tmp_path, chunk):
    p = stix(tmp_path)
    names = [o.get("name") for o in off.iter_json_array_objects(p, chunk_size=chunk)]
    assert names.count('Tricky } "name" ] , {') == 1 and len(names) == 6


def test_attack_slimming_keeps_only_live_techniques_and_their_tactics(tmp_path):
    s = off.slim_attack(stix(tmp_path))
    assert set(s["techniques"]) == {"T1190", "T1059.001"} and s["attack_version"] == "99.9"
    assert s["techniques"]["T1059.001"]["tactics"] == ["execution"]          # the non-ATT&CK kill chain is ignored


def test_files_that_are_not_what_we_expected_are_refused(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"hello": "world"}')
    with pytest.raises(ValueError):
        off.slim_attack(bad)
    with pytest.raises(KeyError):
        off.slim_kev(bad)


def test_sync_writes_atomically_and_a_failed_refresh_keeps_the_good_snapshot(tmp_path):
    spec_ok = {"urls": [kev(tmp_path).as_uri()], "max_bytes": 10_000_000, "licence": "CC0"}
    out = enrich.intel_dir()
    ok, msg = off.sync_one("kev", spec_ok, out)
    assert ok and (out / "kev.json").exists() and not list(out.glob(".*tmp*")), msg
    before = (out / "kev.json").read_bytes()
    ok, msg = off.sync_one("kev", {**spec_ok, "urls": [(tmp_path / "missing.json").as_uri()]}, out)
    assert not ok and "keeping the existing snapshot" in msg and (out / "kev.json").read_bytes() == before
    ok, msg = off.sync_one("kev", {**spec_ok, "max_bytes": 10}, out)
    assert not ok and "cap" in msg and (out / "kev.json").read_bytes() == before


def test_a_dead_first_url_falls_back_to_the_mirror(tmp_path):
    spec_ok = {"urls": [(tmp_path / "nope.json").as_uri(), kev(tmp_path).as_uri()], "max_bytes": 10_000_000, "licence": "CC0"}
    assert off.sync_one("kev", spec_ok, enrich.intel_dir())[0]


def snapshots(tmp_path, age_days=0):
    for name, spec_, src in (("kev", "kev", kev(tmp_path)), ("attack", "attack", stix(tmp_path))):
        off.sync_one(name, {"urls": [src.as_uri()], "max_bytes": 10_000_000, "licence": "x"}, enrich.intel_dir())
    if age_days:
        for n in ("kev", "attack"):
            p = enrich.intel_dir() / f"{n}.json"
            d = json.loads(p.read_text())
            d["fetched_at"] = time.time() - age_days * 86400
            p.write_text(json.dumps(d))


def test_everything_works_with_no_snapshot_and_says_how_to_get_one():
    assert enrich.attack_techniques("T1190") == [{"id": "T1190", "name": None, "tactics": [], "url": "https://attack.mitre.org/techniques/T1190/"}]
    assert "offline sync" in enrich.render_kev(enrich.kev_report("CVE-2024-3400"))
    assert enrich.enrich_incident({"attack": "T1190"})["techniques"][0]["name"] is None


def test_techniques_are_named_from_the_snapshot_and_unknown_ids_survive(tmp_path):
    snapshots(tmp_path)
    t = enrich.attack_techniques("T1190 (exploit public app) / T1059.001 / T9999")
    assert [x["name"] for x in t] == ["Exploit Public-Facing Application", 'Tricky } "name" ] , {', None]
    assert t[1]["url"].endswith("/T1059/001/")


def test_kev_report_flags_exploited_cves_orders_by_due_date_and_notes_staleness(tmp_path):
    snapshots(tmp_path, age_days=30)
    rep = enrich.kev_report("found CVE-2023-0001 and cve-2024-3400 and CVE-2020-0000 in the scan")
    assert [e["cve"] for e in rep["exploited"]] == ["CVE-2023-0001", "CVE-2024-3400"] and rep["cves_seen"] == 3
    text = enrich.render_kev(rep)
    assert "[used in ransomware]" in text and "30 days old" in text
    assert "none of the 1" in enrich.render_kev(enrich.kev_report("CVE-2020-0000"))


def test_the_soc_names_techniques_in_its_incidents_offline(tmp_path):
    snapshots(tmp_path)
    from soc import triage as tri
    recs = [{"ts": i, "principal": "x", "decision": "block", "findings": [{"rule": "PI-001-override", "severity": "high", "category": "c"}]} for i in range(1, 5)]
    inc = tri.triage(recs, summarize=False)["incidents"][0]
    assert inc["rule"] == "repeated-prompt-injection" and inc["techniques"][0]["name"] == "Exploit Public-Facing Application"


def test_epss_keeps_only_the_cves_worth_ranking(tmp_path):
    import gzip
    rows = ["#model_version:v2025.03.14,score_date:2026-10-19T12:55:00Z", "cve,epss,percentile"]
    rows += [f"CVE-2026-{i:05d},0.00{i % 9},0.1" for i in range(1200)] + ["CVE-2024-3400,0.99999,1.0", "cve-2026-99999,0.5,0.97"]
    raw = tmp_path / "e.csv.gz"
    with gzip.open(raw, "wt") as fh:
        fh.write("\n".join(rows) + "\n")
    s = off.slim_epss(raw)
    assert s["score_date"] == "2026-10-19" and s["rows"] == 1202 and s["count"] == 2
    assert s["by_cve"]["CVE-2024-3400"] == [1.0, 1.0] and "CVE-2026-99999" in s["by_cve"]
    small = tmp_path / "s.csv.gz"
    with gzip.open(small, "wt") as fh:
        fh.write("cve,epss,percentile\nCVE-2024-3400,0.9,1\n")
    with pytest.raises(ValueError):
        off.slim_epss(small)
