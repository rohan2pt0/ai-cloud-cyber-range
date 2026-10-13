#!/usr/bin/env python3
"""Prove the hibernation logic WITHOUT a cloud account.

For each scenario this runs `terraform plan` offline (fake credentials, no API calls) and inspects the planned
resources: a dormant estate must plan ONLY the seed bank; an awake one must plan the stage's compute — and nothing
from a bigger stage. Also checks that the guard rails refuse nonsense with a readable message.

  python3 prove.py            run everything (needs `terraform`; first run downloads providers)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = {**os.environ, "AWS_ACCESS_KEY_ID": "offline", "AWS_SECRET_ACCESS_KEY": "offline", "AWS_REGION": "ap-south-1",
       "ARM_CLIENT_ID": "00000000-0000-0000-0000-000000000000",
       "ARM_CLIENT_SECRET": "offline", "ARM_TENANT_ID": "00000000-0000-0000-0000-000000000000",
       "GOOGLE_OAUTH_ACCESS_TOKEN": "offline", "TF_IN_AUTOMATION": "1", "TF_INPUT": "0"}
TENANTS = '{"acme":{},"globex":{"retention_days":730}}'
AWS_BASE = ["-var", "offline=true", "-var", "ami_id=ami-0123456789abcdef0"]
GCP_BASE = ["-var", "gcp_project_id=proj-offline"]


ENV["TF_PLUGIN_CACHE_DIR"] = os.environ.get("TF_PLUGIN_CACHE_DIR", os.path.expanduser("~/.terraform.d/plugin-cache"))
os.makedirs(ENV["TF_PLUGIN_CACHE_DIR"], exist_ok=True)


def tf(*args: str, cwd: str = HERE) -> tuple[int, str]:
    p = subprocess.run(["terraform", *args], cwd=cwd, env=ENV, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


LAST_PLAN: list[dict] = []        # resource_changes of the most recent plan (for the security-invariant checks)


def planned(root: str, vars_: dict[str, str]) -> dict[str, int]:
    """Planned CREATE counts per resource type for the given variables."""
    with tempfile.TemporaryDirectory() as td:
        plan = os.path.join(td, "plan")
        a = ["plan", "-input=false", "-lock=false", "-refresh=false", "-out=" + plan, *(AWS_BASE if root == "aws" else GCP_BASE)]
        for k, v in vars_.items():
            a += ["-var", f"{k}={v}"]
        rc, out = tf(*a, cwd=os.path.join(HERE, root))
        if rc != 0:
            raise RuntimeError("plan failed:\n" + out[-1500:])
        rc, js = tf("show", "-json", plan, cwd=os.path.join(HERE, root))
        counts: dict[str, int] = {}
        LAST_PLAN[:] = json.loads(js).get("resource_changes", [])
        for rc_ in LAST_PLAN:
            if "create" in rc_["change"]["actions"]:
                counts[rc_["type"]] = counts.get(rc_["type"], 0) + 1
        return counts


COMPUTE = ["aws_instance", "aws_eks_cluster", "aws_nat_gateway", "google_container_cluster", "azurerm_kubernetes_cluster"]
SCENARIOS = [
    # (root, title, vars, must_have, must_not_have)
    ("aws", "aws seed (dormant)", dict(stage="seed", awake="false"),
     ["aws_kms_key", "aws_s3_bucket", "aws_s3_bucket_object_lock_configuration", "aws_budgets_budget"], COMPUTE + ["aws_vpc", "aws_ebs_volume"]),
    ("aws", "aws tree, asleep", dict(stage="tree", awake="false"),
     ["aws_kms_key", "aws_ebs_volume", "aws_vpc"], COMPUTE),
    ("aws", "aws tree, awake", dict(stage="tree", awake="true"),
     ["aws_instance", "aws_volume_attachment", "aws_ebs_volume", "aws_vpc"], ["aws_eks_cluster", "aws_nat_gateway"]),
    ("aws", "aws canopy, asleep", dict(stage="canopy", awake="false"),
     ["aws_vpc", "aws_kms_key"], COMPUTE + ["aws_ebs_volume"]),
    ("aws", "aws canopy, awake", dict(stage="canopy", awake="true"),
     ["aws_eks_cluster", "aws_nat_gateway", "aws_vpc"], ["aws_instance"]),
    ("aws", "aws forest, asleep (tenant data persists)", dict(stage="forest", awake="false", tenants=TENANTS),
     ["aws_kms_key", "aws_s3_bucket"], COMPUTE),
    ("aws", "aws forest, awake", dict(stage="forest", awake="true", tenants=TENANTS),
     ["aws_eks_cluster", "aws_nat_gateway", "aws_s3_bucket"], ["aws_instance"]),
    ("gcp", "gcp canopy, asleep", dict(stage="canopy", awake="false", region="asia-south1"),
     ["google_storage_bucket"], COMPUTE),
    ("gcp", "gcp canopy, awake", dict(stage="canopy", awake="true", region="asia-south1"),
     ["google_container_cluster", "google_storage_bucket"], ["aws_eks_cluster", "azurerm_kubernetes_cluster"]),
        ]
EXTRA = {"aws forest, asleep (tenant data persists)": ("aws_s3_bucket", 3), "aws forest, awake": ("aws_s3_bucket", 3)}   # vault + 2 tenants

REFUSALS = [
    # (root, title, vars, needle)
    ("aws", "tree awake without an AMI", dict(stage="tree", awake="true", ami_id=""), "needs ami_id"),
    ("aws", "bad tenant id", dict(stage="forest", awake="false", tenants='{"Bad_Name":{}}'), "tenant ids"),
    ("aws", "unknown stage", dict(stage="jungle", awake="false"), "stage must be"),
    ("gcp", "tree on gcp", dict(stage="tree", awake="false"), "AWS-only"),
    ("gcp", "no project", dict(stage="canopy", awake="false", gcp_project_id=""), "gcp_project_id is required"),
]


def security_invariants(changes: list[dict]) -> list[str]:
    """Policy-as-code over the PLAN (what would be created): the things that must hold in every awake estate."""
    bad: list[str] = []
    by: dict[str, list[dict]] = {}
    for c in changes:
        if "create" in c["change"]["actions"]:
            by.setdefault(c["type"], []).append(c["change"]["after"] or {})
    if len(by.get("aws_s3_bucket", [])) != len(by.get("aws_s3_bucket_public_access_block", [])):
        bad.append("every S3 bucket needs a public-access block")
    for b in by.get("aws_s3_bucket_public_access_block", []):
        if not all(b.get(k) for k in ("block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets")):
            bad.append("public-access block must enable all four protections")
    for v in by.get("aws_ebs_volume", []):
        if v.get("encrypted") is not True:
            bad.append("EBS volumes must be encrypted")
    for i in by.get("aws_instance", []):
        if (i.get("metadata_options") or [{}])[0].get("http_tokens") != "required":
            bad.append("EC2 must require IMDSv2")
        if not (i.get("root_block_device") or [{}])[0].get("encrypted"):
            bad.append("EC2 root volume must be encrypted")
    for sg in by.get("aws_security_group", []):
        if sg.get("ingress"):
            bad.append("security groups must have no inbound rules (access is via SSM/tailscale)")
    for k in by.get("aws_kms_key", []):
        if k.get("enable_key_rotation") is not True:
            bad.append("KMS keys must rotate")
    for c in by.get("aws_eks_cluster", []):
        vpc = (c.get("vpc_config") or [{}])[0]
        if vpc.get("endpoint_public_access") and not vpc.get("public_access_cidrs"):
            bad.append("a public EKS endpoint must be restricted to admin_cidrs")
        if not c.get("encryption_config"):
            bad.append("EKS secrets must be KMS-encrypted")
        if (c.get("upgrade_policy") or [{}])[0].get("support_type") != "STANDARD":
            bad.append("EKS must stay on STANDARD support (extended support is billed at several times the rate)")
    return bad


def main() -> int:
    bad = 0
    for root in ("aws", "gcp", "azure"):
        rc, out = tf("init", "-backend=false", "-input=false", cwd=os.path.join(HERE, root))
        if rc != 0:
            print(out[-1500:])
            return 2
        rc, out = tf("validate", cwd=os.path.join(HERE, root))
        print(f"  {'✓' if rc == 0 else '✗'} {root}: terraform validate" + ("" if rc == 0 else "\n" + out[-800:]))
        bad += 0 if rc == 0 else 1
    print("  · azure: plan-proof skipped (the azurerm provider needs a real login even to plan); validated only")
    for root, title, vars_, have, havent in SCENARIOS:
        try:
            c = planned(root, vars_)
        except RuntimeError as e:
            print(f"  ✗ {title}: {e}")
            bad += 1
            continue
        sec = security_invariants(LAST_PLAN) if root == "aws" else []
        if sec:
            bad += 1
            print(f"  ✗ {title}: security invariants violated: {sorted(set(sec))}")
        miss = [t for t in have if c.get(t, 0) == 0]
        extra = [t for t in havent if c.get(t, 0) > 0]
        want = EXTRA.get(title)
        wrong_n = bool(want and c.get(want[0], 0) != want[1])
        ok = not (miss or extra or wrong_n)
        bad += 0 if ok else 1
        print(f"  {'✓' if ok else '✗'} {title}" + ("" if ok else f"  missing={miss} unexpected={extra}" + (f" {want[0]}={c.get(want[0], 0)} want {want[1]}" if wrong_n else "")))
    for root, title, vars_, needle in REFUSALS:
        a = ["plan", "-input=false", "-lock=false", "-refresh=false", *(AWS_BASE if root == "aws" else GCP_BASE)]
        a += [x for k, v in vars_.items() for x in ("-var", f"{k}={v}")]       # later -var wins over the base defaults
        rc, out = tf(*a, cwd=os.path.join(HERE, root))
        ok = rc != 0 and needle in " ".join(out.split())
        bad += 0 if ok else 1
        print(f"  {'✓' if ok else '✗'} refuses: {title}" + ("" if ok else f"  (rc={rc}) {out[-300:]}"))
    print("PROVED" if not bad else f"{bad} scenario(s) FAILED")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
