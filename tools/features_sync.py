#!/usr/bin/env python3
"""One list of features, and the facts about the estate, written everywhere a person looks, so nothing is kept by hand.

    python3 tools/features_sync.py           rewrite every generated part
    python3 tools/features_sync.py --check   exit 1 when anything is behind (the features-current fitness check runs this in CI)
    python3 tools/features_sync.py --list    the features, for a terminal (./securax features)

From features.json (what SecuRAX can do, in plain words) it writes:
  * guiding-map/features.js      the "Everything SecuRAX can do" cards in the Command Center (hub.html)
  * website/index.html           the "whole estate" section of the product site   <!-- features:start --> ... <!-- features:end -->
  * docs/index.md                the docs home page table                         (same markers)
  * README.md                    the "What you can do" table                      (same markers)
From products.json (what SecuRAX sells: each product, its price and its screenshot) it writes:
  * website/index.html           the "Products" section, with each product's real screenshot    <!-- products:start --> ... <!-- products:end -->
  * docs/securax/106-...md       the catalogue and price table in doc 106                         (same markers)
A product's light is the weakest light of its features, so no page claims more than the code proves.
From the code itself it writes the FACTS (how many tests, journeys, mapped frameworks, docs) wherever a page shows one as
<!-- fact:NAME -->123<!-- /fact -->, in the README, the website, the docs and the portal pages.
Each feature's status light comes from its guide's light in docs/status.yml; its docs link from REPO_SLUG in brand.env.
It also refuses a feature whose command, guide or nav entry does not exist. Standard library only.
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FEATURES = ROOT / "features.json"
HUB_JS = ROOT / "guiding-map" / "features.js"
BLOCKS = {ROOT / "website" / "index.html": "html", ROOT / "docs" / "index.md": "docs", ROOT / "README.md": "readme"}
PRODUCTS = ROOT / "products.json"
PRODUCT_BLOCKS = {ROOT / "website" / "index.html": "html", ROOT / "docs" / "securax" / "106-WHO-SECURAX-IS-FOR.md": "docs"}
FACT_FILES = ["README.md", "website/index.html", "portal/explainer.html", "docs/**/*.md"]
LIGHT = {"green": ("🟢", "l-g", "Built and proven"), "amber": ("🟡", "l-a", "Partly built"), "red": ("🔴", "l-r", "Not built yet")}
E = html.escape


# ---------------------------------------------------------------------------------------------------- sources
def load() -> dict:
    return json.loads(FEATURES.read_text("utf-8"))


def lights() -> dict[str, str]:
    """{doc path under docs/: green|amber|red} from docs/status.yml (one 'path: [light, "text"]' per line)."""
    out = {}
    for line in (ROOT / "docs" / "status.yml").read_text("utf-8").splitlines():
        m = re.match(r"^([\w./-]+\.md):\s*\[(green|amber|red)\b", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def docs_base() -> str:
    """The published docs (GitHub Pages) for this repository, from REPO_SLUG in brand.env only (never the environment)."""
    slug = ""
    for line in (ROOT / "brand.env").read_text("utf-8").splitlines():
        m = re.match(r"^\s*REPO_SLUG\s*=\s*(\S+)", line.split(" #")[0])
        if m:
            slug = m.group(1).strip("'\"")
    owner, _, repo = (slug or "owner/repo").partition("/")
    return f"https://{owner}.github.io/{repo}/"


def commands() -> set[str]:
    src = (ROOT / "securax").read_text("utf-8")
    return {c for m in re.finditer(r"^  ([a-z][a-z0-9|\-]*)\)\s*$", src, re.M) for c in m.group(1).split("|")}


def tracked() -> list[str]:
    r = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
    return r.stdout.splitlines()


def facts() -> dict[str, str]:
    """Numbers a page may show, counted from the code on every run."""
    files = tracked()
    tests = 0
    for f in files:
        name = pathlib.Path(f).name
        if f.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py")) and (ROOT / f).exists():
            tests += len(re.findall(r"^\s*(?:async\s+)?def test_", (ROOT / f).read_text("utf-8", "ignore"), re.M))
    journeys = len(re.findall(r"^@journey\(", (ROOT / "sandbox" / "run.py").read_text("utf-8"), re.M))
    maps = re.search(r"^MAPS = \{(.*?)\}", (ROOT / "governance" / "regmap.py").read_text("utf-8"), re.M | re.S)
    docs = [f for f in files if re.match(r"docs/securax/\d\d-.*\.md$", f)]
    # tests rounded down to the nearest 50 ("750+"), so adding one test does not make every page stale
    return {"tests": f"{tests // 50 * 50}+", "journeys": str(journeys), "frameworks": str(len(re.findall(r'"[\w-]+":\s*"regmap-', maps.group(1))) if maps else 0),
            "docs": str(len(docs)), "features": str(len(load()["features"]))}


def problems(data: dict | None = None) -> list[str]:
    data = data or load()
    cmds, nav = commands(), (ROOT / "mkdocs.yml").read_text("utf-8")
    out, seen = [], set()
    for f in data["features"]:
        where = f"feature {f.get('id')}"
        if f["id"] in seen:
            out.append(f"{where}: the id is used twice")
        seen.add(f["id"])
        if f["group"] not in data["groups"]:
            out.append(f"{where}: group '{f['group']}' is not in groups")
        if f["command"] not in cmds:
            out.append(f"{where}: ./securax {f['command']} does not exist")
        if not (ROOT / "docs" / f["doc"]).exists():
            out.append(f"{where}: its guide docs/{f['doc']} does not exist")
        elif f["doc"] not in nav:
            out.append(f"{where}: its guide {f['doc']} is not in the mkdocs.yml nav")
        if not f.get("icon"):
            out.append(f"{where}: needs an icon name (the Command Center draws it; no emoji)")
        if not f["open"].get("cmd", "").startswith("./securax "):
            out.append(f"{where}: open.cmd must be a ./securax command")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(f.get("added", ""))):
            out.append(f"{where}: needs 'added' (YYYY-MM-DD, the day it first shipped) so every page can show what is new")
    out += product_problems(data, cmds)
    return out


def load_products() -> list[dict]:
    return json.loads(PRODUCTS.read_text("utf-8"))["products"] if PRODUCTS.exists() else []


def product_problems(data: dict, cmds: set[str]) -> list[str]:
    out, ids = [], {f["id"] for f in data["features"]}
    for p in load_products():
        where = f"product {p.get('id')}"
        for k in ("id", "name", "kicker", "tagline", "for", "what", "features", "price", "anchor", "shot", "role", "kill_if"):
            if not p.get(k):
                out.append(f"{where}: needs '{k}'")
        out += [f"{where}: feature '{x}' is not in features.json" for x in p.get("features", []) if x not in ids]
        out += [f"{where}: ./securax {c} does not exist" for c in p.get("commands", []) if c not in cmds]
        if p.get("role") and p["role"] not in ("core", "bet"):
            out.append(f"{where}: role must be core or bet (doc 107)")
        if p.get("kill_if") and not re.search(r"\d{4}-\d{2}-\d{2}", p["kill_if"]):
            out.append(f"{where}: kill_if needs a date, so the test cannot drift (doc 107)")
        if not (ROOT / "website" / "img" / "products" / f"{p.get('id')}.png").exists():
            out.append(f"{where}: no screenshot website/img/products/{p.get('id')}.png (python3 tools/screenshots.py {p.get('id')})")
    return out


def product_light(p: dict, data: dict) -> str:
    """The weakest light of the product's features: a product is only as built as its least-built part."""
    li, docs = lights(), {f["id"]: f["doc"] for f in data["features"]}
    order = ["red", "amber", "green"]
    return min((li.get(docs[x], "amber") for x in p["features"] if x in docs), key=order.index, default="amber")


