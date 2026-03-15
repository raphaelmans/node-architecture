# Server State (TanStack Query)

TanStack Query is treated as **core infrastructure** for server/IO state.

Query key conventions live in `client/core/query-keys.md`.

## Core Rules

- Share async/IO data via the query cache, not via “big data providers”.
- Keep cache rules (query keys, invalidation, optimistic updates) in one dedicated layer.
- Components do not inline cache logic.
- Keep query/mutation units single-responsibility.
- Query adapters depend on `I<Feature>Api` contracts, not transport clients.
- Preserve error normalization boundaries (`unknown -> AppError`) before UI handling.

## Query Lifecycle Patterns

### Basic Query Unit

- One hook/query unit owns one data concern.
- Keep selection/normalization near query adapter, not inside presentation components.

### Dependent Queries

Use dependency guards so downstream queries run only when upstream prerequisites exist.

Rule:

- Gate with explicit dependency checks (for example, “id exists”, “auth context ready”).

### Parallel Queries

Independent concerns should run in parallel, then optionally compose in a `useMod*` hook.

Rule:

- Do not merge independent fetch concerns into one oversized query hook.

### Combined Loading and Error State

When composing multiple query units:

- aggregate loading/error in composition layer (`useMod*` or feature business component)
- keep original query units unchanged and reusable

## Mutation Lifecycle Patterns

### Mutation Unit Ownership

- A mutation hook owns one write concern.
- Post-mutation cache behavior stays in query adapter layer.

### Invalidation Batching

Rules:

- Group related invalidations in one dedicated helper (for example `onSubmitInvalidateQueries`).
- Invalidate in parallel when multiple keys/scopes are affected.
- Prefer deterministic key scopes over broad cache wipes.

### Optimistic Update Guardrails

Use optimistic updates only when rollback can be defined safely.

Minimum requirements:

- snapshot previous cache value
- apply optimistic patch
- rollback on failure
- always revalidate affected keys after mutation settles

If rollback semantics are unclear, skip optimistic update and use explicit invalidation.

### Post-Mutation Navigation Ordering

Default order:

1. run mutation
2. run required invalidations (parallel where possible)
3. then navigate

Exception:

- If UX requires immediate navigation, document the tradeoff and ensure destination can tolerate stale cache briefly.

## Cache Ownership Rules

- Query key definitions live in dedicated key modules.
- Invalidation helpers live next to query adapter hooks, not in view components.
- Cache updates should reference stable keys/contracts, never ad-hoc arrays inside UI code.

## Anti-Patterns

- Storing server entities in client stores as primary source of truth.
- Calling `invalidateQueries` directly from presentation components.
- A “god hook” that fetches unrelated concerns and mutates multiple domains.
- Inline DTO parsing in render paths.

## Immer for Cache Patching

Use Immer's `produce` for all TanStack Query cache updates to preserve immutability guarantees:

```typescript
import { produce } from "immer";

queryClient.setQueryData(queryKey, (old) =>
  old
    ? produce(old, (draft) => {
        const item = draft.items.find((i) => i.id === updatedId);
        if (item) {
          item.status = newStatus;
          item.updatedAt = now;
        }
      })
    : old,
);
```

Rules:

- Always use `produce` — never spread/clone manually for nested updates
- Immer patches are used in both optimistic updates and realtime event-carried state transfer
- Keep patch functions small and focused on one concern

## Optimistic Updates

For mutations where immediate UI feedback matters:

```typescript
const mutation = useFeatureMutation(api.mutUpdateItem, {
  onMutate: async (input) => {
    // 1. Cancel in-flight refetches
    await queryClient.cancelQueries({ queryKey });

    // 2. Snapshot previous value
    const previous = queryClient.getQueryData(queryKey);

    // 3. Apply optimistic patch (Immer)
    queryClient.setQueryData(queryKey, (old) =>
      old
        ? produce(old, (draft) => {
            draft.name = input.name;
          })
        : old,
    );

    return { previous };
  },
  onError: (_err, _input, context) => {
    // 4. Rollback on failure
    if (context?.previous) {
      queryClient.setQueryData(queryKey, context.previous);
    }
  },
  onSettled: () => {
    // 5. Always revalidate after settle
    queryClient.invalidateQueries({ queryKey });
  },
});
```

