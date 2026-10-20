"""Google Keep notes come into the Life OS Inbox: unticked list lines as actions to decide, plain notes as notes, ticked lines and
the bin left out, each note once. A synthetic Takeout zip; nothing personal."""
import importlib.util
import json
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("lifeos", ROOT / "governance" / "lifeos.py")
lo = importlib.util.module_from_spec(_s)
_s.loader.exec_module(lo)


def takeout(path):
    notes = {
        "Takeout/Keep/Home.json": {"title": "Home", "listContent": [{"text": "Fix the garage lock", "isChecked": False}, {"text": "Buy bulbs", "isChecked": True}]},
        "Takeout/Keep/Idea.json": {"title": "Idea", "textContent": "A family offsite in March", "labels": [{"name": "family"}]},
        "Takeout/Keep/Old.json": {"title": "Old", "textContent": "gone", "isTrashed": True},
        "Takeout/Keep/Labels.json": [],
    }
    with zipfile.ZipFile(path, "w") as z:
        for n, d in notes.items():
            z.writestr(n, json.dumps(d))
        z.writestr("Takeout/Keep/photo.png", b"x")


def test_keep_lines_become_actions_and_notes_stay_notes_once(tmp_path):
    z = tmp_path / "takeout-20261020.zip"
    takeout(z)
    items = lo.convert(z)
    assert [(x["t"], x["kind"], x["area"]) for x in items] == [("Fix the garage lock", "action", "Home"), ("Idea: A family offsite in March", "note", "family")]
    out = tmp_path / "inbox-import.json"
    assert lo.write(items, out) == (2, 2) and lo.write(lo.convert(z), out) == (0, 2)            # the second import adds nothing
    assert oct(out.stat().st_mode & 0o777) == "0o600"
