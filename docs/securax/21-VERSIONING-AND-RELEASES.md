# 21 — Versioning & release policy

How SecuRAX is versioned and released — the discipline a professional software product follows
(the same shape as Mattermost, Grafana, etc.), sized to this project.

## Semantic Versioning
We follow [SemVer 2.0](https://semver.org): **MAJOR.MINOR.PATCH**.
- **MAJOR** — incompatible/breaking changes to a public interface or behaviour.
- **MINOR** — new, backward-compatible capability.
- **PATCH** — backward-compatible bug/security fixes.

While in **`0.x`** the product is in initial development: the surface may still change between
minor versions, and only the latest `0.x` is supported ([`SECURITY.md`](../../SECURITY.md)). We
cut **`1.0.0`** when the standard interfaces in
[`17-ENTERPRISE-ARCHITECTURE.md`](17-ENTERPRISE-ARCHITECTURE.md) are considered stable.

### Single source of truth
The product version is the top-level [`VERSION`](../../VERSION) file. It is surfaced at runtime by
the gateway's **`GET /version`** endpoint (with the git commit, when built in CI). Long-lived
components may also carry their own component version (e.g. the gateway's OpenAPI `version`, the
Guiding Map PWA's service-worker cache tag) — those are deliberate and independent of the product
version.

**Every *visible* version label must derive from `VERSION`** — never be typed by hand. The Command
Center and the gateway read it at runtime; the Guiding Map's header badge is stamped from it by
`guiding-map/build.js` (so after bumping `VERSION`, run `cd guiding-map && node build.js`). A CI test
(`test_version_badge_matches_VERSION_file`) fails if the badge drifts or a hardcoded version returns.
(The badge once read "v13.0.2" — a legacy string from before the app joined the estate.)

## Conventional Commits
Commit messages use [Conventional Commits](https://www.conventionalcommits.org):
`type(scope): summary` — `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `deps`, `chore`.
`feat` → a MINOR bump, `fix` → a PATCH bump, and a `!` or `BREAKING CHANGE:` footer → a MAJOR bump.
This makes the changelog and the next version mechanical rather than a judgement call.

## Changelog
Every user-visible change is recorded in [`CHANGELOG.md`](../../CHANGELOG.md) under **[Unreleased]**
as part of its PR, in [Keep a Changelog](https://keepachangelog.com) format
(Added / Changed / Deprecated / Removed / Fixed / Security).

## Cutting a release
1. Move **[Unreleased]** entries into a new `## [X.Y.Z] - <date>` section in `CHANGELOG.md`.
2. Bump [`VERSION`](../../VERSION) to `X.Y.Z`.
3. Open a PR, get it green and reviewed, merge.
4. Tag the merge commit `vX.Y.Z` and push the tag.
5. The **release** workflow (`.github/workflows/release.yml`) runs the full test suite, builds the
   container images, generates the SBOM, and publishes a **GitHub Release** whose notes are taken
   from that version's `CHANGELOG.md` section.

Tags are immutable; a mistake is fixed by a new patch release, never by moving a tag.

## Supported versions & deprecation
See [`SECURITY.md`](../../SECURITY.md) for which versions get security fixes. A feature slated for
removal is first marked **Deprecated** in the changelog for at least one minor release before it is
removed in a subsequent (minor while `0.x`, major once `1.0`) release.
