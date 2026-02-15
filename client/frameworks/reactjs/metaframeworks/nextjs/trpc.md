# tRPC (Next.js)

> Next.js-specific tRPC conventions and how tRPC fits into the client API architecture.

## Where tRPC Fits

In this architecture, components never talk to transport directly.
The canonical chain remains:

`components -> query adapter -> featureApi -> clientApi -> network`

tRPC is a transport adapter choice.
Depending on implementation, it can act as:

- a `clientApi` implementation (typed transport calls + normalized errors)
- a transport primitive consumed by `featureApi`

Recommended contract in this repo:

- keep `I<Feature>Api` + `class <Feature>Api` in `src/features/<feature>/api.ts`
- allow query hooks to call a factory-created API instance (or injected instance in tests)
- keep direct `trpc.*.useQuery/useMutation` usage as compatibility mode during migration

## Cache and Query Keys

There are two valid cache-key patterns depending on adapter choice.

### tRPC procedures (`@trpc/react-query`)

- Do not define Query Key Factory keys for tRPC procedures.
- Use tRPC-generated keys and utilities.
- Prefer invalidation via `trpc.useUtils()` in mutation hooks.
- Component-coordinator invalidation is also allowed for route-local orchestration.

Variant A (preferred): hook-owned invalidation

```typescript
export function useMutProfileUpdate() {
  const utils = trpc.useUtils();

  return trpc.profile.update.useMutation({
    onSuccess: async (result) => {
      await Promise.all([
        utils.profile.getByCurrentUser.invalidate(),
        utils.profile.getById.invalidate({ id: result.id }),
      ]);
    },
  });
}
```

Variant B (allowed): component-coordinator invalidation

```typescript
export function useMutProfileUpdate() {
  return trpc.profile.update.useMutation();
}

export function ProfileForm() {
  const utils = trpc.useUtils();
  const updateMut = useMutProfileUpdate();

  const onSubmitInvalidateQueries = async (id: string) =>
    Promise.all([
      utils.profile.getByCurrentUser.invalidate(),
      utils.profile.getById.invalidate({ id }),
    ]);

  const onSubmit = async (data: ProfileFormShape) => {
    const result = await updateMut.mutateAsync(data);
    await onSubmitInvalidateQueries(result.id);
    router.push(appRoutes.dashboard);
  };
}
```

When to choose:

- Choose Variant A when invalidation behavior should be reusable across multiple screens.
- Choose Variant B when submit sequencing is route-local and easier to audit in one component.
- Choose hybrid when mutation hook owns shared defaults and component adds route-local invalidations.

Detailed scenario matrix:

- `client/frameworks/reactjs/server-state-patterns-react.md`

### Non-tRPC HTTP adapters (`ky`, `fetch`, etc.)

- Use Query Key Factory (`@lukemorales/query-key-factory`).
- Store keys in `src/common/query-keys/<feature>.ts`.

See:

- `./ky-fetch.md`
- `../../../../core/query-keys.md`

## Provider and Runtime Notes

Typical tRPC client setup in React/Next.js:

- shared QueryClient (singleton on browser)
- tRPC client provider at app root
- split link when mixing JSON and non-JSON payloads
- serializer strategy consistent with server

Keep these as implementation details inside app providers, not inside feature components.

## Security and Transport Boundaries

Security checks belong in transport/metaframework boundaries, not in presentation components.
Common examples:

- origin/cross-site checks at the tRPC route handler
- rate limiting in tRPC middleware
- structured server error mapping (code/requestId/details) in server formatter

Client-side rule:

- do not branch on provider-specific error shapes in UI
- normalize errors to `AppError` in adapters/facades

## React Hook Conventions with tRPC

Even when using tRPC directly:

- define server-state hooks in `src/features/<feature>/hooks.ts`
- components do not call `trpc.*.useQuery()` inline
- follow naming conventions:
  - query hooks: `useQuery<Feature><Noun><Qualifier?>`
  - mutation hooks: `useMut<Feature><Verb><Object?>`
  - composed hooks: `useMod<Descriptive>`

Testing guidance:

- if hooks call `I<Feature>Api`, mock that interface in hook tests
- if hooks use direct `trpc.*` compatibility mode, keep those tests localized and treat as transitional

Example:

```typescript
export function useQueryProfileMe() {
  return trpc.profile.getByCurrentUser.useQuery();
}

export function useModDashboard() {
  const profileQuery = trpc.profile.get.useQuery();
  const statsQuery = trpc.stats.get.useQuery();
  const notificationsQuery = trpc.notifications.list.useQuery();

  return { profileQuery, statsQuery, notificationsQuery };
}
```

## Error Handling with tRPC

Normalize once at the boundary:

```text
TRPCClientError | unknown
  -> toAppError(err)
  -> AppError
  -> UI branches on AppError.kind only
```

Keep provider-specific checks inside adapters only.

## Compatibility Appendix (Legacy tRPC-First Style)

Some existing codebases still use direct `trpc.*.useQuery/useMutation` patterns inside feature hooks.
This is acceptable as transitional compatibility when:

- queries/mutations remain in `src/features/<feature>/hooks.ts`
- components still consume feature hooks (not direct transport calls)
- invalidation remains centralized in hooks
- a migration issue/backlog exists to restore `I<Feature>Api` boundaries when touched

Migration direction (incremental):

1. Keep transport calls inside hooks only.
2. Introduce `featureApi` boundaries for endpoint/domain mapping.
3. Keep cache ownership in query adapters.
4. Maintain canonical naming and SRP conventions for new/modified hooks.
