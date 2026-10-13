# SEED BANK (Azure) — an always-present, near-free vault: a versioned storage account for backups and state.
variable "name" { type = string }
variable "location" { type = string }

resource "random_id" "suffix" { byte_length = 3 }

resource "azurerm_resource_group" "seed" {
  name     = "${var.name}-seed"
  location = var.location
}

resource "azurerm_storage_account" "vault" {
  name                            = substr(replace("${var.name}vault${random_id.suffix.hex}", "-", ""), 0, 24)
  resource_group_name             = azurerm_resource_group.seed.name
  location                        = azurerm_resource_group.seed.location
  account_tier                    = "Standard"
  account_replication_type        = "GRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  blob_properties {
    versioning_enabled = true
    delete_retention_policy { days = 30 }
  }
}

resource "azurerm_storage_container" "vault" {
  name                  = "vault"
  storage_account_id    = azurerm_storage_account.vault.id
  container_access_type = "private"
}

output "vault_storage_account" { value = azurerm_storage_account.vault.name }
