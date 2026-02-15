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
  hooks.ts       # query adapter (TanStack Query hooks + cache ops)
  api.ts         # I<Feature>Api + <Feature>Api class + create<Feature>Api factory
  schemas.ts     # Zod schemas + derived types + mapping helpers
  types.ts       # feature types (non-DTO)
  domain.ts      # business rules (pure functions)
  helpers.ts     # small pure utilities (pure functions)
  components/    # business + presentation components
```

## Testability Contract

Test by boundary:

- `domain.ts` / `helpers.ts`: pure function unit tests (no mocks).
- `api.ts`: unit test `<Feature>Api` by mocking `clientApi` + `toAppError`.
- `hooks.ts`: test query behavior by mocking `I<Feature>Api`, not transport.
- business components: mock feature hooks, not network clients.

## Conventions

- Zod parse at boundaries: `featureApi` parses responses and returns safe data.
- Cache rules live in the query adapter: invalidation/optimistic updates never live in components.
- Avoid "big data providers": share server data via query cache + query keys.
