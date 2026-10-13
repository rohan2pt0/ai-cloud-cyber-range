# SEED BANK (GCP) — an always-present, near-free vault: a versioned, retention-locked bucket for backups and state.
variable "name" { type = string }
variable "project_id" { type = string }
variable "region" { type = string }
variable "object_lock_days" { type = number }

resource "random_id" "suffix" { byte_length = 4 }

resource "google_storage_bucket" "vault" {
  name                        = "${var.name}-vault-${random_id.suffix.hex}"
  project                     = var.project_id
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  versioning { enabled = true }

  retention_policy {
    retention_period = var.object_lock_days * 86400
  }

  lifecycle_rule {
    condition { age = 30 }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

output "vault_bucket" { value = google_storage_bucket.vault.name }
