"""The site's second home: docs.yml has a dormant `mirror` job (doc 131). It does nothing until the owner adds the
Cloudflare secrets, and it pins the tool it fetches."""
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((ROOT / ".github" / "workflows" / "docs.yml").read_text("utf-8"))["jobs"].get("mirror")


def test_mirror_job_exists_and_is_bounded():
    assert SPEC, "docs.yml has no mirror job"
    assert SPEC["needs"] == "build"
    assert "refs/heads/main" in SPEC["if"] and "push" in SPEC["if"]
    assert SPEC.get("timeout-minutes")
    assert SPEC["permissions"] == {"contents": "read"}
    for step in SPEC["steps"]:
        assert "name" in step and isinstance(step["name"], str)


def test_mirror_does_nothing_without_the_secret():
    steps = SPEC["steps"]
    gate = steps[0]
    assert "No second host yet: add the CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID secrets" in gate["run"]
    assert "secrets" not in SPEC["if"]  # a secret is not allowed in a job-level if
    assert "secrets.CLOUDFLARE_API_TOKEN" in str(SPEC["env"])
    for step in steps[1:]:
        assert "steps." + gate["id"] + ".outputs" in step.get("if", ""), f"unguarded step: {step['name']}"


def test_mirror_deploys_pinned_wrangler_from_brand_env():
    deploy = [s for s in SPEC["steps"] if "wrangler" in s.get("run", "")]
    assert len(deploy) == 1
    run = deploy[0]["run"]
    assert re.search(r"wrangler@\d+\.\d+\.\d+ pages deploy website\b", run)
    assert '--project-name "$CF_PAGES_PROJECT"' in run and "--branch main" in run
    assert re.search(r"^CF_PAGES_PROJECT=\S+", (ROOT / "brand.env").read_text("utf-8"), re.M)
    assert any("website/build.sh" in s.get("run", "") for s in SPEC["steps"])
