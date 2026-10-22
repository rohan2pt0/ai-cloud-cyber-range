"""SecuRAX's own licence (LICENSING.md): from v0.4.0 the code is FSL-1.1-MIT, so no page may still call SecuRAX itself
"MIT-licensed open source". Open-source tools and open models are other people's software and may be called that."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
STALE = re.compile(r"MIT-licensed open source|open source under the MIT|open source \(MIT\)|free and open source \(MIT\)|core is open source", re.I)


def test_the_licence_is_fsl_with_the_mit_future_grant_and_explained_plainly():
    text = (ROOT / "LICENSE").read_text("utf-8")
    assert text.startswith("# Functional Source License, Version 1.1, MIT Future License") and "${" not in text
    plain = (ROOT / "LICENSING.md").read_text("utf-8")
    assert "v0.3.0" in plain and "two years" in plain and "Competing Use" in plain


def test_no_page_still_calls_securax_mit_licensed_open_source():
    pages = [*sorted((ROOT / "website").glob("**/*.html")), ROOT / "README.md", ROOT / "TRADEMARKS.md", ROOT / "CONTRIBUTING.md",
             ROOT / "mkdocs.yml", ROOT / "website" / "build.sh"]
    bad = [f"{p.relative_to(ROOT)}: {m.group(0)}" for p in pages if p.exists() for m in [STALE.search(p.read_text("utf-8"))] if m]
    assert not bad, bad
