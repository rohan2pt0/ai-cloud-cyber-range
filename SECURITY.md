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

## A fake copy, or misuse
SecuRAX holds things people care about, so copies that only look like it will appear.

- **Where the real one lives:** this repository, its Releases page, and the site and apps this repository's own
  workflows publish. Nothing else is SecuRAX: not an app-store listing we have not announced here, not a download
  link in a message, not a person offering to "set it up" for you.
- **How to check a copy:** every release file is listed in `SHA256SUMS` and carries a signed attestation of where it
  was built. `gh attestation verify FILE --repo OWNER/REPO` (with this repository's name) must pass; the steps are in
  [`docs/securax/21-VERSIONING-AND-RELEASES.md`](docs/securax/21-VERSIONING-AND-RELEASES.md).
- **What we never do:** ask for your password, backup phrase, bank details or a one-time code, by mail, phone or chat;
  give investment tips; or take money outside the published price.
- **Report a fake copy or misuse** (a look-alike site or app, someone selling "SecuRAX advice", the testing tools
  pointed at systems their user does not own, a feature set up on another person's phone or mailbox without their
  knowledge): use the private report link above, or the contact address in `brand.env`. We answer within 3 business days.

The testing tools (red team, the range, the hunt packs) are for systems you own or are authorised in writing to test.

## Where to look
The threat model, data-classification rules and control mapping live in
[`docs/securax/`](docs/securax/) (see `04-COMPLIANCE-MAP.md` and `17-ENTERPRISE-ARCHITECTURE.md`).