Rules:

- Snapshot before patching — rollback must restore exact previous state
- Always invalidate after settle (success or failure) for truth reconciliation
- Skip optimistic updates when rollback semantics are unclear

## Pagination

### Offset-Based Pagination

For paginated lists, use `keepPreviousData` to prevent layout shift:

```typescript
const [page, setPage] = useQueryState("page", parseAsInteger.withDefault(1));

const query = useFeatureQuery(
  ["items", "list"],
  () => api.queryItemsList({ page, limit: 25 }),
  { page, limit: 25 },
  { placeholderData: keepPreviousData },
);
```

### Infinite Scroll

For infinite lists, use `useInfiniteQuery`:

```typescript
const query = useInfiniteQuery({
  queryKey: buildTrpcQueryKey(["items", "listInfinite"], filters),
  queryFn: ({ pageParam }) => api.queryItemsList({ cursor: pageParam, limit: 25 }),
  getNextPageParam: (lastPage) => lastPage.nextCursor,
  initialPageParam: undefined,
});
```

Rules:

- Pagination state lives in URL params (nuqs) for offset-based, in query state for cursor-based
- Use `keepPreviousData` / `placeholderData` to avoid flash-of-empty on page transitions
- Invalidation invalidates the entire list scope, not individual pages

## Search Debounce

Debounce search input before feeding it to queries:

```typescript
const [search, setSearch] = useQueryState("q", parseAsString.withDefault(""));
const debouncedSearch = useDebounce(search, 300);

const query = useFeatureQuery(
  ["items", "search"],
  () => api.queryItemsSearch({ q: debouncedSearch }),
  { q: debouncedSearch },
  { enabled: debouncedSearch.length >= 2 },
);
```

Rules:

- Debounce at 300ms (default) — adjust based on API latency
- Use the raw (non-debounced) value for the input field, debounced value for the query
- Gate queries with `enabled` to avoid empty/short-string searches
- Search state lives in URL via nuqs (`parseAsString`) for shareability

## Filters with URL State

Combine nuqs URL state with query keys for filterable lists:

```typescript
const [status, setStatus] = useQueryState("status", parseAsStringLiteral(STATUSES));
const [sort, setSort] = useQueryState("sort", parseAsStringLiteral(SORT_OPTIONS).withDefault("newest"));
const [search] = useQueryState("q", parseAsString.withDefault(""));
const debouncedSearch = useDebounce(search, 300);

const filters = useMemo(
  () => ({ status, sort, q: debouncedSearch }),
  [status, sort, debouncedSearch],
);

const query = useFeatureQuery(
  ["items", "list"],
  () => api.queryItemsList(filters),
  filters,
);
```

Rules:

- All filter state lives in URL params via nuqs (shareable, bookmarkable, back-button friendly)
- Use `history: "replace"` for filters (don't pollute browser history)
- Use `history: "push"` for tabs and modals (back button should work)
- Memoize the filter object to prevent unnecessary re-renders and refetches
- Debounce text inputs, not select/toggle filters

## Implementation Notes

Framework-specific examples and API signatures live in:

- React: `client/frameworks/reactjs/`
- Next.js + React: `client/frameworks/reactjs/metaframeworks/nextjs/`

Testing split:

- `api.ts` class tests mock `callTrpcQuery` / `callTrpcMutation`
- `hooks.ts` tests mock `I<Feature>Api`

Related docs:

- `client/core/realtime.md` — realtime event-carried state transfer pattern
- `client/core/query-keys.md` — key construction and invalidation patterns
