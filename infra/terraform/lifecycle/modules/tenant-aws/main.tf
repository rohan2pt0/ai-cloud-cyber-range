# TENANT (phase 4, "fly") — one differentiated cell of the multi-tenant forest. Every tenant gets its own encryption
# key and its own object store, so its data is cryptographically isolated from every other tenant's. (Its Kubernetes
# namespace, network policy, quota and SSO realm are created from the same template by GitOps — see gitops/tenants.)
variable "name" { type = string }
variable "tenant" { type = string }
variable "retention_days" { type = number }

resource "aws_kms_key" "tenant" {
  description             = "${var.name} tenant ${var.tenant}"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  tags                    = { securax-tenant = var.tenant }
}

resource "aws_kms_alias" "tenant" {
  name          = "alias/${var.name}-tenant-${var.tenant}"
  target_key_id = aws_kms_key.tenant.key_id
}

resource "random_id" "suffix" { byte_length = 3 }

resource "aws_s3_bucket" "tenant" {
  bucket        = "${var.name}-t-${var.tenant}-${random_id.suffix.hex}"
  force_destroy = false
  tags          = { securax-tenant = var.tenant }
}

resource "aws_s3_bucket_versioning" "tenant" {
  bucket = aws_s3_bucket.tenant.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tenant" {
  bucket = aws_s3_bucket.tenant.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.tenant.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "tenant" {
  bucket                  = aws_s3_bucket.tenant.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "tenant" {
  bucket = aws_s3_bucket.tenant.id
  rule {
    id     = "retention"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration { noncurrent_days = var.retention_days }
  }
}

output "bucket" { value = aws_s3_bucket.tenant.id }
output "kms_key_arn" { value = aws_kms_key.tenant.arn }
