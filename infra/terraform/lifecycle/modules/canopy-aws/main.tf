# CANOPY (phase 3, "run+") — a managed Kubernetes cluster on AWS EKS *Auto Mode*: AWS adds and removes nodes by itself
# as pods appear and disappear (horizontal elasticity with no autoscaler to babysit) and picks bigger or smaller
# machines for what you ask for (vertical elasticity). With no workloads the node count falls to zero.
variable "name" { type = string }
variable "k8s_version" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "public_subnet_ids" { type = list(string) }
variable "kms_key_arn" { type = string }
variable "admin_cidrs" { type = list(string) }
variable "node_pools" { type = list(string) }
variable "vault_bucket_arn" { type = string }

data "aws_iam_policy_document" "cluster_assume" {
  statement {
    actions = ["sts:AssumeRole", "sts:TagSession"]
    principals {
      type        = "Service"
      identifiers = ["eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "cluster" {
  name               = "${var.name}-canopy-cluster"
  assume_role_policy = data.aws_iam_policy_document.cluster_assume.json
}

resource "aws_iam_role_policy_attachment" "cluster" {
  for_each = toset([
    "AmazonEKSClusterPolicy",
    "AmazonEKSComputePolicy",
    "AmazonEKSBlockStoragePolicy",
    "AmazonEKSLoadBalancingPolicy",
    "AmazonEKSNetworkingPolicy",
  ])
  role       = aws_iam_role.cluster.name
  policy_arn = "arn:aws:iam::aws:policy/${each.value}"
}

data "aws_iam_policy_document" "node_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "node" {
  name               = "${var.name}-canopy-node"
  assume_role_policy = data.aws_iam_policy_document.node_assume.json
}

resource "aws_iam_role_policy_attachment" "node" {
  for_each   = toset(["AmazonEKSWorkerNodeMinimalPolicy", "AmazonEC2ContainerRegistryPullOnly"])
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/${each.value}"
}

resource "aws_eks_cluster" "this" {
  name     = "${var.name}-canopy"
  role_arn = aws_iam_role.cluster.arn
  version  = var.k8s_version != "" ? var.k8s_version : null # empty = AWS default (always a currently supported version)

  bootstrap_self_managed_addons = false

  # Stay on STANDARD support: clusters left on an out-of-support Kubernetes version are billed at several times the
  # normal control-plane fee ("extended support"). Better to be upgraded than to be surprised on the invoice.
  upgrade_policy { support_type = "STANDARD" }

  access_config {
    authentication_mode                         = "API"
    bootstrap_cluster_creator_admin_permissions = true
  }

  compute_config {
    enabled       = true
    node_pools    = var.node_pools
    node_role_arn = aws_iam_role.node.arn
  }

  kubernetes_network_config {
    elastic_load_balancing { enabled = true }
  }

  storage_config {
    block_storage { enabled = true }
  }

  vpc_config {
    subnet_ids              = var.private_subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = length(var.admin_cidrs) > 0
    public_access_cidrs     = length(var.admin_cidrs) > 0 ? var.admin_cidrs : null
  }

  encryption_config {
    resources = ["secrets"]
    provider { key_arn = var.kms_key_arn }
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator"]

  depends_on = [aws_iam_role_policy_attachment.cluster, aws_iam_role_policy_attachment.node]
}

output "cluster_name" { value = aws_eks_cluster.this.name }
output "endpoint" { value = aws_eks_cluster.this.endpoint }
output "connect" { value = "aws eks update-kubeconfig --name ${aws_eks_cluster.this.name}" }

# Velero (cluster backups) writes to the seed bank's vault through EKS Pod Identity: no long-lived keys anywhere.
data "aws_iam_policy_document" "velero_assume" {
  statement {
    actions = ["sts:AssumeRole", "sts:TagSession"]
    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "velero" {
  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"]
    resources = ["${var.vault_bucket_arn}/velero/*"]
  }
  statement {
    actions   = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = [var.vault_bucket_arn]
  }
  statement {
    actions   = ["kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
    resources = [var.kms_key_arn]
  }
}

resource "aws_iam_role" "velero" {
  name               = "${var.name}-canopy-velero"
  assume_role_policy = data.aws_iam_policy_document.velero_assume.json
}

resource "aws_iam_role_policy" "velero" {
  name   = "vault-backup"
  role   = aws_iam_role.velero.id
  policy = data.aws_iam_policy_document.velero.json
}

resource "aws_eks_pod_identity_association" "velero" {
  cluster_name    = aws_eks_cluster.this.name
  namespace       = "velero"
  service_account = "velero"
  role_arn        = aws_iam_role.velero.arn
}

output "velero_role_arn" { value = aws_iam_role.velero.arn }
