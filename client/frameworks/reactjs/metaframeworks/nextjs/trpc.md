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

- define public Zod input/response schemas once in `src/lib/modules/<module>/shared/contracts/`
- import those schemas from both the tRPC procedure and client `featureApi`
- keep `I<Feature>Api` + `class <Feature>Api` in `src/features/<feature>/api.ts`
- allow query hooks to call a factory-created API instance (or injected instance in tests)
- keep direct `trpc.*.useQuery/useMutation` usage as compatibility mode during migration
- construct the tRPC client inside `createClientApi`/the client composition root
- instrument transport outcomes and `requestId` once in the tRPC client link/adapter through `AppLogger`

tRPC's inferred router types are useful, but they do not replace the shared runtime contract when the same capability is also consumed by `route.ts`, OpenAPI, mobile, or a non-tRPC client. Do not create a tRPC-only duplicate schema.

The server uses the same success envelope for tRPC and HTTP. A direct tRPC hook therefore receives `ApiResponse<Payload>` and reads the capability payload from `result.data`. A `clientApi`-style tRPC adapter may unwrap that envelope before passing the payload to `featureApi`, matching the non-tRPC client contract.

## Cache and Query Keys

There are two valid cache-key patterns depending on adapter choice.

### tRPC procedures (`@trpc/react-query`)

- Do not define custom key objects for direct tRPC procedures.
- Use tRPC-generated keys and utilities.
- Prefer invalidation via `trpc.useUtils()` in mutation hooks.
- Component-coordinator sequencing is allowed for route-local orchestration, but tRPC cache mechanics stay in a named `useMod*Sync` hook.

Direct-tRPC compatibility hooks are themselves adapter boundaries. Return an app-facing projection rather than the raw provider result:

```typescript
function toAppMutationFacade<TInput, TData>(mutation: {
  isPending: boolean;
  error: unknown;
  mutateAsync(input: TInput): Promise<TData>;
}) {
  return {
    isPending: mutation.isPending,
    error: mutation.error ? toAppError(mutation.error) : null,
    async mutateAsync(input: TInput) {
      try {
        return await mutation.mutateAsync(input);
      } catch (error) {
        throw toAppError(error);
      }
    },
  };
}
```

Do not spread the raw tRPC mutation/query result into the facade because that would re-expose its provider-specific `error`.

Variant A (preferred): hook-owned invalidation

```typescript
export function useMutProfileUpdate() {
  const utils = trpc.useUtils();
  const analytics = useProductAnalytics();

  const mutation = trpc.profile.update.useMutation({
    onSuccess: async (result) => {
      analytics.track({
        name: "profile_updated",
        properties: { source: "settings" },
      });

      await Promise.all([
        utils.profile.getByCurrentUser.invalidate(),
        utils.profile.getById.invalidate({ id: result.data.id }),
      ]);
    },
  });

  return toAppMutationFacade(mutation);
}
```

Variant B (allowed): component-coordinator sequencing

```typescript
export function useMutProfileUpdate() {
  return toAppMutationFacade(trpc.profile.update.useMutation());
}

export function useModProfileSync() {
  const utils = trpc.useUtils();
  return {
    invalidateAfterUpdate: (id: string) =>
      Promise.all([
        utils.profile.getByCurrentUser.invalidate(),
        utils.profile.getById.invalidate({ id }),
      ]),
  };
}

export function ProfileForm() {
  const updateMut = useMutProfileUpdate();
  const profileSync = useModProfileSync();

  const onSubmit = async (data: ProfileFormShape) => {
    const result = await updateMut.mutateAsync(toUpdateProfileInput(data));
    await profileSync.invalidateAfterUpdate(result.data.id);
    router.push(appRoutes.dashboard);
  };
}
```

When to choose:

- Choose Variant A when invalidation behavior should be reusable across multiple screens.
- Choose Variant B when submit sequencing is route-local and easier to audit in one component while `useMod*Sync` owns provider/cache details.
- Choose hybrid when the mutation hook owns shared defaults and a named `useMod*Sync` operation exposes route-local additions to the component coordinator.

Detailed scenario matrix:

- `client/frameworks/reactjs/server-state-patterns-react.md`

### Non-tRPC HTTP adapters (`ky`, `fetch`, etc.)

- Use plain key objects in `src/common/query-keys/<feature>.ts`.
- Reserve `buildTrpcQueryKey` for wrappers that need tRPC interop.

See:

- `./ky-fetch.md`
- `../../../../core/query-keys.md`

## Provider and Runtime Notes

Typical tRPC client setup in React/Next.js:

- shared QueryClient (singleton on browser)
- tRPC client provider at app root
- split link when mixing JSON and non-JSON payloads
- serializer strategy consistent with server
- injected `AppLogger` integration/link for transport outcome and error correlation

Create these through a named factory in the client composition root. Browser dependencies are application-scoped. SSR dependencies are request-scoped only when they capture request headers/cookies/context. App providers receive already-created specific dependencies; they do not construct vendors or expose a runtime service locator.

## Logging and Analytics Ownership

- The tRPC client link/adapter owns request duration, procedure/path, final status, retry exhaustion, and server `requestId` logging.
- `featureApi` logs only response-contract/mapping failures it owns.
- Direct tRPC compatibility hooks must not re-report transport failures already logged by the link/adapter.
- Mutation/workflow owners may emit a typed `ProductAnalytics` event after meaningful success.
- Framework error boundaries own unhandled exceptions and may forward them to the optional Sentry adapter.
- Product analytics and operational logging remain separate ports.

## Security and Transport Boundaries

Security checks belong in transport/metaframework boundaries, not in presentation components.
Common examples:

- origin/cross-site checks at the tRPC route handler
- rate limiting in tRPC middleware
- structured server error mapping (code/requestId/details) in server formatter
- trace/correlation propagation in the tRPC transport link/adapter

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
- use analytics/logger spies rather than live providers when the behavior includes telemetry

Example:

```typescript
export function useQueryProfileMe() {
  const query = trpc.profile.getByCurrentUser.useQuery();
  return {
    data: query.data,
    isPending: query.isPending,
    isFetching: query.isFetching,
    error: query.error ? toAppError(query.error) : null,
    refetch: query.refetch,
  };
}

export function useModDashboard() {
  const profileQuery = useQueryProfileMe();
  const statsQuery = useQueryStats();
  const notificationsQuery = useQueryNotificationsList();

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
5. Move provider construction and singleton lifecycle into the client composition root.
