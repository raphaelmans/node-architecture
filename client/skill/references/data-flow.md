# Data Flow Slice

Use this slice for client transport, feature APIs, TanStack Query adapters, mutation sequencing, query keys, tRPC, and HTTP route-handler clients.

## Contents

- [Canonical chain](#canonical-chain)
- [Boundary contracts](#boundary-contracts)
- [Query and mutation ownership](#query-and-mutation-ownership)
- [Query keys](#query-keys)
- [Create flow](#create-flow)
- [Transport choices](#transport-choices)
- [Review checklist](#review-checklist)

## Canonical Chain

```text
components
  -> query adapter
    -> featureApi
      -> clientApi
        -> network
```

Responses return in reverse. Logging and analytics branch from their owning layers; they do not become extra hops or extra business parameters.

## Boundary Contracts

`clientApi` owns:

- transport construction, base URL, auth/header attachment, timeouts, and retry policy;
- universal response-envelope decoding;
- typed transport errors and response `requestId` capture;
- one transport outcome log.

`featureApi` owns:

- domain endpoint paths;
- shared capability response parsing;
- pure DTO-to-feature-model mapping;
- `unknown -> AppError` handoff;
- contract/mapping diagnostics owned by this boundary.

When it emits those diagnostics, load the `telemetry` slice and follow the `AppLogger` event-first signature:

```ts
logger.error(
  {
    eventName: "profile.update.response.invalid",
    attributes: { "error.type": "api.invalid_response" },
    error,
  },
  "Profile update response violated contract",
);
```

Do not use `logger.error(message, attributes)` and do not normalize a known response-schema failure as a user-input validation error.

Every feature API follows:

```ts
interface IProfileApi {
  getCurrent(): Promise<Profile>;
  update(input: UpdateProfileInput): Promise<Profile>;
}

class ProfileApi implements IProfileApi {
  constructor(private readonly deps: ProfileApiDeps) {}
}

const createProfileApi = (deps: ProfileApiDeps): IProfileApi =>
  new ProfileApi(deps);
```

This shape is required: define the interface, implement an exported class, and expose the factory. Do not replace the class with an inline object returned directly from the factory; the named class is the independently testable implementation boundary.

The query adapter depends on `IProfileApi`, never on Ky, fetch, the tRPC client, or another provider primitive.

## Query and Mutation Ownership

Keep query/mutation units single-purpose. Query adapters own:

- query functions and stable keys;
- dependency guards and composed loading/error state;
- invalidation, optimistic updates, and cache patches;
- reusable success analytics when the mutation owns that occurrence.

Prefer hook-owned invalidation for reusable mutation behavior. A business coordinator may own route-local `mutate -> sync -> navigate` sequencing, but it calls a named operation from `hooks.ts` or `sync.ts`; it never embeds QueryClient or concrete keys in TSX.

Optimistic updates require an exact snapshot, immutable patch, rollback on error, and reconciliation after settle. If rollback semantics are unclear, use explicit invalidation.

## Query Keys

Select keys by transport pattern:

1. Direct tRPC hooks: use tRPC-generated keys and `trpc.useUtils()`.
2. `IFeatureApi` backed by tRPC and requiring cache interop: use `buildTrpcQueryKey(path, input)`.
3. Ky, fetch, or realtime-backed adapters: use plain key factories under `src/common/query-keys/`.

```ts
export const profileKeys = {
  all: ["profile"] as const,
  details: () => [...profileKeys.all, "detail"] as const,
  detail: (id: string) => [...profileKeys.details(), id] as const,
};
```

Include every result-changing dependency. Keep structured inputs serializable. Normalize only when the server treats representations as semantically equivalent, and share that normalization with request mapping.

## Create Flow

```text
CreateForm.onSubmit
  -> useMutCreate.mutateAsync(input)
  -> FeatureApi.create(input)
  -> ClientApi.post(path, input)
  -> network
  <- envelope data + requestId
  <- capability schema parse + mapped model
  +-> completion analytics after success
  +-> cache update/invalidation
  -> toast/navigation
```

Do not pass logger, trace ID, request ID, pathname, or analytics context through `create(input)`. Adapters and injected ports own that context.

## Transport Choices

For tRPC:

- Treat tRPC as a transport adapter, not the feature boundary.
- Keep shared runtime contracts when a capability may be consumed outside tRPC.
- Direct tRPC hooks are an incremental compatibility mode only when they stay inside feature hooks and expose app-facing errors/results.
- Use tRPC utilities for direct-procedure invalidation.

For Ky or fetch:

- Construct the client only in `createClientApi`.
- Decode `{ data }` success envelopes and safe error envelopes at the transport boundary.
- Throw typed, inspectable transport errors and normalize them before UI exposure.
- Use plain query-key factories.

## Review Checklist

- Components do not call transport or inline query definitions.
- Feature APIs own endpoint paths and response parsing, not cache behavior.
- Query adapters depend on `I<Feature>Api`.
- Cache operations and concrete keys stay outside TSX.
- Direct tRPC compatibility code does not leak raw provider errors.
- Request and response contracts are shared with the server.
- Transport and contract failures have separate single reporting owners.
- Completion analytics emits only after meaningful success.
- Factories and the composition root own all provider construction.

## Derivation Sources

Derived from the source repository's client-api-architecture, server-state-tanstack-query, query-keys, conventions, React server-state patterns, Next.js tRPC, and Next.js Ky documents. These paths are provenance only in an installed skill.
