"""./securax finish: every optional part with its steps; items the estate can check tick themselves, the rest are ticked by you."""
import importlib.util
import pathlib

_s = importlib.util.spec_from_file_location("finish", pathlib.Path(__file__).resolve().parent.parent / "finish.py")
fin = importlib.util.module_from_spec(_s)
_s.loader.exec_module(fin)


def _iso(tmp_path, monkeypatch):
    monkeypatch.setattr(fin, "MARKS", tmp_path / "finish.json")
    monkeypatch.setattr(fin, "ENVF", tmp_path / ".env")
    monkeypatch.setattr(fin, "ROOT", tmp_path)
    for k in ("SECURAX_BACKUP_KEYFILE", "SECURAX_OFFSITE_DIR", "SECURAX_NOTIFY_NTFY", "SECURAX_NOTIFY_WEBHOOK"):
        monkeypatch.delenv(k, raising=False)


def test_the_steps_follow_the_domain_and_repository_in_brand_env(tmp_path, monkeypatch):
    _iso(tmp_path, monkeypatch)
    its = fin.items({"SITE_DOMAIN": "new-name.example", "REPO_SLUG": "me/site"})
    text = " ".join(" ".join(i["steps"]) + i["title"] for i in its)
    assert "new-name.example" in text and "https://me.github.io/site/" in text and "SITE_PAGES" in text
    assert all(i["steps"] and i["gives"] for i in its)


def test_checks_tick_themselves_and_manual_items_are_marked_once(tmp_path, monkeypatch, capsys):
    _iso(tmp_path, monkeypatch)
    (tmp_path / ".env").write_text("SECURAX_BACKUP_KEYFILE=/mnt/e/k.key\n")
    st = {s["id"]: s for s in fin.status()}
    assert st["backup-key"]["done"] and st["backup-key"]["how"] == "checked" and not st["offsite-backup"]["done"]
    assert fin.main(["done", "product-site"]) == 0 and {s["id"]: s for s in fin.status()}["product-site"]["done"]
    assert fin.main(["undo", "product-site"]) == 0 and not {s["id"]: s for s in fin.status()}["product-site"]["done"]
    assert fin.main(["done", "nonsense"]) == 2
    capsys.readouterr()
    assert fin.main([]) == 0 and "Next: " in capsys.readouterr().out


def test_the_command_center_card_lists_what_is_left_first_with_numbered_steps(tmp_path, monkeypatch):
    _iso(tmp_path, monkeypatch)
    card = fin.html_card()
    assert "Finish setting up" in card and "<ol><li>" in card and "<script" not in card
    assert card.index("○") < card.index("done</summary>") if "done</summary>" in card else True
