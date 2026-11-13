"""Threat watch: news ranks the curated patterns; it never writes a drill. No network: every source is a fake getter."""
import importlib.util
import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("securax_threatwatch", ROOT / "intel" / "threatwatch.py")
tw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tw)
LIB = tw.load(tw.PATTERNS)
FEEDS = tw.load(tw.FEEDS)


def rss(*items):
    body = "".join(f"<item><title>{t}</title><link>{link}</link><pubDate>{d}</pubDate></item>" for t, link, d in items)
    return f'<?xml version="1.0"?><rss><channel>{body}</channel></rss>'.encode()


def test_the_library_is_complete_and_every_drill_is_a_test_case():
    ids = [p["id"] for p in LIB["patterns"]]
    assert len(ids) == len(set(ids)) and len(ids) >= 10
    for p in LIB["patterns"]:
        assert p["where"] in ("global", "IN") and p["severity"] in (1, 2, 3), p["id"]
        assert p["story"] and len(p["signs"]) >= 2 and p["query"] and p["added"], p["id"]
        assert p["drills"] and all(d["try"].strip() and d["pass"].strip() for d in p["drills"]), p["id"]
        re.compile(p["match"])
    assert "honeytrap" in ids and "digital-arrest" in ids and "voice-clone" in ids


@pytest.mark.parametrize("title,pid", [
    ("What's a Honey Trap? The spy tactic that helped topple a tech CEO", "honeytrap"),
    ("Pune man loses lakhs in digital arrest scam", "digital-arrest"),
    ("Three charged in AI deepfake CEO fraud case", "voice-clone"),
    ("SIM swap gang arrested", "sim-swap"),
])
def test_headlines_land_on_the_right_pattern(title, pid):
    hits = tw.match([{"title": title, "link": "https://news.google.com/x", "published": "2026-11-12"}], {"region": "IN"},
                    tw.compile_patterns(LIB))
    assert pid in {h["pattern"] for h in hits}


def test_cyber_espionage_and_extortion_gangs_are_not_read_as_personal_honeytraps_or_kidnaps():
    hits = tw.match([{"title": "State hackers in cyber espionage campaign", "link": "", "published": ""},
                     {"title": "Cyber extortion group claims breach of a travel site", "link": "", "published": ""}],
                    {}, tw.compile_patterns(LIB))
    assert not {"honeytrap", "kidnap-extortion"} & {h["pattern"] for h in hits}


def test_a_country_pattern_is_searched_only_in_its_own_region():
    srcs = tw.sources(FEEDS, LIB)
    regions = {s["region"] for s in srcs if s.get("pattern") == "digital-arrest"}
    assert regions == {"IN"}
    assert {s["region"] for s in srcs if s.get("pattern") == "honeytrap"} == {"IN", "global"}
    assert all(s["url"].startswith("https://") for s in srcs)


def test_fetch_ranks_by_heat_and_severity_and_a_dead_source_never_stops_the_rest():
    def getter(url):
        if "honey" in url and "gl=IN" in url:
            return rss(("Spy agencies warn of honey trap revival - Some Paper", "https://news.google.com/a", "Wed, 11 Nov 2026 10:00:00 GMT"),
                       ("Honeytrap case: officer arrested - Other Paper", "https://news.google.com/b", "Thu, 12 Nov 2026 10:00:00 GMT"))
        if "TheHackersNews" in url:
            raise OSError("down")
        return rss()
    found, failed = tw.fetch(FEEDS, LIB, getter=getter)
    assert len(failed) == 1 and "thehackernews" in failed[0]
    state = {"items": []}
    assert tw.merge(state, found, "2026-11-13") == 2
    assert tw.merge(state, found, "2026-11-13") == 0, "the same headline is kept once"
    pk = tw.pack(LIB, state, "2026-11-13")
    top = pk["patterns"][0]
    assert top["id"] == "honeytrap" and top["heat"] == 2
    assert top["news"][0]["outlet"] == "Other Paper" and top["news"][0]["title"] == "Honeytrap case: officer arrested"
    assert top["drills"] == next(p for p in LIB["patterns"] if p["id"] == "honeytrap")["drills"]


def test_news_can_never_change_a_drill_and_bad_links_and_dtds_are_refused():
    evil = "<script>alert(1)</script> honey trap"
    found = tw.match([{"title": evil, "link": "", "published": ""}], {}, tw.compile_patterns(LIB))
    state = {"items": []}
    tw.merge(state, found, "2026-11-13")
    pk = tw.pack(LIB, state, "2026-11-13")
    lib_drills = {p["id"]: p["drills"] for p in LIB["patterns"]}
    assert all(p["drills"] == lib_drills[p["id"]] for p in pk["patterns"])
    assert set(pk["patterns"][0]) == {"id", "name", "where", "severity", "story", "signs", "drills", "heat", "news"}
    src = {"link_hosts": ["news.google.com"]}
    items = tw.RW.parse_feed(rss(("honey trap", "https://evil.example/x", "")), src)
    assert items[0]["link"] == "", "a link off the source's hosts is dropped"
    with pytest.raises(ValueError, match="DTD or entities"):
        tw.RW.parse_feed(b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><rss/>', src)


def test_the_state_is_bounded_in_age_and_size():
    state = {"items": [{"pattern": "honeytrap", "title": f"t{i}", "link": f"https://news.google.com/{i}", "date": "2026-01-01", "seen": "2026-01-01"} for i in range(5)]}
    tw.merge(state, [], "2026-11-13")
    assert state["items"] == [], "older than KEEP_DAYS is dropped"
    many = [{"pattern": "honeytrap", "title": f"t{i}", "link": f"https://news.google.com/{i}", "date": "2026-11-12", "region": "IN", "outlet": ""} for i in range(tw.MAX_ITEMS + 50)]
    tw.merge(state, many, "2026-11-13")
    assert len(state["items"]) == tw.MAX_ITEMS


def test_the_bundled_pack_carries_every_drill_offline(tmp_path):
    out = tmp_path / "intel.json"
    assert tw.main(["pack", "--out", str(out), "--state", str(tmp_path / "none.json")]) == 0
    pk = json.loads(out.read_text())
    assert len(pk["patterns"]) == len(LIB["patterns"]) and pk["generated"]
