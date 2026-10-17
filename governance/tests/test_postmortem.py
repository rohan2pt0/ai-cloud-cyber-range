import datetime as dt
import importlib.util
import pathlib

_s = importlib.util.spec_from_file_location("postmortem", pathlib.Path(__file__).resolve().parent.parent / "postmortem.py")
pm = importlib.util.module_from_spec(_s)
_s.loader.exec_module(pm)


def test_new_writes_a_blameless_template_with_dated_mechanism_actions(tmp_path):
    p = pm.new("Chat down after update!", "sev2", dt.date(2026, 10, 17), tmp_path)
    t = p.read_text()
    assert p.name == "2026-10-17-chat-down-after-update.md" and "Blameless" in t and "five whys" in t and "due: 2026-10-31" in t
    assert pm.new("Chat down after update!", "sev2", dt.date(2026, 10, 17), tmp_path).name.endswith("-2.md")   # never overwrites


def test_open_actions_flag_overdue_and_ownerless_and_ignore_done(tmp_path):
    (tmp_path / "a.md").write_text(
        "- [ ] add a fitness check — owner: me — due: 2026-10-01\n"
        "- [ ] rotate the key\n"
        "- [x] done thing — owner: me — due: 2026-01-01\n"
        "- [ ] alert earlier — owner: me — due: 2026-12-01\n")
    acts = pm.actions(tmp_path, dt.date(2026, 10, 17))
    assert [a["action"] for a in acts] == ["add a fitness check", "rotate the key", "alert earlier"]
    assert acts[0]["problems"] == ["overdue since 2026-10-01"] and set(acts[1]["problems"]) == {"no owner", "no due date"}
    assert acts[2]["problems"] == []
