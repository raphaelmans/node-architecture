# Non-tRPC Query Keys (Query Key Factory)

> Standard query key conventions for TanStack Query when you are **not** using tRPC hooks.

## Why

When using raw HTTP clients (e.g., `ky` against Next.js `route.ts`), we still want:

- Standardized query keys
- Easy cache updates (`setQueryData`) and invalidation (`invalidateQueries`)
- Autocomplete + type safety

We use `@lukemorales/query-key-factory` as the single source of truth for keys.

## Where to put keys

Place keys next to the client:

```
src/shared/lib/clients/<client>/
├── index.ts       # client functions + hooks
└── query-keys.ts  # query key definitions
```

## Pattern

```typescript
// src/shared/lib/clients/google-loc-client/query-keys.ts

import { createQueryKeys } from "@lukemorales/query-key-factory";

export const googleLocQueryKeys = createQueryKeys("googleLoc", {
  all: null,
  preview: (url: string) => [url],
});
```

This generates:

- `googleLocQueryKeys._def` → `['googleLoc']` (invalidate everything)
- `googleLocQueryKeys.preview._def` → `['googleLoc', 'preview']` (invalidate all previews)
- `googleLocQueryKeys.preview(url).queryKey` → `['googleLoc', 'preview', url]`

## Using with React Query

### Cache update from a mutation

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { googleLocQueryKeys } from "@/shared/lib/clients/google-loc-client/query-keys";

const queryClient = useQueryClient();

useMutation({
  mutationKey: googleLocQueryKeys.preview._def,
  mutationFn: ({ url }: { url: string }) => googleLocClient.preview({ url }),
  onSuccess: (data, variables) => {
    queryClient.setQueryData(
      googleLocQueryKeys.preview(variables.url).queryKey,
      data,
    );
  },
});
```

### Invalidate a scope

```typescript
queryClient.invalidateQueries({
  queryKey: googleLocQueryKeys.preview._def,
});
```

## Notes

- Prefer key-only definitions in `query-keys.ts` and keep the actual `queryFn` inside the client.
- Use `._def` for invalidation scopes and `mutationKey`.
