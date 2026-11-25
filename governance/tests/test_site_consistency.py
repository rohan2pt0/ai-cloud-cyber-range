"""Every storefront page follows the home page, automatically (website-v2 pages).

The owner met an old-style Personal page after the home page was redesigned: a flat hero, two equal buttons, long text and a promo
banner. A page is only "on the standard" if a test says so, so this one holds every storefront page (website/index.html and every
website/<name>/index.html, so a new page is caught the day it is added) to the home page's pattern:

* a night-sky hero (`.sx-sky`, or `.sx-sea`) with exactly ONE primary button, never two equal ones;
* the shared look and page kit (`shared/lux.css`, `page.css`) and the one shared script (`site.js`), never a private copy;
* a proof strip whose every number is a fact marker the generator fills (no hand-kept count);
* no promo banner above the menu, and no claim that the code is "open source" (the licence is FSL-1.1-MIT);
* a length budget a phone can bear, measured in a static proxy: what is open (outside every fold) stays short, and the rest
  rides in "See more" folds, where nothing is deleted. A page that grows past the budget fails here, not in a person's thumb."""
import importlib.util
import pathlib
import re
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE = ROOT / "website"
PAGES = sorted([SITE / "index.html", *SITE.glob("*/index.html")])
_s = importlib.util.spec_from_file_location("features_sync", ROOT / "tools" / "features_sync.py")
fs = importlib.util.module_from_spec(_s)
_s.loader.exec_module(fs)

# The static budget for what is open on a page (outside every <details> fold and the header menu). Set from the pages as they
# are, with a little room; raise it only with a reason in the pull request, never to make a failing page pass.
MAX_OPEN_SECTIONS = 7      # the hero counts as one
MAX_OPEN_CARDS = 12
MAX_OPEN_WORDS = 650
TOOL_PAGES = {"assess"}    # a working form: its questions are the page, so only the hero, header and look are held


def rel(p: pathlib.Path) -> str:
    return str(p.relative_to(SITE))


