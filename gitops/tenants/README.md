# Tenants

Add `gitops/tenants/<id>.yaml`, commit, push — Argo CD stamps a full tenant cell from `charts/tenant`.
Delete the file — the cell is pruned (its cloud-side key and bucket persist until you remove them in Terraform on purpose).

```yaml
id: acme            # 2-16 chars, lowercase letters/digits, starts with a letter (also the Terraform tenant key)
name: ACME Bank
tier: small         # small | medium | large  -> quota, replicas, autoscaling ceiling
oidcGroup: acme-staff   # Keycloak group whose members get access to the namespace
```

`./securax tenant add <id> --name "ACME Bank" --tier small --group acme-staff` writes this file for you.
