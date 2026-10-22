"""Every GitHub workflow must parse. A YAML error does not fail a check: GitHub just runs nothing, so a pull request looks green
while its tests never ran (a step name with ': ' in it did exactly that). This test fails instead."""
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_every_workflow_parses_and_every_step_has_a_plain_name():
    files = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    assert files
    for f in files:
        doc = yaml.safe_load(f.read_text("utf-8"))
        assert isinstance(doc, dict) and isinstance(doc.get("jobs"), dict) and doc["jobs"], f.name
        for job, spec in doc["jobs"].items():
            for step in spec.get("steps", []):
                assert isinstance(step, dict), f"{f.name}:{job}: a step is not a mapping"
                assert "name" not in step or isinstance(step["name"], str), f"{f.name}:{job}: step name {step.get('name')!r}"


def _triggers(doc):
    on = doc.get(True, doc.get("on"))                      # PyYAML reads the bare key `on` as True
    return set(on) if isinstance(on, (dict, list)) else {on}


def test_a_new_push_never_cancels_a_run_it_should_not():
    """A newer push to a pull request may replace that PR's own older run (it is wasted work). It must never cancel a run on
    main, a nightly or a release: a cancelled nightly read as "main is not green" and could hold the laptop's update."""
    for f in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        doc = yaml.safe_load(f.read_text("utf-8"))
        trig, conc = _triggers(doc), doc.get("concurrency")
        cancel = str((conc or {}).get("cancel-in-progress", False)) if isinstance(conc, dict) else "False"
        if "pull_request" in trig and trig & {"push", "schedule"}:
            assert conc, f"{f.name}: runs on pull requests and on main/schedule but has no concurrency group"
            assert "pull_request.number" in str(conc.get("group")), f"{f.name}: the group must be per pull request"
            assert cancel != "True", f"{f.name}: cancel-in-progress: true would also cancel runs on main or the nightly"
        if f.name.startswith("release") or "schedule" in trig and "pull_request" not in trig:
            assert cancel in ("False", "false"), f"{f.name}: a release or scheduled run must never be cancelled"
        if "pull_request" in trig and "push" in trig:
            branches = (doc.get(True, doc.get("on")).get("push") or {}).get("branches", [])
            assert branches and "**" not in branches, f"{f.name}: push on every branch AND pull_request runs each change twice"
