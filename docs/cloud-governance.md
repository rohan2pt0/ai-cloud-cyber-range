# Cloud Governance Guardrails (preventive, org-wide)

The Terraform modules deploy *resource-level* controls. This note covers the *org-level*
preventive guardrails a Cloud AI Security lead owns ("AWS Organizations, Control Tower,
Azure Policy, Security Command Center"). They are documented as policy-as-code patterns;
enable them once you have an Organization / Management Group (free to define, so they stay
inside the ₹2,500 budget).

## AWS — Service Control Policies (Organizations / Control Tower)
Deny-by-default rails that even an account admin cannot override:
```json
// Deny any region except Mumbai + deny disabling CloudTrail/GuardDuty (data residency + audit)
{ "Version": "2012-10-17", "Statement": [
  { "Sid": "RegionLock", "Effect": "Deny", "NotAction": ["iam:*","organizations:*","sts:*"],
    "Resource": "*", "Condition": { "StringNotEquals": { "aws:RequestedRegion": ["ap-south-1"] } } },
  { "Sid": "ProtectAudit", "Effect": "Deny",
    "Action": ["cloudtrail:StopLogging","guardduty:DeleteDetector"], "Resource": "*" },
  { "Sid": "NoRootKeys", "Effect": "Deny", "Action": "iam:CreateAccessKey",
    "Resource": "*", "Condition": { "StringEquals": { "aws:username": "root" } } }
]}
```
Attach via `aws_organizations_policy` + `aws_organizations_policy_attachment`.

## Azure — Azure Policy (Management Group scope)
```jsonc
// Allowed locations + require encryption; audit/deny effect
{ "policyRule": { "if": { "not": { "field": "location",
     "in": ["centralindia","southindia"] } }, "then": { "effect": "deny" } } }
```
Assign built-ins: *Allowed locations*, *Defender for Cloud ON*, *Storage requires HTTPS*,
*Cognitive Services disables public network access*. Deploy via `azurerm_management_group_policy_assignment`.

## GCP — Organization Policy Constraints
```
constraints/gcp.resourceLocations        -> in:asia-south1-locations     (data residency)
constraints/iam.disableServiceAccountKeyCreation -> true                 (no long-lived keys)
constraints/compute.vmExternalIpAccess   -> deny all                     (no public IPs)
constraints/storage.publicAccessPrevention -> enforced
```
Deploy via `google_org_policy_policy`.

## Why this matters (and the no-SPOF angle)
These are **preventive** controls (they stop misconfiguration before it exists), complementing
the **detective** controls (CSPM/Defender/SCC findings → AI-SOC) and the **responsive** ones
(budgets kill-switch, IR playbooks). Preventive + detective + responsive on three independent
clouds means no single guardrail — and no single cloud — is a single point of failure. Maps to
NIST CSF (PROTECT/DETECT/RESPOND) and SAIF "strong security foundations".
