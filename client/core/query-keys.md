# Query Keys

TanStack Query cache behavior depends on **stable query keys**.

## Strategy

### 1) Direct tRPC Hooks (`@trpc/react-query`)

When a feature uses direct `trpc.*.useQuery/useMutation`, use tRPC-generated keys and utilities (`trpc.useUtils()`) as the default invalidation path.

### 2) Optional `IFeatureApi` Wrappers Backed by tRPC

When an `IFeatureApi`-based query adapter is backed by tRPC and must interoperate with tRPC cache utilities, use `buildTrpcQueryKey` to construct keys that match tRPC's internal key format:

```typescript
// src/common/trpc-query-key.ts
export function buildTrpcQueryKey(
  path: string[],
  input?: unknown,
): QueryKey;
```

This produces keys in the shape `[[...splitPath], { input, type: "query" }]`, enabling interop with `trpc.useUtils()` invalidation calls.

### 3) Non-tRPC Adapters (`ky`, `fetch`, realtime clients)

For features that use non-tRPC adapters (REST clients, realtime subscriptions), define plain key objects:

```typescript
// src/common/query-keys/<feature>.ts
export const featureQueryKeys = {
  all: ["feature"] as const,
  lists: () => [...featureQueryKeys.all, "list"] as const,
  list: (filters: Filters) => [...featureQueryKeys.lists(), filters] as const,
  details: () => [...featureQueryKeys.all, "detail"] as const,
  detail: (id: string) => [...featureQueryKeys.details(), id] as const,
};
```

## Why keys live in `common/`

Store keys in `src/common/query-keys/<feature>.ts` so that:

- query adapters can use them consistently
- cross-feature query/cache-sync modules (shared widgets, nav, dashboards) can coordinate without importing feature internals

## Where to put keys

```
src/common/query-keys/
  shared.ts           # optional semantic normalization utilities
  <feature>.ts        # per-feature key definitions
```

## Input Normalization

TanStack Query hashes serializable object members deterministically, so object key order does not require custom sorting or serialization. Keep structured values in the key.

Normalize a value only when the server/domain treats multiple representations as the same input. For example, trim a search term if the endpoint also trims it. Do not lowercase IDs, case-sensitive search terms, or arbitrary user input merely for cache stability.

When semantic normalization is required, apply it in the key builder and the request mapping through one shared pure helper so the cache key describes the request that is actually sent.

## Using With TanStack Query

### Direct tRPC invalidation (preferred for direct tRPC procedures)

```typescript
const utils = trpc.useUtils();
await utils.reservation.getById.invalidate({ id });
```

### Wrapper-key invalidation (for `IFeatureApi` hooks backed by tRPC)

```typescript
await queryClient.invalidateQueries({
  queryKey: buildTrpcQueryKey(["reservation", "list"]),
});
```

### Non-tRPC key invalidation

```typescript
await queryClient.invalidateQueries({
  queryKey: featureQueryKeys.list(filters),
});
```

### Cache update from a mutation

```typescript
queryClient.setQueryData(
  buildTrpcQueryKey(["reservation", "getById"], { id }),
  updatedReservation,
);
```

## Rules

- Keys must be serializable and stable.
- Include every query-function dependency that changes the result.
- Apply only domain-approved semantic normalization; do not stringify structured key inputs.
- Keep keys **key-only** (no `queryFn`) — `queryFn` lives in the query adapter layer.
- Invalidation patterns:
  1. `trpc.useUtils()` for direct tRPC procedures
  2. `buildTrpcQueryKey(...)` only for `IFeatureApi` wrappers backed by tRPC that require interop
  3. plain key objects for non-tRPC adapters
  4. `useModFeatureSync()` for orchestrated multi-query invalidation (see `client/core/client-api-architecture.md`)
