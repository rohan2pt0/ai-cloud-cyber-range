#!/usr/bin/env python3
"""OFFLINE — keep threat-intel snapshots on disk so the estate stays sharp with no network.

    ./securax offline sync [kev|attack]     refresh while you are online (a failed refresh never destroys a good snapshot)
    ./securax offline status                age + size of each snapshot (works fully offline)
    ./securax kev CVE-2024-3400 ...         is this CVE known-exploited? (offline, from the snapshot)
    ./securax offline sync epss             FIRST's EPSS: the chance each CVE is exploited in the next 30 days (the findings
                                            register uses it to raise what is likely to be attacked soon)

Low-resource by design: downloads are size-capped and streamed to disk; the 55 MB MITRE bundle is parsed object-by-object (flat
memory) and only a slim technique map is kept. Standard library only. Consumers: ai-soc/soc/enrich.py.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ai-soc"))
from soc import enrich  # noqa: E402


def cfg() -> dict:
    return json.loads((HERE / "offline.json").read_text("utf-8"))


def say(m: str = "") -> None:
    print(m, flush=True)


def download(urls: list[str], max_bytes: int, dest: pathlib.Path, timeout: int = 90) -> tuple[str, int, str]:
    """Stream the first URL that works into `dest`. Returns (url, bytes, sha256). Raises OSError with the reasons if all fail."""
    errors = []
    for url in urls:
        h, n = hashlib.sha256(), 0
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "securax-offline/1"}), timeout=timeout) as r, open(dest, "wb") as f:
                while True:
                    chunk = r.read(1 << 16)
                    if not chunk:
                        break
                    n += len(chunk)
                    if n > max_bytes:
                        raise OSError(f"larger than the {max_bytes // 1_000_000} MB cap")
                    h.update(chunk)
                    f.write(chunk)
            return url, n, h.hexdigest()
        except (OSError, ValueError) as e:
            errors.append(f"{url}: {e}")
    raise OSError("; ".join(errors))


def iter_json_array_objects(path: pathlib.Path, key: str = "objects", chunk_size: int = 1 << 20):
    """Yield each element of the top-level `key` array one at a time (flat memory), without a streaming-JSON dependency."""
    dec = json.JSONDecoder()
    with open(path, encoding="utf-8") as f:
        buf, pos, started = "", 0, False
        marker = f'"{key}"'
        while True:
            chunk = f.read(chunk_size)
            buf += chunk
            if not started:
                i = buf.find(marker)
                if i < 0:
                    if not chunk:
                        return
                    buf = buf[-len(marker):]
                    continue
                j = buf.find("[", i)
                if j < 0:
                    continue
                buf, pos, started = buf[j + 1:], 0, True
            while True:
                while pos < len(buf) and buf[pos] in " \r\n\t,":
                    pos += 1
                if pos >= len(buf):
                    break
                if buf[pos] == "]":
                    return
                try:
                    obj, end = dec.raw_decode(buf, pos)
                except ValueError:
                    break                                               # object continues in the next chunk
                yield obj
                pos = end
            buf, pos = buf[pos:], 0
            if not chunk:
                return


def slim_kev(raw: pathlib.Path) -> dict:
    d = json.loads(raw.read_text("utf-8"))
    vs = d["vulnerabilities"]                                           # KeyError = not the file we expected: refuse it
    by = {v["cveID"].upper(): {"vendor": v.get("vendorProject", ""), "product": v.get("product", ""), "name": v.get("vulnerabilityName", ""),
                               "added": v.get("dateAdded", ""), "due": v.get("dueDate", ""), "ransomware": v.get("knownRansomwareCampaignUse", "")} for v in vs}
    return {"catalog_version": d.get("catalogVersion"), "count": len(by), "by_cve": by}


def slim_attack(raw: pathlib.Path) -> dict:
    techs, version = {}, None
    for o in iter_json_array_objects(raw):
        t = o.get("type")
        if t == "x-mitre-collection":
            version = o.get("x_mitre_version")
        if t != "attack-pattern" or o.get("revoked") or o.get("x_mitre_deprecated"):
            continue
        tid = next((r["external_id"] for r in o.get("external_references", []) if r.get("source_name") == "mitre-attack" and r.get("external_id")), None)
        if tid:
            techs[tid] = {"name": o.get("name", ""), "tactics": [p["phase_name"] for p in o.get("kill_chain_phases", []) if p.get("kill_chain_name") == "mitre-attack"]}
    if not techs:
        raise ValueError("no ATT&CK techniques found: not the file we expected")
    return {"attack_version": version, "count": len(techs), "techniques": techs}


EPSS_KEEP = 0.10      # CVEs under a 10% chance are left out (about 17,000 of ~300,000 stay, ~0.4 MB): absent means "unlikely"


def slim_epss(raw: pathlib.Path) -> dict:
    """The daily EPSS file (gzipped CSV: a '#model_version:...,score_date:...' line, then cve,epss,percentile)."""
    by, meta, rows = {}, "", 0
    with gzip.open(raw, "rt", encoding="utf-8") as fh:
        for row in csv.reader(fh):
            if not row:
                continue
            if row[0].startswith("#"):
                meta = ",".join(row).lstrip("#")
                continue
            if row[0] == "cve":
                continue
            rows += 1
            score = float(row[1])
            if score >= EPSS_KEEP:
                by[row[0].upper()] = round(score, 4)
    if rows < 1000:
        raise ValueError("too few EPSS rows: not the file we expected")
    info = dict(kv.split(":", 1) for kv in meta.split(",") if ":" in kv)
    return {"model_version": info.get("model_version"), "score_date": info.get("score_date", "")[:10], "rows": rows,
            "kept_from": EPSS_KEEP, "count": len(by), "by_cve": by}


SLIMMERS = {"kev": slim_kev, "attack": slim_attack, "epss": slim_epss}


def sync_one(name: str, spec: dict, out_dir: pathlib.Path) -> tuple[bool, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out_dir) as td:
        raw = pathlib.Path(td) / "raw.json"
        try:
            url, n, digest = download(spec["urls"], spec["max_bytes"], raw)
            slim = SLIMMERS[name](raw)
        except (OSError, ValueError, KeyError) as e:
            return False, f"{name}: refresh FAILED ({str(e)[:160]}) — keeping the existing snapshot"
        slim.update({"fetched_at": time.time(), "source": url, "licence": spec["licence"], "raw_sha256": digest, "raw_bytes": n})
        tmp = out_dir / f".{name}.json.tmp"
        tmp.write_text(json.dumps(slim, separators=(",", ":")), encoding="utf-8")
        os.replace(tmp, out_dir / f"{name}.json")                      # atomic: a crash never leaves a half snapshot
    return True, f"{name}: {slim['count']} entries from {url.split('/')[2]} ({n // 1000} KB downloaded, {(out_dir / f'{name}.json').stat().st_size // 1000} KB kept)"


def cmd_sync(a: argparse.Namespace) -> int:
    c = cfg()
    out_dir = enrich.intel_dir()
    names = [a.source] if a.source else list(c["sources"])
    bad = 0
    for n in names:
        if n not in c["sources"]:
            say(f"unknown source '{n}'. Sources: {', '.join(c['sources'])}")
            return 2
        ok, msg = sync_one(n, c["sources"][n], out_dir)
        say(("  ✔ " if ok else "  ✘ ") + msg)
        bad += 0 if ok else 1
    return 1 if bad else 0


def cmd_status(_: argparse.Namespace) -> int:
    c = cfg()
    say(f"threat-intel snapshots in {enrich.intel_dir()} (all of this works with no network):")
    for name, spec in c["sources"].items():
        snap = enrich._load(name)
        if not snap:
            say(f"  ○ {name:<7} none yet  — {spec['what']}\n            get it once:  ./securax offline sync {name}")
            continue
        age = enrich.age_days(snap) or 0
        stale = age > spec["stale_days"]
        say(f"  {'◐' if stale else '●'} {name:<7} {snap['count']} entries, {age:.0f} day(s) old{'  (STALE: refresh when online)' if stale else ''}  — {spec['what']}")
    return 0


def cmd_kev(a: argparse.Namespace) -> int:
    rep = enrich.kev_report(" ".join(a.cves))
    say(enrich.render_kev(rep))
    return 1 if rep["exploited"] else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sync", help="refresh snapshots (needs internet once)")
    s.add_argument("source", nargs="?", default="")
    s.set_defaults(fn=cmd_sync)
    sub.add_parser("status", help="age/size of each snapshot (offline)").set_defaults(fn=cmd_status)
    k = sub.add_parser("kev", help="are these CVEs known-exploited? (offline)")
    k.add_argument("cves", nargs="+")
    k.set_defaults(fn=cmd_kev)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
