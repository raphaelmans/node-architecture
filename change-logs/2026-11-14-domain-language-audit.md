# Domain Language Audit

Date: 2026-11-14

## Changes

- Grouped the `CONTEXT.md` glossary into clusters and added the terms the docs already relied on without defining: Feature, Capability, Architecture role, Organization, Membership, Actor, Organization role, Permission catalog, Access scope, Scoped assignment, Active organization, Access result, Provider-managed endpoint, Business component and Presentation component.
- Made Organization the canonical tenant boundary. Product workspace now names only how a product presents an organization to its users.
- Separated Operation (the business action and scaffold target) from Capability (the server-side behavior that fulfils one operation). Server scaffolding now targets `<module>/<operation>`; client scaffolding keeps `<feature>/<operation>` and calls its unit a feature operation. Removed "vertical capability", "vertical feature" and "capability slices".
- Replaced references to a "monorepo `workspace` slice", which does not exist, with the `$client`/`$server` `workspace` topology slice.
- Listed Better Auth in the top-level technology table and documented convention leaves and the checker test in the server skill maintenance steps.

- Renamed `server/runtime/` to `server/runtimes/` and `server/runtimes/nodejs/metaframeworks/` to `server/runtimes/nodejs/frameworks/`, matching `client/frameworks/`, `development/runtimes/` and `monorepo/build-systems/`. Express, Hono and NestJS are not metaframeworks. Links into the old paths from outside this repository break.
- Standardised on "entrypoint" and replaced the generic sense of "capability" in the scaffolding contracts with "infrastructure concern".
- Gave the client drift checker the same `refresh <slice-or-leaf> ...` subcommand as the other three; `--refresh` and `--refresh-all` are removed.
- Recorded three existing decisions as ADRs 0005 to 0007 (provider-managed endpoints, deployable-owned environment, atomic repository operations), added an ADR index, and linked the glossary and ADRs from `README.md`, `CONTRIBUTING.md` and the owning canonical docs.

## Validation

- Reviewed the affected portable references with their canonical sources and refreshed the client and server source fingerprints; all four drift checks report current after the renames.
- Ran the server drift-checker unit tests.
- Checked every local Markdown link and heading anchor outside `legacy/` and `change-logs/`.
