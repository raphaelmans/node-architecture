# Server State Patterns (React)

> Comprehensive cookbook for TanStack Query usage in React features, aligned with `client/core/server-state-tanstack-query.md`.

## Purpose

This document shows **how** to apply core server-state contracts in React code with practical patterns.

Core contracts still live in:

- `client/core/server-state-tanstack-query.md`
- `client/core/conventions.md`

## Decision Matrix (Mixed Ownership)

Use this matrix when deciding where invalidation/cache orchestration should live.

| Situation | Preferred Pattern | Why |
| --- | --- | --- |
| Standard single-feature mutation | Hook-owned invalidation | Reusable, low duplication |
| Form flow with route-local orchestration (redirect/toast/local UI sequence) | Component-coordinator invalidation | Makes submit sequence explicit near UX flow |
| Edit/update form must reflect fresh external server data after save | Component-coordinator with explicit refetch | Deterministic post-submit UI state (same as refresh) |
| Mutation has base cache effects, component has extra route-local effects | Hybrid | Shared defaults + local orchestration |
| Legacy feature currently coordinating in component | Component-coordinator (transitional) | Keeps behavior stable while migrating incrementally |

## Pattern A: Hook-Owned Invalidation (Preferred Default)

Use when mutation effects are reusable across multiple components.

```ts
// src/features/profile/hooks.ts
export function useMutProfileUpdate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateProfile,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: profileQueryKeys.current._def }),
        queryClient.invalidateQueries({ queryKey: profileQueryKeys.detail._def }),
      ]);
    },
  });
}
```

Component:

```ts
const updateMut = useMutProfileUpdate();
await updateMut.mutateAsync(data);
router.push(appRoutes.dashboard);
```

## Pattern B: Component-Coordinator Invalidation (Allowed)

Use when the submit flow is route-local and sequencing is central to UX.

```ts
// src/features/profile/components/profile-form.tsx
const queryClient = useQueryClient();
const profileQuery = useQueryProfileCurrent();
const updateMut = useMutProfileUpdate();

const onSubmitInvalidateQueries = async () =>
  Promise.all([
    queryClient.invalidateQueries({ queryKey: profileQueryKeys.current._def }),
    queryClient.invalidateQueries({ queryKey: profileQueryKeys.detail._def }),
  ]);

const onSubmit = async (data: ProfileFormShape) => {
  await updateMut.mutateAsync(data);
  await onSubmitInvalidateQueries();
  await profileQuery.refetch();
  router.push(appRoutes.dashboard);
};
```

## Pattern C: Hybrid Ownership

Mutation hook handles shared invalidation; component handles route-local additions.

```ts
// hook: shared defaults
export function useMutProfileUpdate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateProfile,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: profileQueryKeys.current._def });
    },
  });
}

// component: route-local additions
const onSubmit = async (data: ProfileFormShape) => {
  await updateMut.mutateAsync(data);
  await queryClient.invalidateQueries({ queryKey: dashboardQueryKeys.summary._def });
  router.push(appRoutes.dashboard);
};
```

## Scenario Cookbook

### Create Form

- Usually hook-owned invalidation.
- Component handles success UX (toast/redirect).

### Edit Form

- Either hook-owned or component-coordinator.
- Button default: disable only during submit.
- Optional edit/update-only exception: disable when `!isDirty` for no-op prevention.
- For edit/update forms with external defaults, run explicit `onSubmitRefetch` (`query.refetch()`), then re-sync form defaults from refreshed `query.data`.

### Upload + Follow-Up Mutation

- Prefer hybrid:
  - upload mutation owns upload-related invalidation
  - component coordinates follow-up list/detail invalidations and navigation

### List + Detail Synchronization

- Keep list/detail keys explicit.
- Batch invalidation with `Promise.all`.
- Avoid broad invalidation when scoped keys are known.

### Dashboard Multi-Query Composition

- Use `useMod<Descriptive>` for combining multiple query units.
- Keep each underlying `useQuery*` single-responsibility.

## Guardrails

- Keep query/mutation units SRP (`useQuery*`, `useMut*`).
- Query hooks depend on `I<Feature>Api` contracts, not transport clients.
- Batch invalidation with `Promise.all` when multiple keys are required.
- For edit/update forms, keep query-data -> form reset logic in a dedicated sync hook (single responsibility).
- Use deterministic key scopes (`src/common/query-keys/*` for non-tRPC).
- Normalize errors to `AppError` before presentation logic branches.
- Keep transport checks out of presentation components.

## Testing Cookbook (React Query Layer)

### Query/Mutation Hook Tests

- mock `I<Feature>Api` (or factory return) as the data source
- assert query key usage, invalidation behavior, and status transitions
- avoid mocking transport providers directly (`fetch`, `axios`, `trpc` client internals)

### Feature API Tests

- unit test `class <Feature>Api` with mocked `clientApi` and `toAppError`
- assert schema parsing, DTO mapping, and error normalization handoff

### Domain/Helper Tests

- keep pure and table-driven (`domain.ts`, `helpers.ts`)
- no mocks needed

## Anti-Patterns

- Presentation component calling transport/query-library hooks directly.
- “God hook” combining unrelated domains.
- Ad-hoc key arrays repeated across components.
- Duplicating server entities into local stores as source of truth.

## Related Docs

- Forms: `./forms-react-hook-form.md`
- Composition: `./composition-react.md`
- Next.js tRPC: `./metaframeworks/nextjs/trpc.md`
- Next.js ky: `./metaframeworks/nextjs/ky-fetch.md`
