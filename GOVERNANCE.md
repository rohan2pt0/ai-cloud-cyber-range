# Governance

SecuRAX uses a lightweight **BDFL-style** model appropriate to its current size.

## Roles
- **Maintainers** (see [`MAINTAINERS.md`](MAINTAINERS.md)) review and merge changes, cut releases,
  and set direction. They are the code owners (see `.github/CODEOWNERS`).
- **Contributors** are anyone who opens an issue or pull request. You do not need to be a
  maintainer to propose a change.

## How decisions are made
- **Everyday changes** (bug fixes, docs, small features) are decided by maintainer review on the PR.
- **Significant/architectural changes** are proposed first — as an issue or a short ADR under
  `docs/` — and discussed before implementation, so the design is agreed before the code.
- Changes must honour the project [principles](docs/securax/01-PRINCIPLES.md) and the end-state
  [conformance rules](docs/securax/17-ENTERPRISE-ARCHITECTURE.md).

## Releases
Releases follow [`docs/securax/21-VERSIONING-AND-RELEASES.md`](docs/securax/21-VERSIONING-AND-RELEASES.md)
(SemVer, Conventional Commits, CHANGELOG-driven).

## Changing this document
Governance changes are themselves significant changes: propose, discuss, then merge.

## Growing the model
As the contributor base grows, this will evolve toward a maintainers' committee with a documented
voting rule. Until then, keep it simple.
