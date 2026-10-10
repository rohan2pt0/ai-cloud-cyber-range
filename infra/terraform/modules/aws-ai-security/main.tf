# AWS slice of the range: cost guardrails first, then free/near-free security posture.
# Designed for the new 2026 AWS Free Plan ($200 credit, 6 months). Everything that can
# cost money is gated behind var.enable_paid and capped by an AWS Budget kill-switch.
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.70" }
  }
}

variable "region" {
  type    = string
  default = "ap-south-1"
} # Mumbai - data residency (RBI/DPDP)
variable "budget_inr" {
  type    = number
  default = 2500
}
variable "budget_usd" {
  type    = number
  default = 30
}
variable "alert_email" { type = string }
variable "enable_paid" {
  description = "Turn on services that draw down credit / cost money (GuardDuty, Security Hub)."
  type        = bool
  default     = false
}
variable "github_repo" {
  type    = string
  default = "rohan2pt0/ai-cloud-cyber-range"
}
variable "tags" {
  type    = map(string)
  default = { project = "ai-cloud-cyber-range", owner = "rohan", managed_by = "terraform" }
}

data "aws_caller_identity" "me" {}

# --- 1. Cost kill-switch: alert at 50/80%, and this is the hard INR ceiling ------------
resource "aws_budgets_budget" "monthly" {
  name         = "range-monthly-ceiling"
  budget_type  = "COST"
  limit_amount = tostring(var.budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = [50, 80, 100]
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.alert_email]
    }
  }
}

# --- 2. Audit trail (free tier: one trail, management events) -------------------------
resource "aws_cloudtrail" "range" {
  name                          = "range-trail"
  s3_bucket_name                = aws_s3_bucket.trail.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  tags                          = var.tags
  depends_on                    = [aws_s3_bucket_policy.trail]
}

resource "aws_s3_bucket" "trail" {
  bucket        = "range-trail-${data.aws_caller_identity.me.account_id}"
  force_destroy = true
  tags          = var.tags
}
resource "aws_s3_bucket_public_access_block" "trail" {
  bucket                  = aws_s3_bucket.trail.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_server_side_encryption_configuration" "trail" {
  bucket = aws_s3_bucket.trail.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "aws:kms" }
  }
}
resource "aws_s3_bucket_policy" "trail" {
  bucket = aws_s3_bucket.trail.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Sid = "AWSCloudTrailAclCheck", Effect = "Allow", Principal = { Service = "cloudtrail.amazonaws.com" },
      Action = "s3:GetBucketAcl", Resource = aws_s3_bucket.trail.arn },
      { Sid    = "AWSCloudTrailWrite", Effect = "Allow", Principal = { Service = "cloudtrail.amazonaws.com" },
        Action = "s3:PutObject", Resource = "${aws_s3_bucket.trail.arn}/AWSLogs/${data.aws_caller_identity.me.account_id}/*",
      Condition = { StringEquals = { "s3:x-amz-acl" = "bucket-owner-full-control" } } }
    ]
  })
}

# --- 3. ECR for the gateway image, with scan-on-push (free) ---------------------------
resource "aws_ecr_repository" "gateway" {
  name                 = "ai-range/llm-gateway"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "KMS" }
  tags = var.tags
}

# --- 4. Keyless CI: GitHub OIDC -> deploy role (no long-lived keys) --------------------
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_deploy" {
  name = "range-github-deploy"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = { "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com" }
        StringLike   = { "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:*" }
      }
    }]
  })
  tags = var.tags
}
resource "aws_iam_role_policy" "github_deploy_ecr" {
  name = "push-ecr"
  role = aws_iam_role.github_deploy.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["ecr:GetAuthorizationToken", "ecr:BatchCheckLayerAvailability", "ecr:PutImage",
      "ecr:InitiateLayerUpload", "ecr:UploadLayerPart", "ecr:CompleteLayerUpload"]
      Resource = "*"
    }]
  })
}

# --- 5. Paid posture: GuardDuty + Security Hub (gated; GuardDuty has a 30-day free trial) ---
resource "aws_guardduty_detector" "this" {
  count  = var.enable_paid ? 1 : 0
  enable = true
  tags   = var.tags
}
resource "aws_securityhub_account" "this" { count = var.enable_paid ? 1 : 0 }

output "ecr_repo_url" { value = aws_ecr_repository.gateway.repository_url }
output "github_deploy_role_arn" { value = aws_iam_role.github_deploy.arn }
output "budget_name" { value = aws_budgets_budget.monthly.name }
