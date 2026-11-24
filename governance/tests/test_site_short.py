"""The product site's home page fits a phone: the estate and the products are folded, not deleted (website-v2, slice 1).

A person on a phone met a 25,819 px page. Its two longest sections are now six cards and one fold: every feature and every
product's detail is still there, inside a plain details and summary, so nothing is lost and nothing needs a script."""
import importlib.util
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("features_sync", ROOT / "tools" / "features_sync.py")
fs = importlib.util.module_from_spec(_s)
_s.loader.exec_module(fs)


def between(text: str, start: str, end: str) -> str:
    return text[text.index(start) + len(start):text.index(end)]


def test_capabilities_show_three_strongest_then_fold_the_rest():
    page = (ROOT / "website" / "index.html").read_text("utf-8")
    start = re.search(r'<section[^>]*\bid="capabilities"', page).start()   # website-v2 gave it the alternate background
    block = page[start:page.index("</section>", start)]
    assert "<details" in block, "the seven weaker capabilities should be folded, not all open"
    open_cards = block[:block.index("<details")].count('<div class="card">')
    assert open_cards == 3, "the three strongest capabilities stay open before the fold"
    titles = re.findall(r"<h3>(.*?)</h3>", block, re.S)
    assert titles[:3] == ["Prompt-attack rails", "India-grade PII redaction", "Data residency routing"], titles[:3]
    assert block.count("<details") == 1, "the other seven ride in one fold"
    summary = re.search(r"<summary>(.*?)</summary>", block, re.S).group(1).strip()
    assert summary == "See all 10"
    all_titles = ["Prompt-attack rails", "India-grade PII redaction", "Data residency routing",
                  "Audit trail and evidence", "Multi-model failover", "Agent and tool-call guard",
                  "Identity and roles", "SIEM integration", "Admin console", "GDPR and EU AI Act maps"]
    assert len(titles) == len(all_titles) == 10, titles
    for title in all_titles:
        assert title in titles, title


def test_the_estate_is_six_cards_then_one_fold_with_everything_else():
    page = (ROOT / "website" / "index.html").read_text("utf-8")
    block = between(page, "<!-- features:start -->", "<!-- features:end -->")
    data = fs.load()
    open_cards = block[:block.index("<details")].count('<div class="card">')
    assert open_cards <= 6, "a phone should scroll past at most six cards before the fold"
    assert open_cards == 6, "the six newest features stay open"
    assert block.count("<details") == 1, "everything else rides in one fold"
    summary = re.search(r"<summary>(.*?)</summary>", block, re.S).group(1).strip()
    assert summary == f"All {len(data['features'])} things SecuRAX does"
    assert block.count('<div class="card">') == len(data["features"]), "every feature is still shown, only folded"


def test_the_home_page_keeps_the_vital_few_open_and_folds_everything_else_once():
    # website-v2: hero, proof, how, capabilities and editions stay open; the estate, the products, Readiness and the FAQ
    # ride in one "See every capability (n)" fold, and the proof strip shows only counted facts.
    page = (ROOT / "website" / "index.html").read_text("utf-8")
    fold = page[page.index('<details class="everything"'):page.index('<section class="closing"')]
    for inside in ("<!-- features:start -->", "<!-- products:start -->", 'id="readiness"', 'class="faq"'):
        assert inside in fold, inside
    assert re.search(r"<summary><span>See every capability \(<!-- fact:features -->\d+<!-- /fact -->\)</span></summary>", fold)
    proof = page[page.index('<div class="proof"'):page.index('<section id="how">')]
    assert [m for m in re.findall(r"<!-- fact:(\w+) -->", proof)] == ["attacks", "refuse_ms", "tests", "frameworks"]
    hero = page[page.index('<section class="hero'):page.index("</section>", page.index('<section class="hero'))]
    assert hero.count('class="btn') == 1, "one primary action in the first screen"
    assert not re.search(r"\d{10}|PAN [A-Z]{5}\d{4}[A-Z]|install\.txt", hero), "no sample personal data and no raw install address up top"


def test_each_product_keeps_its_face_and_folds_what_and_for_under_more():
    page = (ROOT / "website" / "index.html").read_text("utf-8")
    block = between(page, "<!-- products:start -->", "<!-- products:end -->")
    cards = block.split('<article class="card prod"')[1:]
    products = fs.load_products()
    assert len(cards) == len(products) == 8
    for p, card in zip(products, cards):
        body = card.split("</article>")[0]
        for needed in (f'img src="img/products/{p["id"]}.png"', f'<span class="kicker">{fs.E(p["kicker"])}</span>',
                       f'<h3>{fs.E(p["name"])}</h3>', f'<p class="tag">{fs.E(p["tagline"])}</p>',
                       f'<p class="price">{fs.E(p["price"])}</p>', '<span class="light '):
            assert needed in body, (p["id"], needed)
        assert body.count("<details") == 1 and re.search(r"<summary>\s*More\s*</summary>", body), p["id"]
        fold = body[body.index("<details"):body.index("</details>")]
        assert fs.E(p["what"]) in fold and f'<b>For:</b> {fs.E(p["for"])}' in fold, p["id"]


def _media_body(css: str, width: int):
    """The body of the first @media (max-width: <width>px) block, by matching braces."""
    match = re.search(r"@media\s*\(\s*max-width\s*:\s*" + str(width) + r"px\s*\)\s*\{", css)
    if not match:
        return None
    depth, i = 1, match.end()
    while i < len(css) and depth:
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
        i += 1
    return css[match.end():i - 1]


def _rules(css: str):
    """(selectors, declarations) for each rule in a style block body."""
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        yield [s.strip() for s in selector.split(",")], body


def _decls(body: str):
    out = {}
    for part in body.split(";"):
        if ":" in part:
            prop, value = part.split(":", 1)
            out[prop.strip().lower()] = " ".join(value.split()).lower()
    return out


def test_on_a_phone_the_products_are_one_sideways_row():
    page = (ROOT / "website" / "index.html").read_text("utf-8")
    css = between(page, "<style>", "</style>")

    block = _media_body(css, 640)
    assert block is not None, "a max-width 640px media query should hold the phone layout"
    rules = list(_rules(block))

    row = next((_decls(body) for sels, body in rules if any(sel == ".prods" for sel in sels)), None)
    assert row is not None, "the phone rule should give .prods a row"
    assert row.get("display") == "flex", row
    assert row.get("overflow-x") == "auto", row
    assert row.get("scroll-snap-type") == "x mandatory", row

    card = next((_decls(body) for sels, body in rules if any(" ".join(sel.split()) == ".prods .prod" for sel in sels)), None)
    assert card is not None, "the phone rule should size each .prods .prod card"
    flex = card.get("flex", "")
    basis = card.get("flex-basis", "")
    parsed = flex.split()[2] if len(flex.split()) == 3 else basis
    assert parsed.endswith("%"), card
    assert 80 <= float(parsed[:-1]) <= 90, "a card should be near 85% wide, with a peek of the next"
    assert card.get("scroll-snap-align") == "start", card

    products = between(page, "<!-- products:start -->", "<!-- products:end -->")
    assert products.count('<article class="card prod"') == 8, "all eight products stay on the page"

    for value in re.findall(r"(?<![-a-z])width\s*:\s*(\d+(?:\.\d+)?)vw", page, re.I):
        assert float(value) <= 100, f"the body must not scroll sideways (width:{value}vw)"