def products_html(data: dict) -> str:
    cards = []
    for p in load_products():
        _, cls, label = LIGHT[product_light(p, data)]
        cards.append(
            f'    <article class="card prod" id="p-{E(p["id"])}">\n'
            f'      <img src="img/products/{E(p["id"])}.png" alt="{E(p["shot"]["alt"])}" loading="lazy" width="1280" height="800">\n'
            f'      <span class="kicker">{E(p["kicker"])}</span><h3>{E(p["name"])}</h3><p class="tag">{E(p["tagline"])}</p>\n'
            f'      <p>{E(p["what"])}</p><p class="for"><b>For:</b> {E(p["for"])}</p>\n'
            f'      <p class="price">{E(p["price"])}</p><span class="light {cls}">{label}</span>\n    </article>')
    return ('<section id="products">\n  <div class="wrap center">\n    <span class="kicker">Products</span>\n'
            f"    <h2>{len(cards)} products, one estate.</h2>\n"
            '    <p class="sub">Buy one, or the whole estate. Every screenshot is the real product on sample data, and every light comes from '
            "its tests. Prices are founding prices, set with our design partners.</p>\n"
            '  </div>\n  <div class="wrap grid3 prods">\n' + "\n".join(cards) + "\n  </div>\n</section>")


def products_docs(data: dict) -> str:
    rows = ["| Product | Line | For | What it is | Price (hypothesis) | Set against | Stop or change if | Status |", "|---|---|---|---|---|---|---|---|"]
    for p in load_products():
        icon, _, label = LIGHT[product_light(p, data)]
        rows.append(f"| **{p['name']}** ({p['kicker']}) | {p['role']} | {p['for']} | {p['tagline']} | {p['price']} | {p['anchor']} | {p['kill_if']} | {icon} {label} |")
    return ("Generated from [`products.json`](../../products.json) by `tools/features_sync.py`: edit that file to change a product or a price. "
            "Community (the open-source core) stays free.\n\n" + "\n".join(rows))


