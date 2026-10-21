"""A routine that messages a person runs on one machine of several (doc 91)."""
import json
import time

from routines.scheduler import run_due


def _jobs(tmp_path):
    p = tmp_path / "jobs.json"
    p.write_text(json.dumps([{"id": "nudge", "cron": "* * * * *", "command": ["true"], "once": True, "kind": "nudge"},
                             {"id": "guard", "cron": "* * * * *", "command": ["true"]}]))
    return p


def test_a_once_routine_is_skipped_when_another_machine_leads_and_the_rest_still_run(tmp_path):
    ran = []
    res = run_due(time.localtime(), jobs_path=_jobs(tmp_path), runner=lambda c: (ran.append(c) or (0, "")),
                  read_state=dict, write_state=lambda s: None, leader=lambda: False)
    assert len(ran) == 1 and any(r.get("skipped") for r in res) and all(r.get("exit_code", 1) == 0 for r in res)


def test_the_leader_runs_it(tmp_path):
    ran = []
    run_due(time.localtime(), jobs_path=_jobs(tmp_path), runner=lambda c: (ran.append(c) or (0, "")),
            read_state=dict, write_state=lambda s: None, leader=lambda: True)
    assert len(ran) == 2
