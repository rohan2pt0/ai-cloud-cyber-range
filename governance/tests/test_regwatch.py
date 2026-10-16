import importlib.util
import pathlib

import pytest

_p = pathlib.Path(__file__).resolve().parent.parent / "regwatch.py"
_s = importlib.util.spec_from_file_location("regwatch", _p)
rw = importlib.util.module_from_spec(_s)
_s.loader.exec_module(rw)

RBI = b"""\xef\xbb\xbf<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>RBI</title>
<item><title><![CDATA[Master Direction on IT Governance]]></title><link>https://www.rbi.org.in/scripts/N.aspx?Id=1</link><pubDate>Mon, 12 Oct 2026 23:55:00</pubDate></item>
<item><title><![CDATA[Money Market Operations as on October 15, 2026]]></title><link>https://www.rbi.org.in/scripts/N.aspx?Id=2</link><pubDate>Thu, 15 Oct 2026 10:00:00</pubDate></item>
<item><title>Phish\xe2\x80\x8b &lt;b&gt;here&lt;/b&gt;</title><link>https://rbi.org.in.evil.example/x</link><pubDate>Thu, 15 Oct 2026 10:00:00</pubDate></item>
</channel></rss>"""
SEBI = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Cybersecurity framework update</title><link>https://www.sebi.gov.in/legal/circulars/oct-2026/x</link><pubDate>16 Oct, 2026 +0530</pubDate></item>
<item><title>Recovery proceeding</title><link>https://www.sebi.gov.in/enforcement/recovery-proceedings/y</link><pubDate>16 Oct, 2026 +0530</pubDate></item>
</channel></rss>"""
FEEDS = {"feeds": [
    {"id": "rbi", "regulator": "RBI", "title": "t", "url": "https://rbi", "link_hosts": ["rbi.org.in"], "exclude_title": "money market operations"},
    {"id": "sebi", "regulator": "SEBI", "title": "t", "url": "https://sebi", "link_hosts": ["sebi.gov.in"], "include_link": "/legal/|/press-releases/"}],
    "manual": [{"regulator": "CERT-In", "title": "CERT-In advisories", "url": "https://www.cert-in.org.in/"}]}


def test_filters_dates_and_foreign_links():
    its = rw.parse_feed(RBI, FEEDS["feeds"][0])
    assert [i["title"] for i in its] == ["Master Direction on IT Governance", "Phish here"]
    assert its[0]["published"] == "2026-10-12" and its[0]["link"].startswith("https://www.rbi.org.in/")
    assert its[1]["link"] == ""                       # a look-alike host is dropped, never linked
    s = rw.parse_feed(SEBI, FEEDS["feeds"][1])
    assert [i["title"] for i in s] == ["Cybersecurity framework update"] and s[0]["published"] == "2026-10-16"


def test_entity_declarations_are_refused():
    with pytest.raises(ValueError):
        rw.parse_feed(b'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY a "aaaa">]><rss><channel></channel></rss>', FEEDS["feeds"][0])


def test_first_fetch_is_a_silent_baseline_then_only_new_items_alert():
    state, data = {}, {"https://rbi": RBI, "https://sebi": SEBI}
    new, err = rw.fetch_all(FEEDS, state, getter=data.__getitem__, today="2026-10-16")
    assert new == [] and err == [] and len(state["items"]) == 3
    data["https://sebi"] = SEBI.replace(b"</channel>", b"<item><title>New master circular</title><link>https://www.sebi.gov.in/legal/master-circulars/z</link><pubDate>17 Oct, 2026 +0530</pubDate></item></channel>")
    new, _ = rw.fetch_all(FEEDS, state, getter=data.__getitem__, today="2026-10-17")
    assert [i["title"] for i in new] == ["New master circular"]
    new, _ = rw.fetch_all(FEEDS, state, getter=data.__getitem__, today="2026-10-18")
    assert new == []                                  # de-duplicated


def test_a_broken_feed_does_not_hide_the_others():
    def getter(url):
        if url == "https://rbi":
            raise OSError("down")
        return SEBI
    state = {}
    _, err = rw.fetch_all(FEEDS, state, getter=getter, today="2026-10-16")
    assert len(err) == 1 and err[0].startswith("rbi:") and len(state["items"]) == 1


def test_digest_lists_titles_and_links_only_and_the_manual_checks():
    state = {}
    rw.fetch_all(FEEDS, state, getter={"https://rbi": RBI, "https://sebi": SEBI}.__getitem__, today="2026-10-16")
    md = rw.digest(state, FEEDS, "2026-10")
    assert "# Regulator watch: October 2026" in md
    assert "[Master Direction on IT Governance](https://www.rbi.org.in/scripts/N.aspx?Id=1)" in md
    assert "## SEBI (1)" in md and "CERT-In advisories" in md and "read the source" in md
    assert "## RBI (0)" in rw.digest(state, FEEDS, "2026-09")


def test_alert_text_caps_at_ten():
    new = [{"regulator": "RBI", "title": f"t{i}", "link": ""} for i in range(13)]
    assert "and 3 more" in rw.alert_text(new)


def test_shipped_sources_are_https_and_parse():
    src = rw.load_sources()
    assert all(f["url"].startswith("https://") and f["link_hosts"] for f in src["feeds"])
