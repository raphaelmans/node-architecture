# Query Keys (Query Key Factory)

TanStack Query cache behavior depends on **stable query keys**.

We use `@lukemorales/query-key-factory` as the **single source of truth** for query keys.

Reference: https://github.com/lukemorales/query-key-factory

## Why keys live in `common/`

Store keys in `src/common/query-keys/<feature>.ts` so that:

- query adapters can use them consistently
- cross-feature components (shared widgets, nav, dashboards) can invalidate/refetch without importing feature internals

## Where to put keys

```
src/common/query-keys/
  <feature>.ts
```

## Pattern

```typescript
// src/common/query-keys/profile.ts

import { createQueryKeys } from "@lukemorales/query-key-factory";

export const profileQueryKeys = createQueryKeys("profile", {
  all: null,

  // Instance key
  current: null,
  byId: (id: string) => [id],

  // Collection key (example)
  list: (filters: { q?: string }) => [{ filters }],
});
```

This generates (examples):

- `profileQueryKeys._def` -> `["profile"]`
- `profileQueryKeys.byId._def` -> `["profile", "byId"]`
- `profileQueryKeys.byId(id).queryKey` -> `["profile", "byId", id]`

## Using With TanStack Query

### Invalidate a scope

```typescript
await queryClient.invalidateQueries({
  queryKey: profileQueryKeys.list._def,
});
```

### Cache update from a mutation

```typescript
queryClient.setQueryData(
  profileQueryKeys.byId(profileId).queryKey,
  updatedProfile,
);
```

## Rules

- Keys must be serializable and stable.
- Prefer `._def` for invalidation scopes and `mutationKey`.
- Keep keys **key-only** (no `queryFn`) if you want to preserve strict boundaries:
  `queryFn` lives in the query adapter layer, not next to the key definition.
