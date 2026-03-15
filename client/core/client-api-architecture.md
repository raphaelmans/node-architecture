# Client API Architecture (`clientApi -> featureApi -> query adapter`)

Define the standard way the client calls backend endpoints with strict separation of concerns, DI-friendly boundaries, and predictable cache behavior.

## Core Rule

Components never talk to transport directly.

All IO happens through this chain:

`components -> query adapter -> featureApi -> clientApi -> network`

## Layers

### 1) `clientApi` (transport + cross-cutting concerns)

Owns:

- HTTP client wrapper (`fetch`/`ky`/`axios`-style)
- base URL, headers/auth attachment
- standard response envelope decoding
- typed, inspectable transport errors
- global retry/timeouts (if any)

Does not own:

- endpoint-specific paths
- domain logic
- cache logic

Example surface:

- `clientApi.get<T>(path, options)`
- `clientApi.post<T>(path, body, options)`

### 2) `featureApi` (endpoint-scoped API, class-based)

One contract + one class per feature domain:

- `IProfileApi` + `ProfileApi implements IProfileApi`
- `IBillingApi` + `BillingApi implements IBillingApi`

Owns:

- endpoint paths for that domain
- request/response schema parsing (Zod)
- DTO -> feature model mapping (pure helpers)
- normalization handoff (`unknown -> AppError`) at the boundary

Depends on injected collaborators:

- `clientApi` (required)
- `toAppError` (required)
- optional deterministic utilities (`clock`, `idFactory`) when needed

Does not own:

- query/mutation cache behavior
- React hook orchestration

### Required `featureApi` Contract

```ts
// src/features/profile/api.ts
import type { AppError } from "@/common/errors/app-error";

export interface IProfileApi {
  getCurrent(): Promise<Profile>;
  update(input: UpdateProfileInput): Promise<Profile>;
}

export type ProfileApiDeps = {
  clientApi: IClientApi;
  toAppError: (err: unknown) => AppError;
};

export class ProfileApi implements IProfileApi {
  constructor(private readonly deps: ProfileApiDeps) {}

  async getCurrent(): Promise<Profile> {
    try {
      const dto = await this.deps.clientApi.get<ProfileDto>("/profile/me");
      return parseProfile(dto);
    } catch (err) {
      throw this.deps.toAppError(err);
    }
  }

  async update(input: UpdateProfileInput): Promise<Profile> {
    try {
      const dto = await this.deps.clientApi.patch<ProfileDto>("/profile/me", input);
      return parseProfile(dto);
    } catch (err) {
      throw this.deps.toAppError(err);
    }
  }
}

export const createProfileApi = (deps: ProfileApiDeps): IProfileApi =>
  new ProfileApi(deps);
```

Optional runtime convenience:

- `getProfileApi()` for singleton wiring
- keep singleton ownership in app composition, not inside components

### 3) Query adapter (server state + cache management)

Owns:

- query/mutation definitions
- query keys
- invalidation / optimistic updates

Depends on:

- `I<Feature>Api` contract (not `clientApi`)

Does not own:

- endpoint paths
- transport decoding

### 4) Components

Own:

- UI composition, loading/error wiring, form orchestration

Do not own:

- query/mutation definitions
- transport/IO logic

## File Layout (Feature Module)

Recommended feature module layout:

```text
src/features/<feature>/
  api.ts              # I<Feature>Api + <Feature>Api class + create<Feature>Api factory
  api.runtime.ts      # re-exports singleton factory (stable mock target for tests)
  hooks.ts            # query adapter (TanStack Query hooks + cache ops)
  schemas.ts          # Zod schemas + derived types + mapping helpers
  types.ts            # feature types (non-DTO)
  helpers.ts          # small pure utilities (pure functions)
  components/         # business + presentation components
```

Optional files (add when the feature requires them):

```text
  domain.ts           # feature-local pure domain rules (when not reusable cross-runtime)
  sync.ts             # cache sync composition hooks (multi-query invalidation orchestration)
  realtime-api.ts     # I<Feature>RealtimeApi + implementation for Supabase realtime subscriptions
  realtime-api.runtime.ts  # re-exports realtime singleton (same pattern as api.runtime.ts)
  query-options.ts    # TanStack Query queryOptions() factories for RSC/prefetch
  stores/             # Zustand stores for client coordination state
  machines/           # XState state machines for complex UI interaction logic
  hooks/              # sub-folder when root hooks.ts becomes too large
```

Domain transform precedence:

- prefer module-level shared domain logic in `lib/modules/<module>/shared/domain.ts` when reused across runtimes
- keep `src/features/<feature>/domain.ts` or `helpers.ts` for feature-local pure logic that is not shared

### `api.runtime.ts` — Testability Indirection

Every feature with an API class has an `api.runtime.ts` that re-exports the singleton:

```typescript
// src/features/reservation/api.runtime.ts
export { getReservationApi } from "./api";
```

Tests mock `@/features/reservation/api.runtime` while keeping `api.ts` pure. This is a testability boundary artifact — without it, mocking the singleton in tests would require mocking the entire `api.ts` module.

### `useFeatureQuery` / `useFeatureMutation` — Custom Hook Wrappers

Features using the `IFeatureApi` boundary use `useFeatureQuery` and `useFeatureMutation` from `src/common/feature-api-hooks.ts`:

```typescript
// src/common/feature-api-hooks.ts
export function useFeatureQuery<TData>(
  path: string[],
  queryFn: () => Promise<TData>,
  input?: unknown,
  options?: UseQueryOptions,
): UseQueryResult<TData, AppError>;

export function useFeatureMutation<TData, TInput>(
  mutationFn: (input: TInput) => Promise<TData>,
  options?: UseMutationOptions,
): UseMutationResult<TData, AppError, TInput>;

export function useFeatureQueryCache(): FeatureQueryCache;
```

These wrappers:

- Build query keys via `buildTrpcQueryKey(path, input)` for tRPC interop
- Type errors as `AppError` throughout the hook chain
- Provide `useFeatureQueryCache()` for imperative cache operations (invalidation, optimistic updates)

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
- `api.ts`: unit test `<Feature>Api` by mocking `callTrpcQuery` / `callTrpcMutation` from transport wrappers.
- `hooks.ts`: test query behavior by mocking `I<Feature>Api`, not transport.
- business components: mock feature hooks, not network clients.

All test files live in `src/__tests__/` mirroring the source tree.
Full testing standard (AAA pattern, table-driven tests, test doubles, naming): `client/core/testing.md`.

## Conventions

- Zod parse at boundaries: `featureApi` parses responses and returns safe data.
- Cache rules live in the query adapter: invalidation/optimistic updates never live in components.
- Avoid "big data providers": share server data via query cache + query keys.
- Domain transforms follow precedence: module shared (`lib/modules/<module>/shared/*`) first, then feature-local (`src/features/<feature>/*`).