def put_products(text: str, body: str, kind: str) -> str:
    start, end = ("<!-- products:start -->", "<!-- products:end -->")
    rx = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not rx.search(text):
        raise SystemExit(f"no {start} marker in a {kind} page: add the two markers where the catalogue belongs")
    return rx.sub(lambda _: f"{start}\n{body}\n{end}", text)


def latest(data: dict, n: int = 5) -> list[dict]:
    """The most recent additions, newest first (ties keep the file's order). A fixed count, not 'the last 30 days', so the
    generated pages do not change by themselves as days pass."""
    order = {f["id"]: i for i, f in enumerate(data["features"])}
    return sorted(data["features"], key=lambda f: (f.get("added", ""), -order[f["id"]]), reverse=True)[:n]


# ---------------------------------------------------------------------------------------------------- renderers
def hub_js(data: dict) -> str:
    li, base = lights(), docs_base()
    rows = [{"id": f["id"], "group": f["group"], "icon": f["icon"], "name": f["name"], "what": f["what"], "cmd": f["open"]["cmd"],
             "path": f["open"].get("path", ""), "port": f["open"].get("port", 0), "service": bool(f.get("service")), "added": f.get("added", ""),
             "outcome": f.get("outcome", ""), "shows": f.get("shows", ""),
             "light": li.get(f["doc"], "amber"), "guide": base + f["doc"][:-3] + "/"} for f in data["features"]]
    return ("// GENERATED by tools/features_sync.py from features.json. Edit that file and run the tool; CI checks this one is current.\n"
            "window.SECURAX_FEATURES = " + json.dumps({"groups": data["groups"], "features": rows}, ensure_ascii=False, indent=1) + ";\n")


def block_html(data: dict) -> str:
    li = lights()
    cards = []
    for f in data["features"]:
        if not f.get("highlight"):
            continue
        _, cls, label = LIGHT[li.get(f["doc"], "amber")]
        cards.append(f'    <div class="card"><h3>{E(f["name"])}</h3><p>{E(f["what"])}</p><span class="light {cls}">{label}</span></div>')
    return ('<section class="alt" id="estate">\n  <div class="wrap center">\n    <span class="kicker">The whole estate</span>\n'
            "    <h2>More than a gateway.</h2>\n"
            f'    <p class="sub">The gateway is one of <!-- fact:features -->{len(data["features"])}<!-- /fact --> things SecuRAX does. These are the ones people use most.</p>\n'
            '  </div>\n  <div class="wrap grid3">\n' + "\n".join(cards) + "\n  </div>\n</section>")


