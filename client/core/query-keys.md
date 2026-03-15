# Query Keys

TanStack Query cache behavior depends on **stable query keys**.

## Strategy

### 1) Direct tRPC Hooks (`@trpc/react-query`)

When a feature uses direct `trpc.*.useQuery/useMutation`, use tRPC-generated keys and utilities (`trpc.useUtils()`) as the default invalidation path.

### 2) `IFeatureApi` Wrappers Backed by tRPC

Features using the `IFeatureApi` pattern with tRPC use `buildTrpcQueryKey` to construct keys that match tRPC's internal key format:

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
  byId: (id: string) => ["feature", "byId", id] as const,
  list: (filters: Filters) => ["feature", "list", filters] as const,
};
```

## Why keys live in `common/`

Store keys in `src/common/query-keys/<feature>.ts` so that:

- query adapters can use them consistently
- cross-feature components (shared widgets, nav, dashboards) can invalidate/refetch without importing feature internals

## Where to put keys

```
src/common/query-keys/
  shared.ts           # normalizeString, serializeStableScope utilities
  <feature>.ts        # per-feature key definitions
```

## Input Normalization

Query key inputs must be normalized for cache stability. Use `normalizeString` (trim + lowercase) and `serializeStableScope` (JSON.stringify with sorted keys) to prevent cache misses from whitespace, case, or key-order differences:

```typescript
// src/common/query-keys/shared.ts
export function normalizeString(s: string): string;
export function serializeStableScope(obj: Record<string, unknown>): string;
```

Apply these in key builder functions, not at call sites.

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
- Normalize inputs before embedding in keys.
- Keep keys **key-only** (no `queryFn`) — `queryFn` lives in the query adapter layer.
- Invalidation patterns:
  1. `trpc.useUtils()` for direct tRPC procedures
  2. `buildTrpcQueryKey(...)` for `IFeatureApi` wrappers backed by tRPC
  3. plain key objects for non-tRPC adapters
  4. `useModFeatureSync()` for orchestrated multi-query invalidation (see `client/core/client-api-architecture.md`)
