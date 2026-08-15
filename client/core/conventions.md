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
- UI/workflow product events when the business component owns the occurrence

Does not own:

- transport (HTTP/tRPC)
- reusable cache invalidation rules or direct query-key mechanics
- direct logging or analytics vendor calls

A screen/business coordinator may own route-local sequencing such as `mutate -> sync -> navigate`, but it calls an exported query/cache-sync operation from the query adapter rather than inlining `queryClient` keys in TSX. Presentation components never coordinate cache operations.

### Query Adapter Layer (Server State + Cache)

Owns:

- query/mutation definitions
- query keys (for non-tRPC adapters, defined in `src/common/query-keys/<feature>.ts`)
- reusable cache utilities/invalidation (for tRPC adapters, via generated tRPC query utilities)
- route-local cache-sync operations exposed to screen/business coordinators
- invalidation / optimistic updates
- combined loading/success/error composition for multiple query units
- successful mutation product events when the mutation hook owns the reusable action

Depends on:

- `featureApi` (not transport)
- injected/facade `ProductAnalytics` when the hook emits a typed event

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
3. Is this a serialized request/response contract shared with the server?
   - Put it in `src/lib/modules/<module>/shared/contracts/`.
4. Is this an operational transport log or correlation field?
   - Emit through `AppLogger` at `clientApi`; enrich context in the logging adapter.
5. Is this a contract parsing/mapping diagnostic?
   - Emit through injected `AppLogger` in `featureApi` without re-logging the transport failure.
6. Is this a product event for a successful reusable mutation?
   - Emit through typed `ProductAnalytics` in the mutation/workflow owner after success.
7. Is this cache/query behavior (keys, invalidation, optimistic update)?
   - Put in `src/features/<feature>/hooks.ts` (query adapter).
8. Is this pure domain rule or deterministic transformation?
   - Put in `domain.ts` or `helpers.ts`.
9. Is this render-only?
   - Keep in presentation component.

### 2) Should it live in `feature` or `common`?

1. Used by multiple features and no feature ownership? Put in `src/common/*`.
2. Owned by one feature even if reused nearby? Keep in that feature.
3. A request/response contract used by client and server? Use `src/lib/modules/<module>/shared/contracts/*` even when only one feature consumes it.
4. Other logic reusable across server + client for one module? Use `src/lib/modules/<module>/shared/*` first.

### 3) Does it need a factory?

Use a factory for dependency-heavy infrastructure with swappable adapters or runtime lifecycle:

- `createAppLogger`
- `createProductAnalytics`
- `createClientApi`
- `create<Feature>Api`

Assemble factories once in the client composition root. Browser dependencies are application-scoped. SSR dependencies are request-scoped only when they capture request context. Inject specific ports, never the complete runtime container.

Do not add factories for React components, Zod schemas, pure helpers, or simple hooks.

## Feature Module File Boundaries

In `src/features/<feature>/`:

- `hooks.ts`: query adapter (framework-specific)
- `api.ts`: `I<Feature>Api` contract + `<Feature>Api` class + `create<Feature>Api` factory
- `schemas.ts`: client-only form/UI schemas composed from shared input contracts
- `types.ts`: shared feature types (non-DTO)
- `domain.ts`: business rules (pure, deterministic)
- `helpers.ts`: DTO-to-feature-model mapping and small pure utilities

## Feature API Contract (Required)

For each feature API:

- define `I<Feature>Api` first
- implement `class <Feature>Api implements I<Feature>Api`
- expose `create<Feature>Api(deps)` factory

Dependency rules:

- inject transport boundary (`clientApi`)
- inject error normalizer (`toAppError`)
- inject `AppLogger` only when the feature API emits boundary-owned diagnostics
- inject optional deterministic utilities only when needed (`clock`, `idFactory`)

Testing rules:

- unit test class behavior by mocking injected dependencies
- query adapter tests mock `I<Feature>Api` (not transport providers)
- domain helpers stay function-based and are tested without mocks
- all test files live in `src/__tests__/` mirroring the source tree (never colocated)

Full standard: `client/core/testing.md`.

## Domain Logic Placement (Precedence)

When you need domain-specific rules or transformations:

1. API request/response contract: `src/lib/modules/<module>/shared/contracts/*`
2. Other module-owned shared code: `src/lib/modules/<module>/shared/*`
3. Client-only logic: `src/features/<feature>/(domain.ts|helpers.ts)`

More details: `client/core/domain-logic.md`.

## Key Rules

- Components never talk to HTTP directly.
- Cache rules live in the query adapter layer.
- Client and server import one shared Zod wire contract; client-only schemas compose it rather than copy it.
- Zod parses at both network boundaries.
- Hook/query units follow single responsibility.

## Operational Logging and Product Analytics

Use separate ports:

- `AppLogger`: operational diagnostics; `debug` is the local browser sink and Sentry may be a filtered remote sink
- `ProductAnalytics`: typed user/business behavior with consent-aware vendor adapters

Rules:

- never block submit/navigation UX on non-critical side effects
- keep provider SDKs behind adapters
- enrich correlation/context at boundaries; do not add telemetry fields to business DTOs
- assign one owner per failure to prevent duplicate reporting
- emit completion analytics only after the meaningful operation succeeds
- keep business-critical workflows independent from telemetry success

Critical durable business facts belong in the server-side analytics/outbox flow, not browser-only analytics.

## Transport Guard Boundaries

Security and transport controls belong at metaframework/server boundaries, not in presentation components:

- CSRF/origin checks
- rate limiting
- request correlation metadata attachment (`requestId`, optional path metadata)

## Naming Conventions (Core Contracts)

Feature files:

- `api.ts`: `I<Feature>Api` + `<Feature>Api` + factory
- `hooks.ts`: query adapter hooks (framework-specific implementation)
- `schemas.ts`: client-only form/UI schemas composed from shared input contracts
- `domain.ts`: pure domain logic
- `helpers.ts`: DTO-to-feature-model mapping + small pure transforms

Hook naming (for hook-based frameworks):

- Single-responsibility query hook: `useQuery<Feature><Noun>`
- Single-responsibility mutation hook: `useMut<Feature><Verb>`
- Composed hook (multiple query/mutation units): `useMod<DescriptiveName>`

Rules:

- `useQuery*` / `useMut*` must each own one server-state responsibility.
- Composition belongs in `useMod*`, not in a single query/mutation hook.
- Feature API classes stay in `api.ts` behind `I<Feature>Api`.
- Provider/vendor construction and singleton lifecycle stay in the composition root, not feature modules.
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
- [ ] Feature code imports `AppLogger` / `ProductAnalytics` ports, never provider SDKs
- [ ] Operational records use stable event names and typed primitive attributes
- [ ] Product events are typed and emitted only by the occurrence owner
- [ ] Telemetry context is absent from business DTOs and ordinary method parameters
- [ ] The same error is not reported by multiple client layers
- [ ] Dependency-heavy infrastructure uses factories assembled by one composition root
- [ ] Consumers receive specific ports rather than a runtime/service-locator container
- [ ] Browser and request-contextual SSR lifetimes are explicit
- [ ] Domain transforms follow precedence (`lib/modules/<module>/shared` first, then feature-local)
- [ ] `domain.ts` / `helpers.ts` tests are pure (no mocks)
- [ ] `api.ts` unit tests mock injected dependencies (`clientApi`, `toAppError`, logger when used)
- [ ] Test files are in `src/__tests__/` mirroring source tree (not colocated)
- [ ] Shared contracts are in `src/common/*` only when truly cross-feature
