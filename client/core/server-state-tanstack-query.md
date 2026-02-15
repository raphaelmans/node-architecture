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

## Implementation Notes

Framework-specific examples and API signatures live in:

- React: `client/frameworks/reactjs/`
- Next.js + React: `client/frameworks/reactjs/metaframeworks/nextjs/`

Testing split:

- `api.ts` class tests mock `clientApi` + `toAppError`
- `hooks.ts` tests mock `I<Feature>Api`
