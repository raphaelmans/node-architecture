# Client Architecture Conventions (Agnostic)

Core conventions that should remain valid if we swap frameworks.

## Layer Responsibilities

### Route Layer (Metaframework-Owned)

Owns:

- route entrypoints (pages)
- layout composition
- SSR/RSC behavior
- param/searchParam parsing

Does not own:

- feature business logic
- transport/caching rules

### Feature Business Layer

Owns:

- composing sections and flows
- loading/error wiring
- form orchestration
- calling the query adapter

Does not own:

- transport (HTTP/tRPC)
- cache invalidation rules

### Query Adapter Layer (Server State + Cache)

Owns:

- query/mutation definitions
- query keys (for non-tRPC adapters, defined in `src/common/query-keys/<feature>.ts`)
- cache utilities/invalidation (for tRPC adapters, via generated tRPC query utilities)
- invalidation / optimistic updates
- combined loading/success/error composition for multiple query units

Depends on:

- `featureApi` (not transport)

### Presentation Layer

Owns:

- render-only UI (fields/cards/lists)

Does not own:

- fetching/mutations
- navigation/route parsing

## Execution Decision Flows

### 1) Where should logic go?

Use this decision chain:

1. Is this transport-specific (HTTP/tRPC/auth headers/retry wiring)?
   - Put in `clientApi` or metaframework boundary docs.
2. Is this endpoint-scoped request/response orchestration?
   - Put in `src/features/<feature>/api.ts` (`featureApi`).
3. Is this cache/query behavior (keys, invalidation, optimistic update)?
   - Put in `src/features/<feature>/hooks.ts` (query adapter).
4. Is this pure domain rule or deterministic transformation?
   - Put in `domain.ts` or `helpers.ts`.
5. Is this render-only?
   - Keep in presentation component.

### 2) Should it live in `feature` or `common`?

1. Used by multiple features and no feature ownership? Put in `src/common/*`.
2. Owned by one feature even if reused nearby? Keep in that feature.
3. Reusable across server + client for one module? Use `src/lib/modules/<module>/shared/*` first.

## Feature Module File Boundaries

In `src/features/<feature>/`:

- `hooks.ts`: query adapter (framework-specific)
- `api.ts`: `I<Feature>Api` contract + `<Feature>Api` class + `create<Feature>Api` factory
- `schemas.ts`: Zod schemas + derived types + DTO-to-feature mapping helpers
- `types.ts`: shared feature types (non-DTO)
- `domain.ts`: business rules (pure, deterministic)
- `helpers.ts`: small pure utilities (formatting, grouping, transforms)

## Feature API Contract (Required)

For each feature API:

- define `I<Feature>Api` first
- implement `class <Feature>Api implements I<Feature>Api`
- expose `create<Feature>Api(deps)` factory

Dependency rules:

- inject transport boundary (`clientApi`)
- inject error normalizer (`toAppError`)
- inject optional deterministic utilities only when needed (`clock`, `idFactory`)

Testing rules:

- unit test class behavior by mocking injected dependencies
- query adapter tests mock `I<Feature>Api` (not transport providers)
- domain helpers stay function-based and are tested without mocks
- all test files live in `src/__tests__/` mirroring the source tree (never colocated)

Full standard: `client/core/testing.md`.

## Domain Logic Placement (Precedence)

When you need domain-specific rules or transformations:

1. Prefer module-owned shared code (reusable across server + client): `src/lib/modules/<module>/shared/*`
2. Otherwise keep it client-only in the feature: `src/features/<feature>/(domain.ts|helpers.ts)`

More details: `client/core/domain-logic.md`.

## Key Rules

- Components never talk to HTTP directly.
- Cache rules live in the query adapter layer.
- Zod parses at boundaries (recommended).
- Hook/query units follow single responsibility.

## Non-Blocking Side Effects

Treat telemetry/analytics and other best-effort side effects as non-blocking:

- never block submit/navigation UX on non-critical side effects
- swallow/report failures appropriately
- keep business-critical workflows independent from telemetry success

## Transport Guard Boundaries

Security and transport controls belong at metaframework/server boundaries, not in presentation components:

- CSRF/origin checks
- rate limiting
- request correlation metadata attachment (`requestId`, optional path metadata)

## Naming Conventions (Core Contracts)

Feature files:

- `api.ts`: `I<Feature>Api` + `<Feature>Api` + factory
- `hooks.ts`: query adapter hooks (framework-specific implementation)
- `schemas.ts`: zod schemas + derived types + mapping helpers
- `domain.ts`: pure domain logic
- `helpers.ts`: small pure transforms

Hook naming (for hook-based frameworks):

- Single-responsibility query hook: `useQuery<Feature><Noun>`
- Single-responsibility mutation hook: `useMut<Feature><Verb>`
- Composed hook (multiple query/mutation units): `useMod<DescriptiveName>`

Rules:

- `useQuery*` / `useMut*` must each own one server-state responsibility.
- Composition belongs in `useMod*`, not in a single query/mutation hook.
- Feature API classes stay in `api.ts` behind `I<Feature>Api`.
- `domain.ts` / `helpers.ts` remain function-based (no feature API classes there).

## Import and Colocation Rules

Import order:

1. framework/runtime imports
2. external packages
3. internal absolute imports (`@/...`)
4. relative imports

Colocation:

- Keep feature-owned logic in `src/features/<feature>/*`.
- Move only genuinely cross-feature contracts to `src/common/*`.
- Do not colocate transport code in presentation folders.

## PR Review Checklist (Client Core)

- [ ] Layer ownership is respected (route vs business vs query adapter vs presentation)
- [ ] No direct transport calls from presentation components
- [ ] Query/cache behavior is centralized in query adapter layer
- [ ] Hook names follow `useQuery*` / `useMut*` / `useMod*` convention
- [ ] `api.ts` follows `I<Feature>Api` + `<Feature>Api` + factory contract
- [ ] Query adapters depend on `I<Feature>Api` (not direct transport clients)
- [ ] Domain transforms follow precedence (`lib/modules/<module>/shared` first, then feature-local)
- [ ] `domain.ts` / `helpers.ts` tests are pure (no mocks)
- [ ] `api.ts` unit tests mock injected dependencies (`clientApi`, `toAppError`)
- [ ] Test files are in `src/__tests__/` mirroring source tree (not colocated)
- [ ] Shared contracts are in `src/common/*` only when truly cross-feature
