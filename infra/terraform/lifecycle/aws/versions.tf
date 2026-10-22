terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
  # Remote state is recommended once you are awake for real: create the seed bank first (stage=seed), then point a
  # backend at its vault bucket. A solo lab can keep local state.
}

provider "aws" {
  region = var.region
  # `offline` lets CI prove the plan (what would exist awake vs dormant) with no cloud account.
  skip_credentials_validation = var.offline
  skip_requesting_account_id  = var.offline
  skip_metadata_api_check     = var.offline
  skip_region_validation      = var.offline
  default_tags {
    tags = { project = "securax", managed-by = "terraform", stage = var.stage }
  }
}
