# Folder Structure (Agnostic)

This document describes framework-agnostic client directory conventions. The trees below are the single-project topology mapping; [monorepo architecture](../../monorepo/core/architecture.md) maps the same roles to deployable apps and activated packages.

## High-Level Structure

```text
src/
  <routes>/            # Metaframework-owned routes (Next.js: app/)
  common/              # App-wide shared utilities
    errors/            # AppError contract + adapters/facades
    query-keys/        # Server-state cache keys (cross-feature)
    toast/             # Toast facade + provider adapters
    logging/           # AppLogger + context/redaction/sampling + debug/Sentry adapters
    analytics/         # Typed ProductAnalytics + consent/identity + vendor adapters
    runtime/           # Browser/request composition roots; owns infrastructure lifecycle
    clients/           # Non-tRPC API client wrappers (HTTP + realtime)
  components/          # Shared UI components
  features/            # Feature modules (primary unit of organization)
  hooks/               # Global framework hooks (React only)
  lib/
    modules/<module>/shared/
      contracts/       # Canonical client/server Zod wire contracts
      domain.ts        # Optional cross-runtime pure domain logic
```

## Topology Mapping

| Client role | Single-project topology | Monorepo topology |
| --- | --- | --- |
| Client routes/features/common infrastructure | `src/*` | `apps/<client>/src/*` |
| Shared wire contracts | `src/lib/modules/<module>/shared/contracts/*` | `packages/contracts/<module>/*` when the contract crosses packages |
| Shared pure domain rules | `src/lib/modules/<module>/shared/*` | `packages/domain/<module>/*` only when genuinely cross-runtime/package |
| Shared UI | `src/components/*` | `packages/ui/<system>/*` only when multiple client apps consume it |
| Client composition root | `src/common/runtime/*` | Remains owned by `apps/<client>` |

Do not extract app-local feature code merely because a workspace exists. Cross-package creation, manifests, exports, and dependency edges follow the [monorepo scaffolding contract](../../monorepo/core/scaffolding.md).

Metaframework-specific routing conventions:

- Next.js: `client/frameworks/reactjs/metaframeworks/nextjs/folder-structure.md`

## Feature Module Structure

```text
src/features/<feature>/
  components/
    <feature>-view.tsx          # business component (composition + wiring)
    <feature>-fields.tsx        # presentation components (render-only)
  api.ts                        # I<Feature>Api + <Feature>Api class + factory
  api.runtime.ts                # re-exports composition-root-owned API accessor (stable mock target)
  hooks.ts                      # query adapter (framework-specific)
  schemas.ts                    # UI/form schemas composed from shared contracts
  types.ts                      # non-DTO types
  helpers.ts                    # DTO mapping + small pure helpers
```

## Feature Starter Contract

Required files for a new feature:

- `components/<feature>-view.tsx` (business wiring/composition)
- `components/<feature>-fields.tsx` (presentation-only UI, if form/field heavy)
- `api.ts` (`I<Feature>Api` + `<Feature>Api` + factory)
- `api.runtime.ts` (composition-root-owned API accessor for testability)
- `hooks.ts` (query adapter)
- `schemas.ts` (UI/form schemas composed from shared input contracts)

Recommended files:

- `helpers.ts` for small pure transforms
- `types.ts` for non-DTO feature-owned types

Optional (add when the feature's complexity justifies them):

- `sync.ts` for multi-query cache invalidation orchestration
- `realtime-api.ts` + `realtime-api.runtime.ts` for provider-neutral feature realtime subscriptions
- `query-options.ts` for TanStack Query `queryOptions()` factories (RSC/prefetch)
- `stores/` for client coordination state (Zustand — co-located with the feature)
- `machines/` for XState state machines (complex UI interaction logic)
- `hooks/` sub-folder when root `hooks.ts` becomes too large

Domain transform precedence (using the resolved topology mapping):

- import public API schemas/types from `lib/modules/<module>/shared/contracts/`
- prefer `lib/modules/<module>/shared/domain.ts` for cross-runtime reusable logic
- keep `src/features/<feature>/domain.ts` or `helpers.ts` for feature-local pure logic

Tests for these files go in `src/__tests__/features/<feature>/` — never colocated.
See Testing Layout below and `client/core/testing.md`.

## Ownership Boundaries by Path

- `src/features/<feature>/api.ts`: endpoint-scoped data access for one feature via `I<Feature>Api` + class implementation.
- Resolved shared-contract boundary: single source for serialized API request/response schemas and inferred types; use the local module path in one project or an activated contract package when cross-package.
- `src/features/<feature>/schemas.ts`: client-only form/UI schemas; may compose shared input contracts but must not redefine wire responses.
- `src/features/<feature>/types.ts`: client models/view models; never ORM entities.
- `src/features/<feature>/api.runtime.ts`: stable re-export of a composition-root-owned API accessor for test mocking; it does not construct the instance.
- `src/features/<feature>/hooks.ts`: query/mutation/cache behavior.
- `src/features/<feature>/sync.ts`: multi-query cache invalidation orchestration.
- `src/features/<feature>/realtime-api.ts`: provider payload validation/mapping into feature domain events behind `I<Feature>RealtimeApi`.
- `src/features/<feature>/components/*`: composition + rendering only.
- `src/features/<feature>/stores/*`: Zustand stores (co-located with feature).
- `src/features/<feature>/machines/*`: XState state machines.
- `src/common/query-keys/*`: cross-feature cache key contracts (plain keys for non-tRPC adapters; `buildTrpcQueryKey` only for tRPC-wrapper interop).
- `src/common/errors/*`: `AppError` contract + normalization adapters/facades (including `adapters/trpc.ts`).
- `src/common/toast/*`: provider-neutral `ToastFacade.show({ variant, ... })` contract plus provider adapter.
- `src/common/logging/*`: OpenTelemetry-shaped `AppLogger` + contextual wrappers + local `debug` and optional remote Sentry adapters.
- `src/common/analytics/*`: typed `ProductAnalytics` + consent/identity lifecycle + debug/noop/vendor/composite adapters.
- `src/common/runtime/*`: composition roots that call infrastructure factories and own browser/request lifetimes; never imported as a service locator.
- `src/common/clients/*`: non-tRPC API client wrappers for external APIs and realtime channels. Provider-private schemas may live with the adapter; canonical TanStack keys remain in `src/common/query-keys/*`.
- `src/common/trpc-feature-api-hooks.ts`: optional tRPC-interoperability wrappers for `IFeatureApi` query adapters; non-tRPC adapters use plain keys directly.

## Testing Layout

Tests live in `src/__tests__/` and **mirror the source tree exactly**. Never colocate test files next to source files.

```text
src/
  __tests__/
    features/
      <feature>/
        api.test.ts       # mock injected IClientApi/toAppError/logger, assert class behavior
        hooks.test.ts     # mock I<Feature>Api, assert query/invalidation behavior
        domain.test.ts    # pure table-driven tests (no mocks)
        helpers.test.ts   # pure table-driven tests (no mocks)
    common/
      errors/
        error-adapter.test.ts
      logging/
        logger.test.ts
        adapters/
          debug.test.ts
          sentry.test.ts
      analytics/
        analytics.test.ts
      runtime/
        browser.test.ts
    lib/
      modules/
        <module>/
          shared/
            contracts/
              <capability>.contract.test.ts
            domain.test.ts
```

Full testing standard: `client/core/testing.md`.

## Cross-Feature Promotion Rules

Promote from feature-local to `src/common/*` only when all are true:

1. used in multiple features
2. not owned by one domain workflow
3. stable API contract is clear

Otherwise keep it in the feature module.
