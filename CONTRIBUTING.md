# Contributing Guide

This repository documents architecture standards.
When contributing, treat these docs as a system of contracts, not isolated notes.

## Source of Truth

- Client canonical base: `client/core/*`
- Client framework layer: `client/frameworks/*`
- Client agent skill: curated derivatives under `client/skill/references/*`
- Server canonical base: `server/core/*`
- Server runtime layer: `server/runtime/*`
- Server agent skill: curated derivatives under `server/skill/references/*`
- Monorepo canonical base: `monorepo/core/*`
- Monorepo build-system layer: `monorepo/build-systems/*`
- Monorepo agent skill: curated derivatives under `monorepo/skill/references/*`

Rule:

- Keep `core/*` framework/runtime-agnostic.
- Put framework/runtime-specific behavior in framework/runtime folders.
- Keep `monorepo/core/*` build-system and package-manager agnostic.
- Keep build-system specializations thin and resolve version-sensitive behavior from matching authoritative sources.
- Curate portable skills down to durable concepts, rationale, outcomes, and decision criteria. Retain named libraries and official links when they clarify a supported specialization or selection choice. Do not copy vendor-owned API symbols, framework filenames, configuration keys, flags, version matrices, deprecations, or migration recipes from canonical examples into a skill; the executing agent detects installed versions, retrieves current primary documentation, and verifies the derived implementation.

## Contribution Types

### 1) Add or update architecture guidance

Use this flow:

1. Update canonical docs first (`core/*`) if the rule is agnostic.
2. Update framework/runtime docs for implementation-specific behavior.
3. Add or update diagrams only when they clarify boundaries or flow.
4. Add a changelog entry under `change-logs/` for non-trivial doc updates.

### 2) Add a new client framework (example: Vue)

Create:

- `client/frameworks/<framework>/README.md`
- `client/frameworks/<framework>/overview.md`
- Optional: `client/frameworks/<framework>/metaframeworks/<meta>/README.md`

Must align with existing client contracts:

- `components -> query adapter -> featureApi -> clientApi -> network`
- Error normalization to `AppError`
- Server-state ownership in query adapter layer

Also update:

- `client/frameworks/README.md`
- `client/README.md` (framework docs index)

Do not:

- move canonical rules out of `client/core/*`
- duplicate core rules in framework docs unless adding framework-specific constraints

### 3) Add a new server runtime/language (example: Go)

Create:

- `server/runtime/<runtime>/README.md` (for Go, use `server/runtime/go/README.md`)
- Runtime-specific subfolders as needed (libraries, metaframeworks, adapters)

Must align with existing server contracts:

- Layer boundaries from `server/core/conventions.md`
- Error and response envelope contracts from `server/core/error-handling.md` and `server/core/api-response.md`
- Transaction and logging expectations from `server/core/transaction.md` and `server/core/logging.md`

Also update:

- `server/runtime/README.md`
- `server/README.md`
- `README.md` (top-level structure/index)

Do not:

- move runtime-specific details into `server/core/*`
- couple server core rules to one runtime/framework

### 4) Add a new monorepo build system (example: Nx)

Create:

- `monorepo/build-systems/<build-system>/README.md`
- A scaffolding mapping only when the build system is executable through the generic contract

Must align with:

- `monorepo/core/architecture.md`
- `monorepo/core/package-boundaries.md`
- `monorepo/core/scaffolding.md`

Do not copy a vendor manual or freeze version-sensitive configuration in this repository. Detect the target version, retrieve matching official sources, map the durable core outcomes, and verify with the actual tool.

## Cross-Layer Consistency Requirements

When adding any new stack/framework/runtime, validate these contracts remain consistent:

- Client API chain and layer ownership
- Query key strategy (direct tRPC generated keys, `buildTrpcQueryKey` for wrapper interop, plain keys for non-tRPC adapters)
- Error normalization boundary (`unknown -> AppError`)
- Logging/correlation boundary ownership (`requestId` and related metadata at transport boundaries)
- Equal canonical single-project and monorepo topology mappings
- Cross-package ownership (`$monorepo`) versus resolved client/server package ownership
- Package and onion dependency direction

