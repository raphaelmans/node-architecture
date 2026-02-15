# Contributing Guide

This repository documents architecture standards.
When contributing, treat these docs as a system of contracts, not isolated notes.

## Source of Truth

- Client canonical base: `client/core/*`
- Client framework layer: `client/frameworks/*`
- Server canonical base: `server/core/*`
- Server runtime layer: `server/runtime/*`

Rule:

- Keep `core/*` framework/runtime-agnostic.
- Put framework/runtime-specific behavior in framework/runtime folders.

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

## Cross-Layer Consistency Requirements

When adding any new stack/framework/runtime, validate these contracts remain consistent:

- Client API chain and layer ownership
- Query key strategy (tRPC generated keys vs Query Key Factory for non-tRPC adapters)
- Error normalization boundary (`unknown -> AppError`)
- Logging/correlation boundary ownership (`requestId` and related metadata at transport boundaries)

## Documentation Style Rules

- Prefer additive updates over broad rewrites.
- Keep examples concrete but avoid forcing one project-specific path unless required.
- Mark legacy/reference-only content explicitly as non-canonical.

## Pull Request Checklist

- [ ] Updated the correct layer (`core` vs framework/runtime)
- [ ] Kept canonical contracts unchanged unless intentionally evolving them
- [ ] Updated indices/README links for new folders
- [ ] Added/updated changelog for non-trivial changes
- [ ] Verified no contradictory guidance across related docs

## If You Are Unsure Where A Rule Belongs

Use this rule of thumb:

- Works across frameworks/runtimes: put it in `core/*`
- Depends on specific framework/runtime behavior: put it in framework/runtime docs
- If both apply: define the contract in `core/*`, then add implementation details in framework/runtime docs