class Open(HTMLParser):
    """Counts what a person sees without opening a fold: sections, cards and words."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.sections, self.cards, self.words, self.skip = [], 0, 0, 0, 0

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "img", "meta", "link", "input"):
            return
        cls = dict(attrs).get("class") or ""
        folded = tag == "details" or tag in ("script", "style", "head", "noscript", "header", "footer")
        self.stack.append(folded)
        if folded:
            self.skip += 1
        if not self.skip:
            if tag == "section":
                self.sections += 1
            if tag == "div" and "card" in cls.split():
                self.cards += 1

    def handle_endtag(self, tag):
        if tag in ("br", "img", "meta", "link", "input") or not self.stack:
            return
        if self.stack.pop():
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.words += len(data.split())


def measure(page: str) -> Open:
    p = Open()
    p.feed(page)
    return p


def hero_of(page: str) -> str:
    start = re.search(r'<section\b[^>]*\bclass="hero\b[^"]*"', page)
    assert start, "no hero section"
    return page[start.start():page.index("</section>", start.start())]


def test_there_are_storefront_pages_and_the_glob_finds_them_all():
    names = {rel(p) for p in PAGES}
    assert {"index.html", "personal/index.html", "nbfc/index.html", "assess/index.html"} <= names, names


def test_every_storefront_page_has_the_night_sky_hero_with_one_primary_button():
    for path in PAGES:
        page = path.read_text("utf-8")
        hero = hero_of(page)
        assert re.search(r'class="hero (?:sx-sky|sx-sea)\b', hero), f"{rel(path)}: the hero must be the shared .sx-sky (or .sx-sea)"
        assert 'id="hero"' in hero, f"{rel(path)}: the hero needs id=hero so the shared script can draw the sky"
        primaries = re.findall(r'class="btn [^"]*\bbtn-gold\b', hero)
        assert len(primaries) == 1, f"{rel(path)}: exactly one primary button in the first screen, found {len(primaries)}"
        assert hero.count('class="btn') == 1, f"{rel(path)}: the second action is a quiet text link, not a second button"
        assert 'class="quiet"' in hero or rel(path) in {"assess/index.html"}, f"{rel(path)}: one quiet text link beside the button"
        assert "<h1>" in hero, rel(path)


def test_every_storefront_page_uses_the_shared_pieces_and_keeps_no_private_copy():
    for path in PAGES:
        page, up = path.read_text("utf-8"), "../" if path.parent != SITE else ""
        for needed in (f'href="{up}site.css"', f'href="{up}shared/lux.css"', f'href="{up}page.css"', f'<script src="{up}site.js" defer>'):
            assert needed in page, f"{rel(path)}: missing {needed}"
        inline = "".join(re.findall(r"<style>(.*?)</style>", page, re.S))
        for private in (r"\.hero\b[^{]*\{", r"header\.nav\s*\{", r"\.proof\b[^{]*\{", r"(?:^|\})\s*\.btn(?:-gold)?\s*[{,]", r"(?:^|\})\s*footer\s*\{",
                        r"\.banner\s*\{", r"\.eyebrow\s*\{", r"\.seal-slot\b[^{]*\{"):
            assert not re.search(private, inline), f"{rel(path)}: a private copy of a shared rule ({private}); put it in website/page.css"
        assert 'class="banner"' not in page, f"{rel(path)}: no promo banner; say it once, quietly, low on the page"
        assert not re.search(r"open[- ]source(?! intelligence)", page, re.I), f"{rel(path)}: the licence is FSL-1.1-MIT (source available), never 'open source'"


def test_the_proof_strip_shows_only_counted_facts():
    known = set(fs.facts())
    for path in PAGES:
        page = path.read_text("utf-8")
        if '<div class="proof"' not in page:
            assert rel(path).split("/")[0] in TOOL_PAGES, f"{rel(path)}: a storefront page carries the proof strip"
            continue
        strip = page[page.index('<div class="proof"'):page.index("</ul>", page.index('<div class="proof"'))]
        figures = re.findall(r"<b>(.*?)</b>", strip, re.S)
        assert len(figures) == 4, f"{rel(path)}: four proof figures, found {len(figures)}"
        for figure in figures:
            marker = re.search(r"<!-- fact:(\w+) -->", figure)
            assert marker and marker.group(1) in known, f"{rel(path)}: proof figure {figure!r} is not a fact marker the generator fills"
            assert not re.sub(r"<!--.*?-->|&lt;|&#8202;|[\s<]|ms|[\d+]|of", "", figure), f"{rel(path)}: hand-typed text in a proof figure: {figure!r}"


def test_no_page_is_longer_than_the_budget():
    for path in PAGES:
        if path.parent.name in TOOL_PAGES:
            continue
        m = measure(path.read_text("utf-8"))
        assert m.sections <= MAX_OPEN_SECTIONS, f"{rel(path)}: {m.sections} open sections (budget {MAX_OPEN_SECTIONS}); fold the rest under 'See more'"
        assert m.cards <= MAX_OPEN_CARDS, f"{rel(path)}: {m.cards} open cards (budget {MAX_OPEN_CARDS})"
        assert m.words <= MAX_OPEN_WORDS, f"{rel(path)}: {m.words} open words (budget {MAX_OPEN_WORDS}); shorten, or fold what is not the vital few"


def test_a_page_folds_its_long_tail_under_one_see_more():
    for path in PAGES:
        page = path.read_text("utf-8")
        if path.parent.name in TOOL_PAGES:
            continue
        assert page.count('<details class="everything"') == 1, f"{rel(path)}: one 'See more' fold holds the long tail"
        assert re.search(r'<details class="everything"[^>]*>\s*<summary><span>See ', page), rel(path)


def test_the_shared_script_finds_the_sky_next_to_itself_on_any_page_depth():
    script = (SITE / "site.js").read_text("utf-8")
    assert "currentScript" in script and "shared/sky.js" in script, "the sky path must come from the script's own address"
    assert "prefers-reduced-motion" in (ROOT / "guiding-map" / "shared" / "sky.js").read_text("utf-8")
    build = (SITE / "build.sh").read_text("utf-8")
    assert "shared/lux.css guiding-map/shared/sky.js website/shared/" in build
