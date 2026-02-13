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
- form orchestration (conceptually)
- calling the query adapter

Does not own:

- transport (HTTP/tRPC)
- cache invalidation rules

### Query Adapter Layer (Server State + Cache)

Owns:

- query/mutation definitions
- query keys
- invalidation / optimistic updates

Depends on:

- `featureApi` (not transport)

### Presentation Layer

Owns:

- render-only UI (fields/cards/lists)

Does not own:

- fetching/mutations
- navigation/route parsing

## Feature Module File Boundaries

In `src/features/<feature>/`:

- `hooks.ts`: query adapter (framework-specific)
- `api.ts`: `featureApi` implementation (endpoint-scoped; depends on `clientApi`)
- `dtos.ts`: DTO schemas/types + DTO-to-feature mapping helpers
- `types.ts`: shared feature types (non-DTO)
- `domain.ts`: business rules (pure, deterministic)
- `helpers.ts`: small pure utilities (formatting, grouping, transforms)

## Key Rules

- Components never talk to HTTP directly.
- Cache rules live in the query adapter layer.
- Zod parses at boundaries (recommended).

