output "state" {
  description = "What exists right now, in plain words."
  value = {
    stage = var.stage
    awake = var.awake
    mode  = var.awake ? "awake: ${var.stage} compute exists" : "dormant: only the seed bank (and, for tree, its data disk) exists"
  }
}

output "connect" {
  description = "How to reach the awake estate (empty while dormant)."
  value       = try(module.canopy_aws[0].connect, module.tree_aws[0].connect, "")
}

output "vault" {
  description = "The seed bank's object store (backups, state, evidence)."
  value       = module.seedbank_aws.vault_bucket
}

output "tenants" {
  value = { for k, m in module.tenant_aws : k => { bucket = m.bucket, kms_key_arn = m.kms_key_arn } }
}

output "region" { value = var.region }

output "velero_role_arn" {
  description = "Pod-identity role Velero uses to reach the vault (empty while dormant)."
  value       = try(module.canopy_aws[0].velero_role_arn, "")
}
