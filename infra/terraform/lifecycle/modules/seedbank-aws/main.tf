# SEED BANK — the part of the estate that is NEVER put to sleep and costs almost nothing.
# Like a real seed vault it holds what is needed to regrow everything: an encryption key, an immutable
# (object-locked) backup bucket, the persistent data disk that survives hibernation, and a budget alarm.
variable "name" { type = string }
variable "alert_email" { type = string }
variable "monthly_budget_usd" { type = number }
variable "az" { type = string }
variable "data_volume_gb" { type = number }
variable "with_data_volume" { type = bool }
variable "object_lock_days" { type = number }

resource "aws_kms_key" "seed" {
  description             = "${var.name} seed-bank key (encrypts backups, state and the data disk)"
  enable_key_rotation     = true
  deletion_window_in_days = 30
}

resource "aws_kms_alias" "seed" {
  name          = "alias/${var.name}-seed"
  target_key_id = aws_kms_key.seed.key_id
}

resource "random_id" "suffix" { byte_length = 4 }

resource "aws_s3_bucket" "vault" {
  bucket              = "${var.name}-vault-${random_id.suffix.hex}"
  object_lock_enabled = true
  force_destroy       = false
}

resource "aws_s3_bucket_versioning" "vault" {
  bucket = aws_s3_bucket.vault.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "vault" {
  bucket = aws_s3_bucket.vault.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.seed.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "vault" {
  bucket                  = aws_s3_bucket.vault.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# WORM: backups and audit evidence cannot be altered or deleted for N days, even by an administrator.
resource "aws_s3_bucket_object_lock_configuration" "vault" {
  bucket = aws_s3_bucket.vault.id
  rule {
    default_retention {
      mode = "GOVERNANCE"
      days = var.object_lock_days
    }
  }
  depends_on = [aws_s3_bucket_versioning.vault]
}

resource "aws_s3_bucket_lifecycle_configuration" "vault" {
  bucket = aws_s3_bucket.vault.id
  rule {
    id     = "age-out-to-cheaper-storage"
    status = "Enabled"
    filter {}
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    noncurrent_version_expiration { noncurrent_days = 90 }
    abort_incomplete_multipart_upload { days_after_initiation = 7 }
  }
}

# The roots: the data disk that holds cluster state/volumes while the "leaves" (compute) are gone.
resource "aws_ebs_volume" "roots" {
  count             = var.with_data_volume ? 1 : 0
  availability_zone = var.az
  size              = var.data_volume_gb
  type              = "gp3"
  encrypted         = true
  kms_key_id        = aws_kms_key.seed.arn
  tags              = { Name = "${var.name}-roots", securax-organ = "roots" }
  lifecycle { prevent_destroy = true }
}

resource "aws_sns_topic" "alerts" {
  name              = "${var.name}-alerts"
  kms_master_key_id = aws_kms_key.seed.id
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Metabolism: a hard monthly budget with alerts at 50 / 80 / 100 % (forecast and actual).
resource "aws_budgets_budget" "monthly" {
  name         = "${var.name}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = toset([50, 80, 100])
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.alert_email]
    }
  }
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}

output "kms_key_arn" { value = aws_kms_key.seed.arn }
output "vault_bucket" { value = aws_s3_bucket.vault.id }
output "vault_bucket_arn" { value = aws_s3_bucket.vault.arn }
output "roots_volume_id" { value = try(aws_ebs_volume.roots[0].id, "") }
output "alerts_topic_arn" { value = aws_sns_topic.alerts.arn }
