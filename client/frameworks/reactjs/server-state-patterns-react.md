# Server State Patterns (React)

> Comprehensive cookbook for TanStack Query usage in React features, aligned with `client/core/server-state-tanstack-query.md`.

## Purpose

This document shows **how** to apply core server-state contracts in React code with practical patterns.

Core contracts still live in:

- `client/core/server-state-tanstack-query.md`
- `client/core/conventions.md`

## Decision Matrix (Cache Ownership + Workflow Sequencing)

Use this matrix when deciding where invalidation/cache orchestration should live.

| Situation | Preferred Pattern | Why |
| --- | --- | --- |
| Standard single-feature mutation | Hook-owned invalidation | Reusable, low duplication |
| Form flow with route-local orchestration (redirect/toast/local UI sequence) | Component-coordinator sequencing through `useMod*Sync` | Makes submit sequence explicit while cache mechanics stay outside TSX |
| Edit/update form must reflect fresh external server data after save | Await invalidation, then sync from refreshed query data | Active matching queries refetch during invalidation |
| Mutation has base cache effects, component has extra route-local effects | Hybrid | Shared defaults + local orchestration |
| Legacy feature currently coordinating in component | Component-coordinator (transitional) | Keeps behavior stable while migrating incrementally |

Product analytics follows the same occurrence ownership: a reusable mutation hook emits its typed completion event after success; a route-local workflow event stays with the component coordinator or `useMod*` workflow hook.

## Pattern A: Hook-Owned Invalidation (Preferred Default)

Use when mutation effects are reusable across multiple components.

```ts
// src/features/profile/hooks.ts
export function useMutProfileUpdate() {
  const queryClient = useQueryClient();
  const analytics = useProductAnalytics();

  return useMutation({
    mutationFn: updateProfile,
    onSuccess: async () => {
      analytics.track({
        name: "profile_updated",
        properties: { source: "settings" },
      });

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: profileQueryKeys.current() }),
        queryClient.invalidateQueries({ queryKey: profileQueryKeys.details() }),
      ]);
    },
  });
}
```

Component:

```ts
const updateMut = useMutProfileUpdate();
await updateMut.mutateAsync(toUpdateProfileInput(data));
router.push(appRoutes.dashboard);
```

## Pattern B: Component-Coordinator Sequencing (Allowed)

Use when the submit flow is route-local and sequencing is central to UX. The component owns the order; a query/cache-sync hook owns keys and invalidation mechanics.

```ts
// src/features/profile/sync.ts
export function useModProfileSync() {
  const queryClient = useQueryClient();

  return {
    invalidateAfterUpdate: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: profileQueryKeys.current() }),
        queryClient.invalidateQueries({ queryKey: profileQueryKeys.details() }),
      ]),
  };
}

// src/features/profile/components/profile-form.tsx
const updateMut = useMutProfileUpdate();
const profileSync = useModProfileSync();

const onSubmit = async (data: ProfileFormShape) => {
  await updateMut.mutateAsync(toUpdateProfileInput(data));
  await profileSync.invalidateAfterUpdate();
  router.push(appRoutes.dashboard);
};
```

## Pattern C: Hybrid Ownership

The mutation hook handles shared invalidation; a named sync hook exposes route-local additions that the component sequences.

```ts
// hook: shared defaults
export function useMutProfileUpdate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateProfile,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: profileQueryKeys.current() });
    },
  });
}

// sync.ts: route-local addition exposed to the component
export function useModDashboardSync() {
  const queryClient = useQueryClient();
  return {
    invalidateSummary: () =>
      queryClient.invalidateQueries({ queryKey: dashboardQueryKeys.summary() }),
  };
}

// component: route-local sequencing
const dashboardSync = useModDashboardSync();

const onSubmit = async (data: ProfileFormShape) => {
  await updateMut.mutateAsync(toUpdateProfileInput(data));
  await dashboardSync.invalidateSummary();
  router.push(appRoutes.dashboard);
};
```

## Scenario Cookbook

### Create Form

- Usually hook-owned invalidation.
- Component handles success UX (toast/redirect).

### Edit Form

- Either hook-owned or coordinator sequencing through a named sync operation.
- Button default: disable only during submit.
- Optional edit/update-only exception: disable when `!isDirty` for no-op prevention.
- For edit/update forms with external defaults, await invalidation of the active detail/current query, then re-sync form defaults from refreshed `query.data`.
- Call `query.refetch()` explicitly only when invalidation is intentionally configured not to refetch, the query is disabled/inactive but must refresh immediately, or no invalidation occurs.

### Upload + Follow-Up Mutation

- Prefer hybrid:
  - upload mutation owns upload-related invalidation
  - a cache-sync hook owns follow-up list/detail invalidations
  - the component coordinates that sync operation with navigation

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
- Use deterministic key scopes (`src/common/query-keys/*` for non-tRPC) inside hooks/cache-sync modules, not TSX.
- Normalize errors to `AppError` before presentation logic branches.
- Keep transport checks out of presentation components.
- Do not re-log transport failures already owned by `clientApi`/`featureApi`.
- Emit typed completion analytics only after mutation success; analytics delivery remains non-blocking.
- Resolve feature APIs and telemetry ports from composition-root-owned factories, never hidden feature singletons or a runtime service locator.

## Testing Cookbook (React Query Layer)

### Query/Mutation Hook Tests

- mock `I<Feature>Api` (or factory return) as the data source
- assert query key usage, invalidation behavior, and status transitions
- use a `ProductAnalytics` spy for success-only event behavior
- avoid mocking transport providers directly (`fetch`, `axios`, `trpc` client internals)

### Feature API Tests

- unit test `class <Feature>Api` with mocked `clientApi`, `toAppError`, and logger when used
- assert shared response-contract parsing, DTO-to-feature-model mapping, and error normalization handoff

### Domain/Helper Tests

- keep pure and table-driven (`domain.ts`, `helpers.ts`)
- no mocks needed

## Anti-Patterns

- Presentation component calling transport/query-library hooks directly.
- “God hook” combining unrelated domains.
- Ad-hoc key arrays repeated across components.
- Duplicating server entities into local stores as source of truth.
- Reporting the same mutation failure in transport, hook, and component layers.
- Importing analytics/logging vendors directly inside hooks.

## Related Docs

- Forms: `./forms-react-hook-form.md`
- Composition: `./composition-react.md`
- Next.js tRPC: `./metaframeworks/nextjs/trpc.md`
- Next.js ky: `./metaframeworks/nextjs/ky-fetch.md`