def _table(data: dict, link) -> str:
    li, out = lights(), []
    for g in data["groups"]:
        rows = [f for f in data["features"] if f["group"] == g]
        out += [f"**{g}**", "", "| | What it does | How to open it |", "|---|---|---|"]
        for f in rows:
            out.append(f"| {LIGHT[li.get(f['doc'], 'amber')][0]} [{f['name']}]({link(f['doc'])}) | {f['what']} | `{f['open']['cmd']}` |")
        out.append("")
    return "\n".join(out).rstrip()


def _latest(data: dict, link) -> str:
    rows = [f"- **{f['added']}** · [{f['name']}]({link(f['doc'])}): {f['outcome']} `{f['open']['cmd']}`" for f in latest(data)]
    return "### New in the estate\n\nThe latest additions, newest first (the Command Center marks each one New for 30 days):\n\n" + "\n".join(rows) + "\n\n"


def block_docs(data: dict) -> str:
    return ("## Everything SecuRAX can do\n\n" + _latest(data, lambda d: d) + "Each line names what it does, in plain words, and the one command that opens it. "
            "The light is the guide's status (what the lights mean is below).\n\n" + _table(data, lambda d: d))


def block_readme(data: dict) -> str:
    return ("## What you can do\n\n" + _latest(data, lambda d: "docs/" + d) + _table(data, lambda d: "docs/" + d)
            + "\n\nThis list is generated from [`features.json`](features.json); the Command Center, the website and the docs home page show the same one.")


RENDER = {"html": block_html, "docs": block_docs, "readme": block_readme}


def put_block(text: str, body: str, kind: str) -> str:
    start, end = ("<!-- features:start -->", "<!-- features:end -->")
    rx = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not rx.search(text):
        raise SystemExit(f"no {start} marker in a {kind} page: add the two markers where the block belongs")
    return rx.sub(lambda _: f"{start}\n{body}\n{end}", text)


def put_facts(text: str, f: dict) -> str:
    return re.sub(r"<!-- fact:(\w+) -->.*?<!-- /fact -->", lambda m: f"<!-- fact:{m.group(1)} -->{f.get(m.group(1), m.group(0))}<!-- /fact -->"
                  if m.group(1) in f else m.group(0), text)


def outputs() -> dict[pathlib.Path, str]:
    data = load()
    f = facts()
    out = {HUB_JS: hub_js(data)}
    for path, kind in BLOCKS.items():
        out[path] = put_block(path.read_text("utf-8"), RENDER[kind](data), kind)
    if PRODUCTS.exists():
        for path, kind in PRODUCT_BLOCKS.items():
            text = out.get(path, path.read_text("utf-8"))
            out[path] = put_products(text, products_html(data) if kind == "html" else products_docs(data), kind)
    for pattern in FACT_FILES:
        for path in sorted(ROOT.glob(pattern)):
            text = out.get(path, path.read_text("utf-8") if path.exists() else "")
            if "<!-- fact:" in text:
                out[path] = put_facts(text, f)
    return out


def listing(data: dict) -> str:
    lines = ["Everything SecuRAX can do (features.json). Type the command on the right; the guide is in the docs.", "", "NEW IN THE ESTATE"]
    lines += [f"  {f['added']}  {f['name']:<36} {f['open']['cmd']}" for f in latest(data)]
    lines.append("")
    for g in data["groups"]:
        lines.append(g.upper())
        for f in data["features"]:
            if f["group"] == g:
                lines.append(f"  {f['name']:<36} {f['open']['cmd']}")
        lines.append("")
    return "\n".join(lines).rstrip()


def main(argv: list[str]) -> int:
    if "--list" in argv:
        print(listing(load()))
        return 0
    probs = problems()
    if probs:
        print("\n".join("✗ " + p for p in probs))
        return 1
    stale = [p for p, text in outputs().items() if not p.exists() or p.read_text("utf-8") != text]
    if "--check" in argv:
        if stale:
            print("behind: " + ", ".join(str(p.relative_to(ROOT)) for p in stale) + "  →  python3 tools/features_sync.py")
            return 1
        print("✔ features and facts are current everywhere")
        return 0
    for p, text in outputs().items():
        if p in stale:
            p.write_text(text, "utf-8")
            print(f"updated {p.relative_to(ROOT)}")
    if not stale:
        print("✔ already current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
