"""governance/backlog.py (doc 103): nothing started or promised is lost when a session ends. Deferred asks, dated promises
due or late, open pull requests and branches without one are all listed; finished and ledger rows are not; and when GitHub
cannot be asked the list says so instead of looking empty."""
import datetime as dt
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("securax_backlog_t", ROOT / "governance" / "backlog.py")
bl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bl)
TODAY = dt.date(2026, 10, 22)


def test_deferred_asks_are_listed_until_done_and_late_ones_are_marked(tmp_path):
    q = tmp_path / "queue.json"
    q.write_text(json.dumps({"items": [
        {"id": "a", "ask": "late one", "due": "2026-10-20", "state": "open"},
        {"id": "b", "ask": "waiting for the owner", "due": "", "state": "waiting-owner"},
        {"id": "c", "ask": "finished", "due": "2026-10-01", "state": "done"}]}))
    items = bl.queue_items(TODAY, q)
    assert [i["title"] for i in items] == ["late one", "waiting for the owner"]
    assert items[0]["overdue"] and items[0]["days"] == -2 and not items[1]["overdue"]


def test_dated_promises_due_soon_or_late_are_found_and_finished_or_ledger_rows_are_not(tmp_path):
    (tmp_path / "x.md").write_text("\n".join([
        "| Step | By |", "|---|---|",
        "| Late promise | 2026-10-01 |",
        "| Soon promise | **2026-10-30** |",
        "| Far promise | 2027-03-01 |",
        "| ~~Struck~~ done 2026-10-10 | ~~2026-10-15~~ |",
        "| Said done | done 2026-10-05 |",
        "| 2026-10-02 | a ledger entry: something that happened |"]))
    got = {i["title"]: i for i in bl.promises(TODAY, tmp_path)}
    assert set(got) == {"Late promise", "Soon promise"}
    assert got["Late promise"]["overdue"] and got["Soon promise"]["days"] == 8


def test_open_prs_and_branches_without_one_are_listed():
    def api(path):
        if "/pulls" in path:
            return [{"number": 7, "title": "deps: bump x", "head": {"ref": "dependabot/x"}, "created_at": "2026-10-11T03:00:00Z",
                     "user": {"login": "dependabot[bot]"}, "html_url": "u"}]
        if "/branches" in path:
            return [{"name": "main"}, {"name": "dependabot/x"}, {"name": "lost-work"}, {"name": "merged-elsewhere"}]
        return {"ahead_by": 3 if "lost-work" in path else 0}
    items, note = bl.github_work(TODAY, "o/r", api)
    assert note == ""
    pr = [i for i in items if i["kind"] == "pr"][0]
    assert pr["overdue"] and "close with a reason" in pr["next"]
    assert [i["where"] for i in items if i["kind"] == "branch"] == ["lost-work"]


def test_an_unreachable_github_is_said_never_shown_as_nothing_waiting():
    def down(path):
        raise OSError("offline")
    items, note = bl.github_work(TODAY, "o/r", down)
    assert items == [] and "could not be asked" in note
    b = bl.build(TODAY, github=lambda t: ([], "GitHub could not be asked (OSError)"))
    assert "could not be asked" in bl.markdown(b)


def test_late_items_come_first_and_the_issue_body_has_one_box_each():
    b = bl.build(TODAY, github=lambda t: ([bl._item("pr", "#1 old", "u", -12, True), bl._item("pr", "#2 new", "u", -1, False)], ""))
    late = [i for i in b["items"] if i["overdue"]]
    assert b["items"][:len(late)] == late
    md = bl.markdown(b)
    assert md.count("- [ ] ") == len(b["items"]) and "**late** #1 old" in md


def test_the_real_queue_is_well_formed():
    q = json.loads((ROOT / "governance" / "queue.json").read_text())
    ids = [i["id"] for i in q["items"]]
    assert len(ids) == len(set(ids))
    for i in q["items"]:
        assert i["state"] in ("open", "waiting-owner", "done") and i["ask"] and i["next"], i["id"]
        assert i["state"] != "open" or i.get("due"), f"{i['id']}: an open ask needs a due date"
