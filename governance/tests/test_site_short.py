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
    start = page.index('<section id="capabilities">')
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
