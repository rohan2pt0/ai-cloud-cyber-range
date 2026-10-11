# Security Policy

SecuRAX is a security product, so we hold its own security to a high bar and welcome
coordinated disclosure.

## Supported versions
During initial development (`0.x`), only the **latest** released minor version receives security
fixes. Once `1.0.0` ships, the two most recent minor versions will be supported.

| Version | Supported |
|---|---|
| latest `0.x` | ✅ |
| older | ❌ |

## Reporting a vulnerability
**Do not open a public issue for a security vulnerability.**

Use GitHub's **private vulnerability reporting**:
[Security → Report a vulnerability](https://github.com/rohan2pt0/ai-cloud-cyber-range/security/advisories/new).

Please include:
- affected component and version (see the `VERSION` file / the gateway `/version` endpoint),
- a description and the impact,
- reproduction steps or a proof of concept,
- any suggested remediation.

## Our commitment (targets)
- **Acknowledge** your report within **3 business days**.
- **Triage** and share an initial assessment within **10 business days**.
- **Fix** and release on a severity-based timeline, then publish an advisory crediting you
  (unless you prefer to remain anonymous).

Please give us a reasonable window to remediate before any public disclosure (we aim for 90 days
or sooner).

## Scope
In scope: the code in this repository (gateway, MCP server, agents, PWA, IaC, CI).
Out of scope: third-party dependencies and services (report those upstream), findings that require
a compromised host or physical access, and social-engineering of maintainers.

## Safe harbour
Good-faith security research that respects this policy, avoids privacy violations and service
disruption, and does not exfiltrate data beyond what is needed to prove a finding will not be
pursued or reported by us.

## Where to look
The threat model, data-classification rules and control mapping live in
[`docs/securax/`](docs/securax/) (see `04-COMPLIANCE-MAP.md` and `17-ENTERPRISE-ARCHITECTURE.md`).
