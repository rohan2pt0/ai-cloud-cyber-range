"""Every documentation page carries a status light from docs/status.yml, and the pages agree with that file."""
import pathlib
import re
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
UNLIT = {"index.md", "reference/cli.md", "reference/changelog.md"}      # the home page and generated pages


def test_pages_match_status_file_and_glance_totals_are_true():
    r = subprocess.run([sys.executable, str(ROOT / "docs/sync_status.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_every_page_in_the_site_nav_has_a_light():
    nav_pages = set(re.findall(r":\s*([\w./-]+\.md)\s*$", (ROOT / "mkdocs.yml").read_text(), re.M))
    lit = set(yaml.safe_load((ROOT / "docs/status.yml").read_text()))
    assert nav_pages - UNLIT <= lit, sorted(nav_pages - UNLIT - lit)
