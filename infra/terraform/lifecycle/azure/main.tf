# Azure genome: awake=false → only the seed bank (a versioned storage account); awake=true → AKS germinates.
locals {
  canopy_awake = var.awake && contains(["canopy", "forest"], var.stage)
  tiers = {
    small  = { system = "Standard_D2s_v5", user = "Standard_D4s_v5", max = 3 }
    medium = { system = "Standard_D2s_v5", user = "Standard_D8s_v5", max = 6 }
    large  = { system = "Standard_D4s_v5", user = "Standard_D16s_v5", max = 12 }
  }
  tier = local.tiers[var.size]
}

module "seedbank" {
  source   = "../modules/seedbank-azure"
  name     = var.name
  location = var.region
}

module "canopy" {
  source         = "../modules/canopy-azure"
  count          = local.canopy_awake ? 1 : 0
  name           = var.name
  location       = var.region
  admin_cidrs    = var.admin_cidrs
  system_vm_size = local.tier.system
  user_vm_size   = local.tier.user
  user_max_nodes = local.tier.max
}

output "state" {
  value = {
    stage = var.stage
    awake = var.awake
    mode  = var.awake ? "awake: ${var.stage} compute exists" : "dormant: only the seed bank exists"
  }
}

output "connect" { value = try(module.canopy[0].connect, "") }
output "vault" { value = module.seedbank.vault_storage_account }
