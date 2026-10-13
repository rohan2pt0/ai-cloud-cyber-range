# GCP genome: awake=false → only the seed bank (a retention-locked bucket); awake=true → GKE Autopilot germinates.
locals {
  canopy_awake = var.awake && contains(["canopy", "forest"], var.stage)
}

module "seedbank" {
  source           = "../modules/seedbank-gcp"
  name             = var.name
  project_id       = var.gcp_project_id
  region           = var.region
  object_lock_days = var.object_lock_days
}

module "canopy" {
  source      = "../modules/canopy-gcp"
  count       = local.canopy_awake ? 1 : 0
  name        = var.name
  project_id  = var.gcp_project_id
  region      = var.region
  admin_cidrs = var.admin_cidrs
}

output "state" {
  value = {
    stage = var.stage
    awake = var.awake
    mode  = var.awake ? "awake: ${var.stage} compute exists" : "dormant: only the seed bank exists"
  }
}

output "connect" { value = try(module.canopy[0].connect, "") }
output "vault" { value = module.seedbank.vault_bucket }
