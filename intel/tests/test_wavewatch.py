"""Wave watch: a weekly read of reputable-forum news titles and links; news ranks a wave, it never writes a step. No network."""
import importlib.util
import json
import pathlib
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("securax_wavewatch", ROOT / "intel" / "wavewatch.py")
ww = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ww)
WAVES = ww.load(ww.WAVE_PATTERNS)

SITES = ("weforum.org", "imf.org", "rbi.org.in", "worldbank.org", "oecd.org", "cert-in.org.in")
WAVE_IDS = {"slowdown", "prices-rates", "trade-shocks", "health-weather", "scams", "ai-work"}


def rss(*items):
    body = "".join(f"<item><title>{t}</title><link>{link}</link><pubDate>{d}</pubDate></item>" for t, link, d in items)
    return f'<?xml version="1.0"?><rss><channel>{body}</channel></rss>'.encode()


def test_sources_make_one_search_per_wave_filtered_to_the_six_forums():
    srcs = ww.sources(WAVES, WAVES)
    searched = [s for s in srcs if s.get("pattern")]
    assert {s["pattern"] for s in searched} == WAVE_IDS
    assert len(searched) == len(WAVE_IDS), "one search per wave, nothing else"
    assert len({s["url"] for s in searched}) == len(WAVE_IDS), "each wave has its own news search"
    terms = {"slowdown": ("recession", "contraction"), "prices-rates": ("inflation", "cost of living"),
             "trade-shocks": ("tariff", "export ban"), "health-weather": ("outbreak", "air quality"),
             "scams": ("scam", "ponzi"), "ai-work": ("artificial intelligence", "chatbot")}
    for s in searched:
        q = urllib.parse.unquote_plus(s["url"]).lower()
        for term in terms[s["pattern"]]:
            assert term in q, "the search covers this wave's subjects, not only its site filters"
        for site in SITES:
            assert f"site:{site}" in q, s["pattern"]


def test_a_title_naming_inflation_lands_on_prices_rates():
    hits = ww.match([{"title": "Inflation climbs to 6% as food prices bite", "link": "https://news.google.com/x",
                      "published": "2026-11-12"}], {"region": "global"}, ww.compile_patterns(WAVES))
    assert "prices-rates" in {h["pattern"] for h in hits}


def test_a_link_off_news_google_com_is_dropped():
    def getter(url):
        return rss(("Inflation seen rising again next quarter", "https://example.com/off", "Fri, 13 Nov 2026 10:00:00 GMT"))

    found, failed = ww.fetch(WAVES, WAVES, getter=getter)
    assert not failed
    off = [f for f in found if f["title"] == "Inflation seen rising again next quarter"]
    assert off and all(f["link"] == "" for f in off), "a link off the source's hosts is dropped, never kept"


def test_pack_keeps_each_wave_with_heat_and_at_most_five_titles():
    today = ww.dt.date.today()
    recent = (today - ww.dt.timedelta(days=1)).isoformat()
    stale = (today - ww.dt.timedelta(days=31)).isoformat()
    future = (today + ww.dt.timedelta(days=1)).isoformat()
    items = [{"pattern": "prices-rates", "title": f"Inflation headline {i}", "link": f"https://news.google.com/{i}",
              "date": recent, "region": "global", "outlet": ""} for i in range(7)]
    items.append({"pattern": "slowdown", "title": "Growth slows to a crawl", "link": "https://news.google.com/s",
                  "date": recent, "region": "global", "outlet": ""})
    items.append({"pattern": "prices-rates", "title": "Old inflation headline", "link": "https://news.google.com/old",
                  "date": stale, "region": "global", "outlet": ""})
    items.append({"pattern": "prices-rates", "title": "Future inflation headline", "link": "https://news.google.com/future",
                  "date": future, "region": "global", "outlet": ""})
    pk = ww.pack(WAVES, {"items": items}, today.isoformat())
    assert set(pk) == {"waves"}
    assert len(pk["waves"]) == len(WAVE_IDS)
    assert {w["id"] for w in pk["waves"]} == WAVE_IDS
    assert all(set(w) == {"id", "heat", "items"} for w in pk["waves"])
    by = {w["id"]: w for w in pk["waves"]}
    assert by["prices-rates"]["heat"] == 7, "heat counts only the last 30 days"
    assert len(by["prices-rates"]["items"]) == 5, "titles are capped at five per wave"
    assert "Old inflation headline" not in by["prices-rates"]["items"]
    assert by["slowdown"]["heat"] == 1 and by["slowdown"]["items"] == ["Growth slows to a crawl"]
    assert all(isinstance(i, str) for w in pk["waves"] for i in w["items"]), "items are titles only"


def test_main_sources_names_every_wave(capsys):
    assert ww.main(["sources"]) == 0
    out = capsys.readouterr().out
    assert "waves in intel/wave-patterns.json" in out
    for wid in WAVE_IDS:
        assert wid in out
    assert "search-" not in out, "a wave is named, not its internal search id"


def test_main_list_reports_even_with_nothing_fetched(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ww, "STATE", tmp_path / "wavewatch.json")
    monkeypatch.setattr(ww, "fetch", lambda feeds, lib, getter=None: ([], []))
    assert ww.main(["list"]) == 0
    assert "ranked by how often" in capsys.readouterr().out


def test_main_list_reports_a_failed_initial_fetch(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ww, "STATE", tmp_path / "wavewatch.json")
    monkeypatch.setattr(ww, "fetch", lambda feeds, lib, getter=None: ([], ["search: down"]))
    assert ww.main(["list"]) == 1
    assert "ranked by how often" in capsys.readouterr().out


def test_main_fetch_keeps_new_titles_and_reports_a_failed_source(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ww, "STATE", tmp_path / "wavewatch.json")
    found = [{"pattern": "prices-rates", "title": "Inflation eases", "link": "https://news.google.com/x",
              "date": ww.dt.date.today().isoformat(), "region": "global", "outlet": ""}]
    monkeypatch.setattr(ww, "fetch", lambda feeds, lib, getter=None: (found, ["x: down"]))
    assert ww.main(["fetch"]) == 1, "a failed source still reports the count and exits 1"
    state = json.loads((tmp_path / "wavewatch.json").read_text())
    assert len(state["items"]) == 1
    assert "1 new title(s) matched" in capsys.readouterr().out
