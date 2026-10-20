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
