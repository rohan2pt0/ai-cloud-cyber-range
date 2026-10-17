# 65 · Configuration, not code: nothing specific is hardwired

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** brand.env and integrations.txt are read by the site build, the scripts and go; the config-clean fitness check enforces it in CI. The two Next rows are not built. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

SecuRAX must keep working when a name, a domain, a vendor or an address changes. The rule is the one behind using a
hostname instead of an IP address: **code refers to a name; one small file says what that name means today.**

## The two files

| File | Holds | Like |
|---|---|---|
| **`brand.env`** | your brand name, product name, public domain, contact address, code repository, image registry | a `.env` for identity |
| **`integrations.txt`** | the optional parts that are switched on, one per line: `tailscale`, `ntfy`, `webhook`, `cron`, `regwatch`, `backup`, `cloudflare-pages`, `github`, `tls` | `requirements.txt` |

- Every value in `brand.env` is optional. An environment variable with the same name wins, so CI or another host can
  override it without editing the file.
- Delete or comment out a line in `integrations.txt` to switch that part off. `./securax go` and `./securax doctor` then
  skip it and say so; nothing reports it as broken. With no file at all, everything is on.
- The **core is never optional**: Docker, the gateway, the app, Chat and the local model.

```bash
./securax config show                  # each value, and where it came from (brand.env or your environment)
./securax config check                 # validate both files, and fail if a brand value is hardwired in code
./securax config enabled tailscale     # exit 0 when that integration is on (for scripts)
```

## What reads them

| Part | Before | Now |
|---|---|---|
| Product site (`website/`) | domain, contact e-mail and brand written into every page | `{{SITE_DOMAIN}}`, `{{CONTACT_EMAIL}}`, `{{BRAND_NAME}}` placeholders, filled by `website/build.sh` |
| Docs build (`mkdocs.yml`) | site address and copyright fixed | both come from the environment, which the build sets from `brand.env` |
| `tools/publish-clean.sh` | brand name and e-mail fixed | read from `brand.env`; falls back to the GitHub organisation name |
| Regulator watch | its polite identification named the site | built from `SITE_DOMAIN`, or none |
| `./securax go`, `doctor` | always tried Tailscale, alerts, schedules, regulator watch, backup | do only what `integrations.txt` lists |

The registrar and the static host are named only in the docs, as today's example. Any registrar and any static host
work.

## The guard that keeps it true

`config-clean` is a fitness check, so it runs in CI on every change. It fails when:

- a value from `brand.env` (brand name, domain, contact address) appears in a code file;
- a registrar or hosting vendor is named in a code file;
- `brand.env` holds something malformed (an e-mail that is not one, a domain with `https://`), or `integrations.txt`
  names an integration that does not exist.

Human text is allowed to name them: Markdown docs, `LICENSE`, `MAINTAINERS.md`, `CHANGELOG.md`. The deployment manifests
that must carry a literal repository address (Argo CD, Terraform defaults, Dockerfile labels, `CODEOWNERS`) are rewritten
in one step by `tools/publish-clean.sh` when the code moves.

## Further practices for a robust, distributed SecuRAX

| Practice | Why | Where it stands |
|---|---|---|
| **Names, not addresses** | an address change must not need a code change | done: services by DNS name inside Docker, the Tailscale name detected, `SECURAX_DOMAIN` for the HTTPS edge |
| **One source of truth per setting** | two copies drift | done: `brand.env`, `integrations.txt`, `.env` for secrets, `docs/status.yml` for status lights |
| **Secrets apart from configuration** | config can be public; secrets never | done: secrets only in `.env` (never committed); `brand.env` holds nothing secret |
| **Validate configuration at start-up, fail with the fix** | a typo should be one clear line, not a mystery outage | done for these files (`config check`); `preflight` and `go` for the estate |
| **Safe defaults when a setting is missing** | a new install should work before anyone configures it | done: every brand value optional; no `integrations.txt` = all on; placeholder secrets replaced on start |
| **Feature switches instead of code edits** | turning a part off must not need a release | done for integrations; `SECURAX_OPTIONAL` for add-ons; `GUARDRAIL_MODE`, `FAIL_MODE` for the gateway |
| **Pinned, declared dependencies** | the same build every time | done: image tags pinned, `requirements.txt` per service, vendored skills hashed (`./securax vet verify`) |
| **Health checks and readiness by name** | callers find out a dependency is down before they depend on it | done: `/healthz`, `/readyz`, compose health gates |
| **Idempotent setup** | running setup twice must be safe | done: `./securax go` only acts on what is missing |
| **Contracts between parts** | a change in one part must not silently break another | done: OpenAI-compatible API at the gateway, the impact map (`./securax impact`), CI journeys |
| **Configuration as data for the rest** | regulators, feeds, residency zones and tool policies change more often than code | done: `governance/regulators/`, `regwatch-feeds.json`, `governance/residency/`, `TOOL_POLICY_FILE` |
| **Next: one config schema across the estate** | today `.env`, `brand.env` and the JSON files are checked separately | build a single `securax config check` that also validates `.env` keys and the JSON data files against a schema |
| **Next: service discovery for more than one machine** | the estate is one laptop today | when a second node joins, register services in DNS or Tailscale tags instead of fixed names in compose |
