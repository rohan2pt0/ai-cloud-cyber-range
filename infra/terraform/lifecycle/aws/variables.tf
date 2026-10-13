variable "name" {
  description = "Short prefix for every resource (letters, digits, hyphen)."
  type        = string
  default     = "securax"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.name))
    error_message = "name must be 3-21 chars: lowercase letters, digits, hyphen, starting with a letter."
  }
}

variable "stage" {
  description = "How far the estate is allowed to grow: seed (vault only) | tree (one k3s node) | canopy (managed Kubernetes) | forest (canopy + multi-tenant)."
  type        = string
  default     = "seed"
  validation {
    condition     = contains(["seed", "tree", "canopy", "forest"], var.stage)
    error_message = "stage must be seed, tree, canopy or forest."
  }
}

variable "awake" {
  description = "THE hibernation switch. false = compute is destroyed and only the seed bank (vault, keys, data disk, budget) remains; true = the stage's compute exists."
  type        = bool
  default     = false
}

variable "size" {
  description = "Vertical scale: small | medium | large (see locals.tiers)."
  type        = string
  default     = "small"
  validation {
    condition     = contains(["small", "medium", "large"], var.size)
    error_message = "size must be small, medium or large."
  }
}

variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "azs" {
  description = "Two availability zones in the region (AWS)."
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}

variable "alert_email" {
  description = "Where budget alerts go."
  type        = string
  default     = "you@example.com"
}

variable "monthly_budget_usd" {
  description = "Metabolic limit: alerts at 50/80/100 % of this. Set it BEFORE you wake anything."
  type        = number
  default     = 30
}

variable "object_lock_days" {
  description = "How long backups in the vault are immutable."
  type        = number
  default     = 30
}

variable "admin_cidrs" {
  description = "CIDRs allowed to reach the managed Kubernetes API publicly. Empty = private only (use SSM/tailscale)."
  type        = list(string)
  default     = []
}

variable "ami_id" {
  description = "AWS tree stage only: an Ubuntu 22.04/24.04 AMI id in the region (./securax grow looks it up for you)."
  type        = string
  default     = ""
}

variable "k3s_version" {
  type    = string
  default = "v1.37.1+k3s1"
}

variable "gitops_repo" {
  description = "The git repository Argo CD grows the platform from (this repo, by default)."
  type        = string
  default     = "https://github.com/rohan2pt0/ai-cloud-cyber-range.git"
}

variable "gitops_ref" {
  type    = string
  default = "main"
}

variable "argocd_version" {
  type    = string
  default = "v3.5.5"
}

variable "k8s_version" {
  description = "Managed Kubernetes version (EKS). Empty = let AWS choose its current default, which is always inside standard support (older versions are billed at a much higher 'extended support' rate)."
  type        = string
  default     = ""
}

variable "tailscale_auth_key" {
  description = "Optional: join the node to your private tailscale mesh (the mycelium) so no public port is ever needed."
  type        = string
  default     = ""
  sensitive   = true
}

variable "tenants" {
  description = "Forest stage: one entry per tenant. Each gets its own encryption key + object store (AWS)."
  type = map(object({
    retention_days = optional(number, 365)
  }))
  default = {}
  validation {
    condition     = alltrue([for k, _ in var.tenants : can(regex("^[a-z][a-z0-9]{1,15}$", k))])
    error_message = "tenant ids: 2-16 chars, lowercase letters and digits, starting with a letter."
  }
}

variable "offline" {
  description = "CI only: skip cloud credential checks so `terraform plan` can prove the dormancy logic without an account."
  type        = bool
  default     = false
}
