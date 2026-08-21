# Client API Architecture (`components -> query adapter -> featureApi -> clientApi`)

Define the standard way the client calls backend endpoints with strict separation of concerns, DI-friendly boundaries, and predictable cache behavior.

Construction and runtime lifetimes follow [Client Composition Root and Factories](./composition-root.md).

## Core Rule

Components never talk to transport directly.

All IO happens through this chain:

`components -> query adapter -> featureApi -> clientApi -> network`

Operational logging and product analytics branch from the layer that owns the occurrence; they do not add hops or metadata parameters to this business data flow.

```text
clientApi ----------> AppLogger          # transport outcome/correlation
featureApi ---------> AppLogger          # contract/mapping diagnostics only
mutation/workflow --> ProductAnalytics   # typed event after meaningful success
```

Public request/response schemas are not owned by any of these client layers. In the single-project topology, they are imported from the owning module's isomorphic contract directory:

`src/lib/modules/<module>/shared/contracts/`

In a monorepo topology, import the same contract role from an activated contract package through its public exports when the contract crosses package boundaries.

## Layers

### 1) `clientApi` (transport + cross-cutting concerns)

Owns:

- HTTP client wrapper (`fetch`/`ky`/`axios`-style)
- base URL, headers/auth attachment
- standard response envelope decoding
- typed, inspectable transport errors
- global retry/timeouts (if any)
- request duration/status logging through injected `AppLogger`
- capture of server-provided `requestId` for correlation

Does not own:

- endpoint-specific paths
- domain logic
- cache logic
- product analytics

Transport logging is emitted once here. Higher layers must not re-report the same transport failure.

Example surface:

- `clientApi.get<T>(path, options)`
- `clientApi.post<T>(path, body, options)`

### 2) `featureApi` (endpoint-scoped API, class-based)

One contract + one class per feature domain:

- `IProfileApi` + `ProfileApi implements IProfileApi`
- `IBillingApi` + `BillingApi implements IBillingApi`

Owns:

- endpoint paths for that domain
- parsing network output with shared response schemas
- DTO -> feature model mapping (pure helpers)
- normalization handoff (`unknown -> AppError`) at the boundary
- operational diagnostics for response-contract or mapping failures owned by this boundary

Depends on injected collaborators:

- `clientApi` (required)
- `toAppError` (required)
- `AppLogger` when the implementation emits boundary-owned diagnostics
- optional deterministic utilities (`clock`, `idFactory`) when needed

Does not own:

- query/mutation cache behavior
- React hook orchestration
- product analytics by default
- duplicate reporting of transport failures already owned by `clientApi`

### Required `featureApi` Contract

```ts
// src/features/profile/api.ts
import { ZodError } from "zod";

import type { AppLogger } from "@/common/logging/types";
import type { AppError } from "@/common/errors/app-error";
import { invalidResponseError } from "@/common/errors/invalid-response-error";
import {
  GetCurrentProfileResponseSchema,
  UpdateProfileResponseSchema,
  type UpdateProfileInput,
} from "@/lib/modules/profile/shared/contracts";

export interface IProfileApi {
  getCurrent(): Promise<Profile>;
  update(input: UpdateProfileInput): Promise<Profile>;
}

export type ProfileApiDeps = {
  clientApi: IClientApi;
  toAppError: (err: unknown) => AppError;
  logger: AppLogger;
};

export class ProfileApi implements IProfileApi {
  constructor(private readonly deps: ProfileApiDeps) {}

  async getCurrent(): Promise<Profile> {
    try {
      const raw = await this.deps.clientApi.get<unknown>("/profile/me");
      const dto = GetCurrentProfileResponseSchema.parse(raw);
      return toProfile(dto);
    } catch (err) {
      if (err instanceof ZodError) {
        this.deps.logger.error(
          {
            eventName: "profile.get.response.invalid",
            attributes: { "error.type": "api.invalid_response" },
            error: err,
          },
          "Profile response violated contract",
        );
        throw invalidResponseError(err);
      }
      throw this.deps.toAppError(err);
    }
  }

  async update(input: UpdateProfileInput): Promise<Profile> {
    try {
      const raw = await this.deps.clientApi.patch<unknown>(
        "/profile/me",
        input,
      );
      const dto = UpdateProfileResponseSchema.parse(raw);
      return toProfile(dto);
    } catch (err) {
      if (err instanceof ZodError) {
        this.deps.logger.error(
          {
            eventName: "profile.update.response.invalid",
            attributes: { "error.type": "api.invalid_response" },
            error: err,
          },
          "Profile update response violated contract",
        );
        throw invalidResponseError(err);
      }
      throw this.deps.toAppError(err);
    }
  }
}

export const createProfileApi = (deps: ProfileApiDeps): IProfileApi =>
  new ProfileApi(deps);
```

Optional runtime convenience:

- `getProfileApi()` may expose the browser application-scoped instance owned by the composition root
- `api.runtime.ts` is a stable indirection/mock target, not the owner that constructs a hidden singleton
- SSR creates a request-scoped instance only when the API closes over request context

### 3) Query adapter (server state + cache management)

Owns:

- query/mutation definitions
- query keys
- invalidation / optimistic updates
- typed product analytics after a successful reusable mutation when this layer owns the action

Depends on:

- `I<Feature>Api` contract (not `clientApi`)

Does not own:

- endpoint paths
- transport decoding
- transport logging or provider SDK imports

### 4) Components

Own:

- UI composition, loading/error wiring, form orchestration
- UI-only product events when the component owns the occurrence

Do not own:

- query/mutation definitions
- transport/IO logic
- routine operational logging

## File Layout (Feature Module)

The shared wire contract lives outside the client feature so server and client can both import it:

