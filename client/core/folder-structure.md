# Folder Structure (Agnostic)

This document describes framework-agnostic client directory conventions.

## High-Level Structure

```text
src/
  <routes>/            # Metaframework-owned routes (Next.js: app/)
  common/              # App-wide shared utilities
    errors/            # AppError contract + adapters/facades
    query-keys/        # Server-state cache keys (cross-feature)
    toast/             # Toast facade + provider adapters
    logging/           # Client logging (debug) + wrappers/adapters
  components/          # Shared UI components
  features/            # Feature modules (primary unit of organization)
  hooks/               # Global framework hooks (React only)
  lib/                 # Core logic & integrations
```

Metaframework-specific routing conventions:

- Next.js: `client/frameworks/reactjs/metaframeworks/nextjs/folder-structure.md`

## Feature Module Structure

```text
src/features/<feature>/
  components/
    <feature>-view.tsx          # business component (composition + wiring)
    <feature>-fields.tsx        # presentation components (render-only)
  hooks.ts                      # query adapter (framework-specific)
  api.ts                        # I<Feature>Api + <Feature>Api class + factory
  schemas.ts                    # Zod schemas + derived types + mapping helpers
  types.ts                      # non-DTO types
  domain.ts                     # pure business rules
  helpers.ts                    # small pure helpers
```

## Feature Starter Contract

Required files for a new feature:

- `components/<feature>-view.tsx` (business wiring/composition)
- `components/<feature>-fields.tsx` (presentation-only UI, if form/field heavy)
- `api.ts` (`I<Feature>Api` + `<Feature>Api` + factory)
- `hooks.ts` (query adapter)
- `schemas.ts` (zod schemas + derived types)

Recommended files:

- `domain.ts` for deterministic domain rules
- `helpers.ts` for small pure transforms
- `types.ts` for non-DTO feature-owned types

Optional:

- `stores/*` only for client coordination state (not primary server data)

Tests for these files go in `src/__tests__/features/<feature>/` — never colocated.
See Testing Layout below and `client/core/testing.md`.

## Ownership Boundaries by Path

- `src/features/<feature>/api.ts`: endpoint-scoped data access for one feature via `I<Feature>Api` + class implementation.
- `src/features/<feature>/hooks.ts`: query/mutation/cache behavior.
- `src/features/<feature>/components/*`: composition + rendering only.
- `src/common/query-keys/*`: cross-feature cache key contracts.
- `src/common/errors/*`: `AppError` contract + normalization adapters/facades.
- `src/common/toast/*`: notification facade + provider adapters.
- `src/common/logging/*`: logger contract + adapters/wrappers.

## Testing Layout

Tests live in `src/__tests__/` and **mirror the source tree exactly**. Never colocate test files next to source files.

```text
src/
  __tests__/
    features/
      <feature>/
        api.test.ts       # mock clientApi + toAppError, assert class behavior
        hooks.test.ts     # mock I<Feature>Api, assert query/invalidation behavior
        domain.test.ts    # pure table-driven tests (no mocks)
        helpers.test.ts   # pure table-driven tests (no mocks)
    common/
      errors/
        error-adapter.test.ts
    lib/
      modules/
        <module>/
          shared/
            domain.test.ts
```

Full testing standard: `client/core/testing.md`.

## Cross-Feature Promotion Rules

Promote from feature-local to `src/common/*` only when all are true:

1. used in multiple features
2. not owned by one domain workflow
3. stable API contract is clear

Otherwise keep it in the feature module.
