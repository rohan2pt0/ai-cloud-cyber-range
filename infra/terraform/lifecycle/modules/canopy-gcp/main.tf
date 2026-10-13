# CANOPY (GCP) — GKE Autopilot: Google adds/removes nodes and right-sizes them per pod, so capacity follows demand.
variable "name" { type = string }
variable "project_id" { type = string }
variable "region" { type = string }
variable "admin_cidrs" { type = list(string) }

resource "google_compute_network" "this" {
  name                    = "${var.name}-canopy"
  project                 = var.project_id
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "this" {
  name                     = "${var.name}-canopy"
  project                  = var.project_id
  region                   = var.region
  network                  = google_compute_network.this.id
  ip_cidr_range            = "10.20.0.0/20"
  private_ip_google_access = true
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.24.0.0/14"
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.28.0.0/20"
  }
}

resource "google_container_cluster" "this" {
  name                = "${var.name}-canopy"
  project             = var.project_id
  location            = var.region
  enable_autopilot    = true
  deletion_protection = false
  network             = google_compute_network.this.id
  subnetwork          = google_compute_subnetwork.this.id

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
  }

  dynamic "master_authorized_networks_config" {
    for_each = length(var.admin_cidrs) > 0 ? [1] : []
    content {
      dynamic "cidr_blocks" {
        for_each = var.admin_cidrs
        content { cidr_block = cidr_blocks.value }
      }
    }
  }

  release_channel { channel = "REGULAR" }
}

output "cluster_name" { value = google_container_cluster.this.name }
output "connect" { value = "gcloud container clusters get-credentials ${google_container_cluster.this.name} --region ${var.region} --project ${var.project_id}" }
