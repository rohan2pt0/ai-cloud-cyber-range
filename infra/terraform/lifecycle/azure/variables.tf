variable "name" {
  type    = string
  default = "securax"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.name))
    error_message = "name must be 3-21 chars: lowercase letters, digits, hyphen, starting with a letter."
  }
}

variable "stage" {
  description = "seed (vault only) | canopy (AKS) | forest (canopy; tenants are isolated by GitOps namespaces)."
  type        = string
  default     = "seed"
  validation {
    condition     = contains(["seed", "canopy", "forest"], var.stage)
    error_message = "stage must be seed, canopy or forest on Azure (the single-node tree stage is AWS-only)."
  }
}

variable "awake" {
  description = "THE hibernation switch: false = only the seed bank (storage account) exists; true = the cluster exists."
  type        = bool
  default     = false
}

variable "azure_subscription_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.azure_subscription_id))
    error_message = "azure_subscription_id must be a subscription GUID."
  }
}

variable "region" {
  type    = string
  default = "centralindia"
}

variable "size" {
  type    = string
  default = "small"
  validation {
    condition     = contains(["small", "medium", "large"], var.size)
    error_message = "size must be small, medium or large."
  }
}

variable "admin_cidrs" {
  type    = list(string)
  default = []
}
