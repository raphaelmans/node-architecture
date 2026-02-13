# Client API Architecture (clientApi -> featureApi -> query adapter)

Define the standard way the client calls backend endpoints with strict separation of concerns, DI-friendly boundaries, and predictable cache behavior.

## Core Rule

Components never talk to HTTP directly.

All IO happens through this chain:

`components -> query adapter -> featureApi -> clientApi -> network`

## Layers

### 1) `clientApi` (transport + cross-cutting concerns)

Owns:

- HTTP client wrapper (`fetch`/`ky`/`axios`-style)
- base URL, headers/auth attachment
- standard response envelope decoding
- typed, inspectable errors
- global retry/timeouts (if any)

Does not own:

- endpoint-specific paths
- domain logic
- cache logic

Example surface:

- `clientApi.get<T>(path, options)`
- `clientApi.post<T>(path, body, options)`

### 2) `featureApi` (endpoint-scoped API)

One module per feature domain:

- `profileApi`: profile endpoints only
- `billingApi`: billing endpoints only

Owns:

- endpoint paths for that domain
- request/response DTO typing and parsing (Zod)
- mapping DTO -> feature model (pure helpers)

Depends on:

- injected `clientApi` (interfaces for strategy/adapters and testing doubles)

Does not own:

- cache logic

### 3) Query adapter (server state + cache management)

Owns:

- query/mutation definitions
- query keys
- invalidation / optimistic updates

Depends on:

- `featureApi` (not `clientApi`)

Does not own:

- endpoint paths

### 4) Components

Own:

- UI composition, loading/error wiring, form orchestration

Do not own:

- queries/mutations definitions
- transport/IO logic

## File Layout (Feature Module)

Recommended feature module layout:

```text
src/features/<feature>/
  hooks.ts       # query adapter (React: TanStack Query hooks + cache ops)
  api.ts         # featureApi (depends on clientApi)
  schemas.ts     # Zod schemas + derived types + mapping helpers
  types.ts       # feature types (non-DTO)
  domain.ts      # business rules
  helpers.ts     # small pure utilities
  components/    # business + presentation components
```

## Conventions

- Zod parse at boundaries: `featureApi` parses responses and returns safe data.
- Cache rules live in the query adapter: invalidation/optimistic updates never live in components.
- Avoid “big data providers”: share server data via query cache + query keys.