```text
src/lib/modules/<module>/shared/contracts/
  <capability>.contract.ts
  index.ts
```

Recommended client feature layout:

```text
src/features/<feature>/
  api.ts              # I<Feature>Api + <Feature>Api class + create<Feature>Api factory
  api.runtime.ts      # re-exports composition-root-owned instance/accessor (stable mock target)
  hooks.ts            # query adapter (TanStack Query hooks + cache ops)
  schemas.ts          # UI/form schemas composed from shared input contracts
  types.ts            # feature types (non-DTO)
  helpers.ts          # DTO-to-feature-model mapping + small pure utilities
  components/         # business + presentation components
```

Optional files (add when the feature requires them):

```text
  domain.ts           # feature-local pure domain rules (when not reusable cross-runtime)
  sync.ts             # cache sync composition hooks (multi-query invalidation orchestration)
  realtime-api.ts     # I<Feature>RealtimeApi + implementation for Supabase realtime subscriptions
  realtime-api.runtime.ts  # re-exports composition-root-owned realtime accessor
  query-options.ts    # TanStack Query queryOptions() factories for RSC/prefetch
  stores/             # Zustand stores for client coordination state
  machines/           # XState state machines for complex UI interaction logic
  hooks/              # sub-folder when root hooks.ts becomes too large
```

Domain transform precedence:

- import API input/response contracts from `lib/modules/<module>/shared/contracts/`
- prefer module-level shared domain logic in `lib/modules/<module>/shared/domain.ts` when reused across runtimes
- keep `src/features/<feature>/domain.ts` or `helpers.ts` for feature-local pure logic that is not shared

### `api.runtime.ts` — Testability Indirection

Every feature with an API class has an `api.runtime.ts` that re-exports the composition-root-owned accessor:

```typescript
// src/features/reservation/api.runtime.ts
export { getReservationApi } from "@/common/runtime/browser";
```

Tests mock `@/features/reservation/api.runtime` while keeping `api.ts` pure. The composition root owns construction/lifecycle; the runtime module only provides a stable feature-facing import and test boundary.

### Optional tRPC-Interop Hook Wrappers

The `IFeatureApi` boundary does not require custom TanStack Query wrappers. Most query adapters call `useQuery`/`useMutation` directly with the key strategy for their transport.

When an `IFeatureApi` is backed by tRPC and its cache entries must interoperate with tRPC utilities, the project may expose narrowly named wrappers such as `useTrpcFeatureQuery` from `src/common/trpc-feature-api-hooks.ts`:

```typescript
// src/common/trpc-feature-api-hooks.ts
export function useTrpcFeatureQuery<TData>(
  path: string[],
  queryFn: () => Promise<TData>,
  input?: unknown,
  options?: UseQueryOptions,
): UseQueryResult<TData, AppError>;

export function useAppMutation<TData, TInput>(
  mutationFn: (input: TInput) => Promise<TData>,
  options?: UseMutationOptions,
): UseMutationResult<TData, AppError, TInput>;

export function useTrpcFeatureQueryCache(): FeatureQueryCache;
```

The tRPC-specific query wrapper:

- Build query keys via `buildTrpcQueryKey(path, input)` for tRPC interop
- Type errors as `AppError` throughout the hook chain
- May provide a typed cache facade for imperative tRPC-interoperable operations

For Ky, fetch, and realtime-backed features, use plain key factories from `src/common/query-keys/*`; do not route them through a tRPC-shaped wrapper. A generic mutation helper may standardize the `AppError` type because mutations do not create query keys, but it must not hide transport-specific cache behavior.

### `sync.ts` — Cache Sync Composition

Features with complex, multi-query invalidation patterns extract cache orchestration into a `sync.ts` file:

```typescript
// src/features/reservation/sync.ts
export function useModReservationSync() {
  const utils = trpc.useUtils();
  const queryClient = useQueryClient();

  return {
    invalidateAll: async () => {
      await utils.reservation.invalidate();
      await queryClient.invalidateQueries({ queryKey: buildTrpcQueryKey([...]) });
    },
  };
}
```

This keeps `hooks.ts` focused on individual query/mutation definitions.

## Testability Contract

Test by boundary:

- `domain.ts` / `helpers.ts`: pure function unit tests (no mocks).
- shared contracts: table-test accepted/rejected wire payloads once in the mirrored `src/__tests__/lib/modules/<module>/shared/contracts/` path.
- `api.ts`: unit test `<Feature>Api` by mocking transport and asserting shared response parsing, mapping, and error normalization; inject a logger spy when it emits boundary-owned diagnostics.
- `hooks.ts`: test query behavior by mocking `I<Feature>Api`, not transport; use an analytics spy for typed success events.
- business components: mock feature hooks, not network clients.

All test files live in `src/__tests__/` mirroring the source tree.
Full testing standard (AAA pattern, table-driven tests, test doubles, naming): `client/core/testing.md`.

## Conventions

- Zod parse at boundaries: `featureApi` parses responses and returns safe data.
- Shared wire schemas are imported from `lib/modules/<module>/shared/contracts/`; never copied into `features/`.
- Cache rules live in the query adapter: invalidation/optimistic updates never live in components.
- Operational logs use `AppLogger`; transport failures are owned by `clientApi`, and contract/mapping failures by `featureApi`.
- Product analytics uses `ProductAnalytics` and emits from the successful mutation/workflow owner.
- Correlation context is adapter-owned and never added to business DTOs or ordinary method parameters.
- `createClientApi` and `create<Feature>Api` are called by the composition root; feature modules do not create hidden singletons.
- Avoid "big data providers": share server data via query cache + query keys.
- Domain transforms follow precedence: module shared (`lib/modules/<module>/shared/*`) first, then feature-local (`src/features/<feature>/*`).
