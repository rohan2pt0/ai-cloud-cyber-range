"""tools/screenshots.py (doc 106): product screenshots are taken on sample data only. It refuses a checkout that holds private data
in vault/, so a real register, workbook or assessment can never end up on the product site."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("securax_screenshots_t", ROOT / "tools" / "screenshots.py")
sh = importlib.util.module_from_spec(_s)
_s.loader.exec_module(sh)


def test_private_data_in_the_vault_blocks_screenshots(tmp_path):
    (tmp_path / "vault" / "readiness").mkdir(parents=True)
    (tmp_path / "vault" / "readiness" / "sample-nbfc-fake.json").write_text("{}")
    assert sh.private_files(tmp_path) == []                                     # the sample is allowed
    (tmp_path / "vault" / "controls").mkdir()
    (tmp_path / "vault" / "controls" / "library.json").write_text("{}")         # a real imported workbook
    assert sh.private_files(tmp_path) == ["vault/controls/library.json"]


def test_every_product_has_a_shot_kind_the_tool_knows():
    import json
    for p in json.loads((ROOT / "products.json").read_text())["products"]:
        assert p["shot"]["kind"] in ("page", "terminal", "gateway", "range"), p["id"]
        if p["shot"]["kind"] == "page":
            assert (ROOT / p["shot"]["page"]).exists() or p["shot"].get("prepare"), p["id"]
