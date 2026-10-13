# Azure slice: a consumption budget with action group, Defender for Cloud (free
# Foundational CSPM) and Azure AI Content Safety (the Prompt Shields endpoint the
# gateway calls). Everything sits in one resource group in Central India.
terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.14" }
  }
}
# NOTE: no `provider "azurerm"` block here on purpose. A module that carries its own provider block cannot be
# used with count/for_each (Terraform refuses); the calling environment configures the provider instead.

variable "location" {
  type    = string
  default = "centralindia"
}
variable "subscription_id" { type = string }
variable "budget_usd" {
  type    = number
  default = 30
}
variable "alert_email" { type = string }
variable "enable_paid" {
  type    = bool
  default = false
}

resource "azurerm_resource_group" "range" {
  name     = "rg-ai-cyber-range"
  location = var.location
  tags     = { project = "ai-cloud-cyber-range", managed_by = "terraform" }
}

# --- Cost control: budget + action group that emails on 50/90/100% --------------------
resource "azurerm_monitor_action_group" "budget" {
  name                = "ag-range-budget"
  resource_group_name = azurerm_resource_group.range.name
  short_name          = "rangebudg"
  email_receiver {
    name          = "owner"
    email_address = var.alert_email
  }
}

resource "azurerm_consumption_budget_subscription" "monthly" {
  name            = "range-monthly-ceiling"
  subscription_id = "/subscriptions/${var.subscription_id}"
  amount          = var.budget_usd
  time_grain      = "Monthly"
  time_period { start_date = formatdate("YYYY-MM-01'T'00:00:00'Z'", timestamp()) }
  dynamic "notification" {
    for_each = [50, 90, 100]
    content {
      enabled        = true
      threshold      = notification.value
      operator       = "GreaterThanOrEqualTo"
      threshold_type = "Actual"
      contact_groups = [azurerm_monitor_action_group.budget.id]
    }
  }
  lifecycle { ignore_changes = [time_period] }
}

# --- Azure AI Content Safety (Prompt Shields) - F0 free SKU where available -----------
resource "azurerm_cognitive_account" "content_safety" {
  name                  = "range-content-safety"
  location              = azurerm_resource_group.range.location
  resource_group_name   = azurerm_resource_group.range.name
  kind                  = "ContentSafety"
  sku_name              = var.enable_paid ? "S0" : "F0"
  custom_subdomain_name = "range-content-safety-${var.subscription_id}"
  identity { type = "SystemAssigned" }
  tags = azurerm_resource_group.range.tags
}

# --- Defender for Cloud: Foundational CSPM is free; CSPM plan gated behind enable_paid --
resource "azurerm_security_center_subscription_pricing" "cspm" {
  count         = var.enable_paid ? 1 : 0
  tier          = "Standard"
  resource_type = "CloudPosture"
}

output "content_safety_endpoint" { value = azurerm_cognitive_account.content_safety.endpoint }
output "resource_group" { value = azurerm_resource_group.range.name }
