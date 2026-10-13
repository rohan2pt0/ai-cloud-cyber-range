# TREE (phase 2, "run") — ONE small cloud machine running k3s (a tiny, real Kubernetes), reachable only through SSM or
# a private tailscale mesh (no inbound ports at all). Its state lives on the persistent "roots" disk, so when the
# machine is put to sleep (terraform apply -var awake=false) and later woken, k3s comes back with everything it knew.
variable "name" { type = string }
variable "subnet_id" { type = string }
variable "vpc_id" { type = string }
variable "instance_type" { type = string }
variable "ami_id" { type = string }
variable "roots_volume_id" { type = string }
variable "kms_key_arn" { type = string }
variable "vault_bucket_arn" { type = string }
variable "k3s_version" { type = string }
variable "gitops_repo" { type = string }
variable "gitops_ref" { type = string }
variable "argocd_version" { type = string }
variable "tailscale_auth_key" {
  type      = string
  default   = ""
  sensitive = true
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "tree" {
  name               = "${var.name}-tree"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

# Operate it without opening any port: SSM Session Manager.
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.tree.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

data "aws_iam_policy_document" "vault" {
  statement {
    actions   = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
    resources = [var.vault_bucket_arn, "${var.vault_bucket_arn}/*"]
  }
  statement {
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [var.kms_key_arn]
  }
}

resource "aws_iam_role_policy" "vault" {
  name   = "vault-access"
  role   = aws_iam_role.tree.id
  policy = data.aws_iam_policy_document.vault.json
}

resource "aws_iam_instance_profile" "tree" {
  name = "${var.name}-tree"
  role = aws_iam_role.tree.name
}

resource "aws_security_group" "tree" {
  name        = "${var.name}-tree"
  description = "k3s node: NO inbound; all egress"
  vpc_id      = var.vpc_id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

locals {
  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    k3s_version        = var.k3s_version
    volume_id_nodash   = replace(var.roots_volume_id, "-", "")
    tailscale_auth_key = var.tailscale_auth_key
    hostname           = var.name
    gitops_repo        = var.gitops_repo
    gitops_ref         = var.gitops_ref
    argocd_version     = var.argocd_version
  })
}

resource "aws_instance" "tree" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.tree.id]
  iam_instance_profile   = aws_iam_instance_profile.tree.name
  user_data              = local.user_data
  ebs_optimized          = true
  monitoring             = true

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }
  root_block_device {
    volume_type = "gp3"
    volume_size = 30
    encrypted   = true
    kms_key_id  = var.kms_key_arn
  }
  tags = { Name = "${var.name}-tree", securax-organ = "tree" }
}

resource "aws_volume_attachment" "roots" {
  device_name = "/dev/sdf"
  volume_id   = var.roots_volume_id
  instance_id = aws_instance.tree.id
}

output "instance_id" { value = aws_instance.tree.id }
output "connect" { value = "aws ssm start-session --target ${aws_instance.tree.id}" }
