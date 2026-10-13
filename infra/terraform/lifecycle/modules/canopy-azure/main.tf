# CANOPY (Azure) — AKS with a small always-on system pool and a user pool that scales between zero and N nodes.
variable "name" { type = string }
variable "location" { type = string }
variable "admin_cidrs" { type = list(string) }
variable "system_vm_size" { type = string }
variable "user_vm_size" { type = string }
variable "user_max_nodes" { type = number }

resource "azurerm_resource_group" "canopy" {
  name     = "${var.name}-canopy"
  location = var.location
}

resource "azurerm_kubernetes_cluster" "this" {
  name                = "${var.name}-canopy"
  location            = azurerm_resource_group.canopy.location
  resource_group_name = azurerm_resource_group.canopy.name
  dns_prefix          = "${var.name}-canopy"

  default_node_pool {
    name                         = "system"
    vm_size                      = var.system_vm_size
    auto_scaling_enabled         = true
    min_count                    = 1
    max_count                    = 3
    only_critical_addons_enabled = true
  }

  identity { type = "SystemAssigned" }

  api_server_access_profile {
    authorized_ip_ranges = length(var.admin_cidrs) > 0 ? var.admin_cidrs : null
  }

  azure_policy_enabled = true
}

resource "azurerm_kubernetes_cluster_node_pool" "user" {
  name                  = "user"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.this.id
  vm_size               = var.user_vm_size
  auto_scaling_enabled  = true
  min_count             = 0
  max_count             = var.user_max_nodes
}

output "cluster_name" { value = azurerm_kubernetes_cluster.this.name }
output "connect" { value = "az aks get-credentials --resource-group ${azurerm_resource_group.canopy.name} --name ${azurerm_kubernetes_cluster.this.name}" }