## Documentation Style Rules

- Prefer additive updates over broad rewrites.
- Keep examples concrete but avoid forcing one project-specific path unless required.
- Mark legacy/reference-only content explicitly as non-canonical.
- Treat framework and vendor examples as dated implementation evidence, not version authority for portable skills. A library link supports discovery; it does not make the linked page's current syntax part of the architecture contract.

## Pull Request Checklist

- [ ] Updated the correct layer (`core` vs framework/runtime)
- [ ] Updated the correct topology/build-system layer (`monorepo/core` vs specialization)
- [ ] Kept canonical contracts unchanged unless intentionally evolving them
- [ ] Updated indices/README links for new folders
- [ ] Added/updated changelog for non-trivial changes
- [ ] Verified no contradictory guidance across related docs
- [ ] Portable skills retain library roles, rationale, and official links without freezing vendor syntax or version-specific recipes

## If You Are Unsure Where A Rule Belongs

Use this rule of thumb:

- Works across frameworks/runtimes: put it in `core/*`
- Depends on specific framework/runtime behavior: put it in framework/runtime docs
- If both apply: define the contract in `core/*`, then add implementation details in framework/runtime docs
- Works across monorepo build systems/package managers: put it in `monorepo/core/*`
- Depends on a build-system version: keep only a thin mapping under `monorepo/build-systems/*` and retrieve current official behavior at execution time

## Maintaining the Client Skill

The client docs remain canonical. The `$client` skill reorganizes their guidance into concern-based skill slices and conditionally loaded convention leaves for portable, progressive loading.

When changing a mapped client source document:

1. Run `python3 client/skill-maintenance/check-source-drift.py`.
2. Review every slice or convention leaf reported as stale and update its reference when the source change affects the derived guidance.
3. Refresh only reviewed references with `python3 client/skill-maintenance/check-source-drift.py --refresh <slice-or-leaf>`.
4. Run the drift check again and validate `client/skill/` with the official skill validator.

Do not refresh a fingerprint without reviewing the associated reference. Update `client/skill-maintenance/source-map.json` when a source document starts or stops informing a slice or convention leaf. Maintenance tooling stays outside `client/skill/` so it is not copied into consumer installations.

## Maintaining the Server Skill

The server docs remain canonical. The `$server` skill reorganizes their guidance into concern-based references for portable, progressive loading.

When changing a mapped server source document:

1. Run `python3 server/skill-maintenance/check-source-drift.py`.
2. Review every slice reported as stale and update its reference when the source change affects the derived guidance.
3. Refresh one reviewed slice with `python3 server/skill-maintenance/check-source-drift.py refresh <slice>`.
4. Run the drift check again and validate `server/skill/` with the official skill validator.

Do not refresh a fingerprint without reviewing the associated reference. Update `server/skill-maintenance/source-map.json` when a source document starts or stops informing a slice. Every canonical `server/**/*.md` guide outside `server/skill/` must remain mapped to at least one slice. Maintenance tooling stays outside `server/skill/` so it is not copied into consumer installations.

## Maintaining the Monorepo Skill

The monorepo docs remain canonical. The `$monorepo` skill reorganizes their guidance into topology, package, scaffolding, and build-system slices.

When changing a mapped monorepo source document:

1. Run `python3 monorepo/skill-maintenance/check-source-drift.py`.
2. Review every stale slice against the changed source.
3. Refresh one reviewed slice with `python3 monorepo/skill-maintenance/check-source-drift.py refresh <slice>`.
4. Run the drift check again and validate `monorepo/skill/` with the official skill validator.

Do not refresh a fingerprint without reviewing its reference. Every canonical `monorepo/**/*.md` guide outside `monorepo/skill/` must remain mapped to at least one slice. Maintenance tooling stays outside the portable skill.
