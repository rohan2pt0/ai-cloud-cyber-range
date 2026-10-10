#!/usr/bin/env bash
# Bring up the Kubernetes plane: kind cluster + Kyverno + Falco + the hardened gateway.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT/local/k8s"
log() { printf '\033[1;36m[range-k8s]\033[0m %s\n' "$*"; }

log "Creating kind cluster 'range' (3 nodes, audit logging on)"
kind get clusters | grep -qx range || kind create cluster --config kind-cluster.yaml --name range

log "Loading the locally-built gateway image into the cluster"
docker image inspect vulnbank/llm-gateway:dev >/dev/null 2>&1 || docker build -t vulnbank/llm-gateway:dev "$ROOT/apps/llm-gateway"
kind load docker-image vulnbank/llm-gateway:dev --name range

log "Installing Kyverno (admission control)"
helm repo add kyverno https://kyverno.github.io/kyverno >/dev/null 2>&1 || true
helm repo update >/dev/null
helm upgrade --install kyverno kyverno/kyverno -n kyverno --create-namespace --wait

log "Applying workload, network policy and admission policies"
kubectl apply -f gateway.yaml
kubectl apply -f policies/networkpolicy.yaml
kubectl apply -f policies/kyverno-policies.yaml
kubectl -n ai rollout status deploy/llm-gateway --timeout=120s

log "Negative test: an insecure pod (root, :latest) must be REJECTED by Kyverno"
if kubectl -n ai run bad --image=nginx:latest --restart=Never --dry-run=server 2>/tmp/kyverno.err; then
  echo "  FAIL - insecure pod was admitted"; exit 1
else
  log "  PASS - admission denied:"; sed 's/^/    /' /tmp/kyverno.err | head -4
fi
log "K8s plane ready. Gateway NodePort -> http://localhost:8080"
