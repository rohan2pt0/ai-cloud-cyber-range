# GCP slice: budget kill-switch, Model Armor (the managed LLM guardrail the gateway
# calls), a Cloud Run service for the gateway, and Artifact Registry. Vertex/Gemini
# free tier + Cloud Run free tier keep this near-zero. Budget alerts can trigger a
# Pub/Sub -> Cloud Function that disables billing (the real "stop the bleeding" control).
terraform {
  required_version = ">= 1.6"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 6.12" }
  }
}

variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "asia-south1"
} # Mumbai
variable "billing_account" { type = string }
variable "budget_usd" {
  type    = number
  default = 30
}
variable "enable_paid" {
  type    = bool
  default = false
}

locals {
  services = [
    "run.googleapis.com", "artifactregistry.googleapis.com", "modelarmor.googleapis.com",
    "aiplatform.googleapis.com", "cloudbilling.googleapis.com", "billingbudgets.googleapis.com",
    "securitycenter.googleapis.com", "logging.googleapis.com", "pubsub.googleapis.com",
  ]
}

resource "google_project_service" "apis" {
  for_each                   = toset(local.services)
  project                    = var.project_id
  service                    = each.value
  disable_dependent_services = false
  disable_on_destroy         = false
}

# --- Budget kill-switch: alerts at 50/90/100% and publishes to a Pub/Sub topic that a
#     Cloud Function (see docs/cost-controls.md) uses to detach billing automatically ---
resource "google_pubsub_topic" "budget" {
  name    = "range-budget-alerts"
  project = var.project_id
}

resource "google_billing_budget" "monthly" {
  billing_account = var.billing_account
  display_name    = "ai-range-monthly-ceiling"
  budget_filter { projects = ["projects/${var.project_id}"] }
  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.budget_usd)
    }
  }
  dynamic "threshold_rules" {
    for_each = [0.5, 0.9, 1.0]
    content { threshold_percent = threshold_rules.value }
  }
  all_updates_rule {
    pubsub_topic                   = google_pubsub_topic.budget.id
    disable_default_iam_recipients = false
  }
}

# --- Model Armor template: the managed prompt-injection / DLP / jailbreak filter ------
resource "google_model_armor_template" "range" {
  provider    = google
  location    = var.region
  template_id = "range-guardrail"
  project     = var.project_id
  filter_config {
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = "LOW_AND_ABOVE"
    }
    malicious_uri_filter_settings { filter_enforcement = "ENABLED" }
    sdp_settings {
      basic_config { filter_enforcement = "ENABLED" } # sensitive-data protection
    }
  }
  depends_on = [google_project_service.apis]
}

# --- Artifact Registry for the gateway image (free tier: 0.5 GB) ----------------------
resource "google_artifact_registry_repository" "gateway" {
  location      = var.region
  repository_id = "ai-range"
  format        = "DOCKER"
  project       = var.project_id
  depends_on    = [google_project_service.apis]
}

# --- Cloud Run gateway (scales to zero => free when idle) -----------------------------
resource "google_service_account" "gateway" {
  account_id   = "range-gateway"
  display_name = "AI Range gateway (least privilege)"
  project      = var.project_id
}
resource "google_project_iam_member" "gateway_modelarmor" {
  project = var.project_id
  role    = "roles/modelarmor.user"
  member  = "serviceAccount:${google_service_account.gateway.email}"
}

resource "google_cloud_run_v2_service" "gateway" {
  count    = var.enable_paid ? 1 : 0 # keep off by default; flip on for the demo
  name     = "llm-gateway"
  location = var.region
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_ALL"
  template {
    service_account = google_service_account.gateway.email
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/ai-range/llm-gateway:latest"
      resources { limits = { cpu = "1", memory = "512Mi" } }
      env {
        name  = "MODEL_ARMOR_TEMPLATE"
        value = "projects/${var.project_id}/locations/${var.region}/templates/${google_model_armor_template.range.template_id}"
      }
      env {
        name  = "GUARDRAIL_MODE"
        value = "enforce"
      }
      env {
        name  = "FAIL_MODE"
        value = "closed"
      }
    }
  }
}

output "model_armor_template" { value = google_model_armor_template.range.id }
output "artifact_registry" { value = google_artifact_registry_repository.gateway.name }
output "budget_topic" { value = google_pubsub_topic.budget.id }
