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
    logging/           # Client logging facade + adapters + wrappers
    clients/           # Non-tRPC API client wrappers (HTTP + realtime)
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
  api.ts                        # I<Feature>Api + <Feature>Api class + factory
  api.runtime.ts                # re-exports singleton factory (stable mock target)
  hooks.ts                      # query adapter (framework-specific)
  schemas.ts                    # Zod schemas + derived types + mapping helpers
  types.ts                      # non-DTO types
  helpers.ts                    # small pure helpers
```

## Feature Starter Contract

Required files for a new feature:

- `components/<feature>-view.tsx` (business wiring/composition)
- `components/<feature>-fields.tsx` (presentation-only UI, if form/field heavy)
- `api.ts` (`I<Feature>Api` + `<Feature>Api` + factory)
- `api.runtime.ts` (singleton re-export for testability)
- `hooks.ts` (query adapter)
- `schemas.ts` (zod schemas + derived types)

Recommended files:

- `helpers.ts` for small pure transforms
- `types.ts` for non-DTO feature-owned types

Optional (add when the feature's complexity justifies them):

- `sync.ts` for multi-query cache invalidation orchestration
- `realtime-api.ts` + `realtime-api.runtime.ts` for Supabase realtime subscriptions
- `query-options.ts` for TanStack Query `queryOptions()` factories (RSC/prefetch)
- `stores/` for client coordination state (Zustand — co-located with the feature)
- `machines/` for XState state machines (complex UI interaction logic)
- `hooks/` sub-folder when root `hooks.ts` becomes too large

Domain transform precedence:

- prefer `lib/modules/<module>/shared/domain.ts` for cross-runtime reusable logic
- keep `src/features/<feature>/domain.ts` or `helpers.ts` for feature-local pure logic

Tests for these files go in `src/__tests__/features/<feature>/` — never colocated.
See Testing Layout below and `client/core/testing.md`.

## Ownership Boundaries by Path

- `src/features/<feature>/api.ts`: endpoint-scoped data access for one feature via `I<Feature>Api` + class implementation.
- `src/features/<feature>/api.runtime.ts`: singleton re-export for test mocking.
- `src/features/<feature>/hooks.ts`: query/mutation/cache behavior.
- `src/features/<feature>/sync.ts`: multi-query cache invalidation orchestration.
- `src/features/<feature>/components/*`: composition + rendering only.
- `src/features/<feature>/stores/*`: Zustand stores (co-located with feature).
- `src/features/<feature>/machines/*`: XState state machines.
- `src/common/query-keys/*`: cross-feature cache key contracts (plain keys for non-tRPC adapters; `buildTrpcQueryKey` only for tRPC-wrapper interop).
- `src/common/errors/*`: `AppError` contract + normalization adapters/facades (including `adapters/trpc.ts`).
- `src/common/toast/*`: toast abstraction with typed methods (`success`, `error`, `info`, `warning`), provider + adapter for sonner.
- `src/common/logging/*`: logger interface + strategy selector + pluggable adapters (console, noop, debug) + decorator wrappers (context injection, redaction, sampling) + `feature.ts` for feature-scoped loggers.
- `src/common/clients/*`: non-tRPC API client wrappers for external APIs and realtime channels. Each client folder has `index.ts` (client), optional `query-keys.ts` and `schemas.ts`.
- `src/common/feature-api-hooks.ts`: `useFeatureQuery`, `useFeatureMutation`, `useFeatureQueryCache` wrappers.

## Testing Layout

Tests live in `src/__tests__/` and **mirror the source tree exactly**. Never colocate test files next to source files.

```text
src/
  __tests__/
    features/
      <feature>/
        api.test.ts       # mock callTrpcQuery/callTrpcMutation, assert class behavior
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
