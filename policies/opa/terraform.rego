# Conftest/OPA policies that fail a build if the Terraform *plan* violates the range's
# security baseline. Run in CI before any apply:
#   terraform plan -out tf.plan && terraform show -json tf.plan > plan.json
#   conftest test --policy policies/opa plan.json
package terraform.security

import rego.v1

resources contains r if {
	some rc in input.resource_changes
	r := rc
}

# A cost budget MUST exist - no range without a spend ceiling (protects 2,500 INR cap).
deny contains msg if {
	not has_budget
	msg := "No cost budget resource in plan: a budget/kill-switch is mandatory for the range."
}

has_budget if {
	some r in resources
	r.type in {"aws_budgets_budget", "google_billing_budget", "azurerm_consumption_budget_subscription"}
}

# No public S3 buckets.
deny contains msg if {
	some r in resources
	r.type == "aws_s3_bucket_public_access_block"
	some f in ["block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets"]
	r.change.after[f] == false
	msg := sprintf("S3 bucket %s has public access not fully blocked (%s=false).", [r.address, f])
}

# ECR / registries must scan on push (supply chain).
deny contains msg if {
	some r in resources
	r.type == "aws_ecr_repository"
	r.change.after.image_scanning_configuration[_].scan_on_push == false
	msg := sprintf("ECR repo %s does not scan on push.", [r.address])
}

# Model Armor / Content Safety guardrail filters must be ENABLED, not just present.
deny contains msg if {
	some r in resources
	r.type == "google_model_armor_template"
	r.change.after.filter_config[_].pi_and_jailbreak_filter_settings[_].filter_enforcement != "ENABLED"
	msg := sprintf("Model Armor template %s has prompt-injection filter disabled.", [r.address])
}

# IAM roles for CI must be federated (OIDC), never backed by long-lived access keys.
deny contains msg if {
	some r in resources
	r.type == "aws_iam_access_key"
	msg := sprintf("Long-lived IAM access key %s is forbidden; use GitHub OIDC federation.", [r.address])
}

# Warn (not block) when a paid tier is being turned on, so it is a conscious choice.
warn contains msg if {
	some r in resources
	r.type in {"aws_guardduty_detector", "azurerm_security_center_subscription_pricing", "google_cloud_run_v2_service"}
	msg := sprintf("%s is a billable resource - confirm it fits the monthly budget.", [r.address])
}
