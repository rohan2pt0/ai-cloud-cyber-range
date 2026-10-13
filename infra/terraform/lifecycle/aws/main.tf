# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# THE GENOME. One definition of the whole estate, from a dormant seed to a multi-tenant forest.
#
#   awake = false  →  ONLY the seed bank exists (vault, key, data disk, budget alarm). Compute count = 0. Near-zero cost.
#   awake = true   →  the compute of the chosen `stage` germinates from the same code, then GitOps (gitops/) grows the rest.
#
# Nothing here is ever "rebuilt": hibernate and wake are the same code with one boolean flipped. State lives in the seed
# bank, so waking restores what the estate knew.
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

locals {
  # Vertical scale tiers. Change `size` (not the code) to move up or down.
  tiers = {
    small  = { tree_instance = "t3.large", roots_gb = 100 }
    medium = { tree_instance = "m6i.xlarge", roots_gb = 200 }
    large  = { tree_instance = "m6i.2xlarge", roots_gb = 500 }
  }
  tier = local.tiers[var.size]

  want_tree   = var.stage == "tree"
  want_canopy = contains(["canopy", "forest"], var.stage)
  want_forest = var.stage == "forest"

  # The dormancy switch, applied to every piece of compute.
  tree_awake   = var.awake && local.want_tree
  canopy_awake = var.awake && local.want_canopy

  name = var.name
}

# Guard rails: fail at plan time with a plain message instead of half-creating something.
resource "terraform_data" "guards" {
  lifecycle {
    precondition {
      condition     = !local.tree_awake || var.ami_id != ""
      error_message = "Waking the AWS tree stage needs ami_id (an Ubuntu AMI in ${var.region}). ./securax grow tree looks one up for you."
    }
    precondition {
      condition     = length(var.azs) >= 2
      error_message = "azs needs at least two availability zones."
    }
  }
}

# ── AWS ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
module "seedbank_aws" {
  source             = "../modules/seedbank-aws"
  name               = local.name
  alert_email        = var.alert_email
  monthly_budget_usd = var.monthly_budget_usd
  az                 = var.azs[0]
  data_volume_gb     = local.tier.roots_gb
  with_data_volume   = local.want_tree
  object_lock_days   = var.object_lock_days
}

module "network_aws" {
  source   = "../modules/network-aws"
  count    = (local.want_tree || local.want_canopy) ? 1 : 0
  name     = local.name
  azs      = var.azs
  vpc_cidr = "10.10.0.0/16"
  with_nat = local.canopy_awake # the one network piece that costs money exists only while awake
}

module "tree_aws" {
  source             = "../modules/tree-aws"
  count              = local.tree_awake ? 1 : 0
  name               = local.name
  subnet_id          = module.network_aws[0].public_subnet_ids[0]
  vpc_id             = module.network_aws[0].vpc_id
  instance_type      = local.tier.tree_instance
  ami_id             = var.ami_id
  roots_volume_id    = module.seedbank_aws.roots_volume_id
  kms_key_arn        = module.seedbank_aws.kms_key_arn
  vault_bucket_arn   = module.seedbank_aws.vault_bucket_arn
  k3s_version        = var.k3s_version
  tailscale_auth_key = var.tailscale_auth_key
  gitops_repo        = var.gitops_repo
  gitops_ref         = var.gitops_ref
  argocd_version     = var.argocd_version
}

module "canopy_aws" {
  source             = "../modules/canopy-aws"
  count              = local.canopy_awake ? 1 : 0
  name               = local.name
  k8s_version        = var.k8s_version
  private_subnet_ids = module.network_aws[0].private_subnet_ids
  public_subnet_ids  = module.network_aws[0].public_subnet_ids
  kms_key_arn        = module.seedbank_aws.kms_key_arn
  admin_cidrs        = var.admin_cidrs
  node_pools         = ["general-purpose", "system"]
  vault_bucket_arn   = module.seedbank_aws.vault_bucket_arn
}

# Tenants are DATA (keys + object stores): they persist through hibernation like the rest of the seed bank.
module "tenant_aws" {
  source         = "../modules/tenant-aws"
  for_each       = local.want_forest ? var.tenants : {}
  name           = local.name
  tenant         = each.key
  retention_days = each.value.retention_days
}

