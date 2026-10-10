# The "lab" environment composes the three cloud slices. Each is individually
# toggleable so you only spin up (and pay for) the cloud you are drilling on today.
# Default: everything free-tier, enable_paid = false, hard budget = 2,500 INR / ~$30.
terraform {
  required_version = ">= 1.6"
  # Remote state is recommended; for a solo laptop lab local state is fine. To use a
  # free backend, uncomment and point at a GCS/S3 bucket created by the relevant module.
  # backend "gcs" { bucket = "range-tfstate", prefix = "lab" }
}

variable "alert_email" { type = string }
variable "enable_aws" {
  type    = bool
  default = false
}
variable "enable_gcp" {
  type    = bool
  default = false
}
variable "enable_azure" {
  type    = bool
  default = false
}
variable "enable_paid" {
  type    = bool
  default = false
}

# AWS
variable "aws_region" {
  type    = string
  default = "ap-south-1"
}
# GCP
variable "gcp_project_id" {
  type    = string
  default = ""
}
variable "gcp_billing_account" {
  type    = string
  default = ""
}
# Azure
variable "azure_subscription_id" {
  type    = string
  default = ""
}

provider "aws" { region = var.aws_region }
provider "google" {
  project = var.gcp_project_id != "" ? var.gcp_project_id : null
  region  = "asia-south1"
}

module "aws" {
  source      = "../../modules/aws-ai-security"
  count       = var.enable_aws ? 1 : 0
  region      = var.aws_region
  alert_email = var.alert_email
  enable_paid = var.enable_paid
}

module "gcp" {
  source          = "../../modules/gcp-ai-security"
  count           = var.enable_gcp ? 1 : 0
  project_id      = var.gcp_project_id
  billing_account = var.gcp_billing_account
  enable_paid     = var.enable_paid
}

module "azure" {
  source          = "../../modules/azure-ai-security"
  count           = var.enable_azure ? 1 : 0
  subscription_id = var.azure_subscription_id
  alert_email     = var.alert_email
  enable_paid     = var.enable_paid
}

output "aws" { value = var.enable_aws ? module.aws[0] : null }
output "gcp_model_armor" { value = var.enable_gcp ? module.gcp[0].model_armor_template : null }
output "azure_content_safety" { value = var.enable_azure ? module.azure[0].content_safety_endpoint : null }
