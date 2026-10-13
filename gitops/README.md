# gitops/ — the estate's DNA (what Argo CD grows once a cluster exists)

Terraform (`infra/terraform/lifecycle`) only creates the *soil*: a cluster and its cloud plumbing. **Everything that runs
inside the cluster is defined here and pulled by Argo CD**, which keeps the cluster equal to git (self-heal) and removes
anything that is not in git (prune). A rebuilt or re-woken cluster therefore converges to the same estate without
anyone re-running steps.

```
root-app.yaml            applied once by ./securax grow (or the tree node's user-data)
bootstrap/               "app of apps": platform, core, tenants
platform/                cert-manager · KEDA (scale-to-zero) · Kyverno policies + engine · Falco · kube-prometheus-stack
core/                    the shared model router (LiteLLM) every tenant gateway talks to
templates/velero.app.yaml.tmpl   backups; rendered by ./securax grow with the vault bucket/region (cloud facts are not in git)
charts/tenant/           ONE template that differentiates into a full tenant cell (namespace, quota, network policy, gateway…)
tenants/<id>.yaml        add a file → a tenant appears; delete it → the tenant is pruned.  See tenants/README.md
```

Nature's pattern: every cell carries the same genome and differentiates by which genes are switched on. Here the genome is
`charts/tenant`; a tenant file is the signal that switches it on.

**Version pins:** Argo CD itself is pinned in `lifecycle`. Helm charts are pinned to a *major* range (for example `2.*`):
you get fixes but not breaking changes. After the first healthy sync, copy the exact versions Argo shows into these files
if you want fully frozen builds.
