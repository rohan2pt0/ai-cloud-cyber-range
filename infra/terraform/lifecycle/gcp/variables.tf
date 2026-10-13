variable "name" {
  type    = string
  default = "securax"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.name))
    error_message = "name must be 3-21 chars: lowercase letters, digits, hyphen, starting with a letter."
  }
}

variable "stage" {
  description = "seed (vault only) | canopy (GKE Autopilot) | forest (canopy; tenants are isolated by GitOps namespaces)."
  type        = string
  default     = "seed"
  validation {
    condition     = contains(["seed", "canopy", "forest"], var.stage)
    error_message = "stage must be seed, canopy or forest on GCP (the single-node tree stage is AWS-only)."
  }
}

variable "awake" {
  description = "THE hibernation switch: false = only the seed bank (bucket) exists; true = the cluster exists."
  type        = bool
  default     = false
}

variable "gcp_project_id" {
  type = string
  validation {
    condition     = length(var.gcp_project_id) > 0
    error_message = "gcp_project_id is required (cloud=gcp needs gcp_project_id)."
  }
}

variable "region" {
  type    = string
  default = "asia-south1"
}

variable "admin_cidrs" {
  type    = list(string)
  default = []
}

variable "object_lock_days" {
  type    = number
  default = 30
}
