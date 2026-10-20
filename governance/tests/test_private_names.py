"""The private-names guard: only fingerprints are stored, one- to six-word names are found anywhere in a line or a file name,
and the real repository is clean."""
import importlib.util
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("private_names", ROOT / "governance" / "private_names.py")
pn = importlib.util.module_from_spec(_s)
_s.loader.exec_module(pn)


def test_names_are_found_in_any_case_and_across_punctuation_but_never_stored():
    fps = {pn.fingerprint("Fictional Agency"), pn.fingerprint("ZQXJ")}
    text = "first line\nreport to the FICTIONAL-agency today\nand zqxj/cert too\nfictional agencies are fine"
    assert [n for n, _ in pn.hits(text, fps)] == [2, 3]
    assert pn.fingerprint("Fictional  Agency!") == pn.fingerprint("fictional agency")


def test_add_stores_only_the_fingerprint(tmp_path):
    f = tmp_path / "names.json"
    assert pn.add("Fictional Agency", f) and not pn.add("fictional agency", f)
    assert "Fictional" not in f.read_text() and json.loads(f.read_text())["fingerprints"] == [pn.fingerprint("fictional agency")]


def test_a_file_name_and_a_private_vault_list_count_too(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "zqxj-pack.json").write_text("{}")
    (tmp_path / "notes.md").write_text("nothing here\nbut Other Secret Org here\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    private = tmp_path / "private.txt"
    private.write_text("# my list\nOther Secret Org\n")
    fps = pn.load(tmp_path / "none.json", private) | {pn.fingerprint("zqxj pack")}
    assert pn.problems(tmp_path, fps) == ["notes.md:2", "zqxj-pack.json: the file name"]


def test_the_repository_names_no_private_name():
    assert pn.problems() == []
