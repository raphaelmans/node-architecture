# Error Handling (Agnostic)

Conventions for handling errors across the client architecture.

## Core Rule: Normalize to `AppError`

UI code must not depend on transport/provider-specific error types (Axios, tRPC, fetch wrappers, etc.).

Instead:

- adapters convert `unknown` -> `AppError`
- application code only branches on `AppError.kind`

## App Error Contract (Single Source of Truth)

We use a discriminated union. Preserve only user-safe messages; use generic fallbacks for internal failures.

```ts
export interface AppErrorMeta {
  message: string;
  status?: number;
  code?: string;
  requestId?: string;
  cause?: unknown;
}

export type AppError =
  | ({ kind: "network" } & AppErrorMeta)
  | ({
      kind: "unauthorized" | "forbidden" | "not_found" | "rate_limited";
    } & AppErrorMeta)
  | ({
      kind: "validation";
      fieldErrors?: Record<string, string>;
    } & AppErrorMeta)
  | ({ kind: "contract" } & AppErrorMeta)
  | ({ kind: "unknown" } & AppErrorMeta);
```

## Adapter Pattern (Required)

Adapter signature:

- input: `unknown`
- output: `AppError`

```ts
export function toAppError(err: unknown): AppError;
```

Provider-specific checks live **only** inside adapters.

Feature response parsing uses a small provider-neutral constructor because the owning boundary already knows the failure classification:

```ts
export function invalidResponseError(cause: unknown): AppError {
  return {
    kind: "contract",
    code: "api.invalid_response",
    message: "Something went wrong",
    cause,
  };
}
```

This is not a second normalization pass: transport/provider failures go through `toAppError`; a response parser directly constructs the known contract error.

Runtime placement (Next.js convention):

```text
src/common/errors/
  app-error.ts
  to-app-error.ts
  adapters/
    trpc.ts          # tRPC-specific error field extraction
    ky.ts            # Ky/fetch-specific error extraction
```

### tRPC Error Adapter

The `adapters/trpc.ts` adapter extracts tRPC-specific fields from the raw error shape and maps them to a normalized `TrpcErrorMeta`:

```typescript
// src/common/errors/adapters/trpc.ts
export interface TrpcErrorMeta {
  code: string;
  httpStatus: number;
  requestId?: string;
  zodError?: { fieldErrors: Record<string, string[]> };
}

export function toTrpcErrorMeta(err: unknown): TrpcErrorMeta | null;
```

This adapter is used by `toAppError` to extract `code`, `httpStatus`, `requestId`, and `zodError.fieldErrors` from tRPC's error shape before mapping to `AppError.kind`.

## Error Types

| Error Type | Source | Handling |
| --- | --- | --- |
| Input validation | User-correctable request/form input | Field-level messages |
| Contract violation | Successful response fails decoding/mapping | Generic UI message + boundary-owned diagnostic |
| API errors | `clientApi` / `featureApi` | Toast or root-level error |
| Query errors | Query adapter layer | Error UI or retry |
| Unexpected errors | Runtime exceptions | Framework error boundary |

## Rules

- Prefer typed, inspectable errors emitted from `clientApi`.
- Validation errors should be mapped close to the user’s input.
- Query adapter owns retry and invalidation policies. Screen/business coordinators may sequence named query/cache-sync operations; presentation components only render states.
- Preserve safe metadata from transport errors when available: `message`, `code`, `status`, `requestId`.
- Treat `message` as public-safe text, not raw diagnostics.
- Treat response-decoding or DTO-mapping failures as `kind: "contract"` with code `api.invalid_response`; keep detailed issues in boundary-owned logs and expose only a generic UI message.
- Reserve `kind: "validation"` for user-correctable input failures. Only this kind may populate form field errors.
- For internal/unexpected/server failures (`5xx` / `INTERNAL_*`), render a generic message (for example: `Something went wrong`).
- Normalize once at the owning adapter boundary, then pass `AppError` through unchanged and branch only on `AppError.kind`.
- Inject `toAppError` into `featureApi` classes so normalization behavior is testable and consistent.
- Assign one operational reporting owner: `clientApi` for transport failures, `featureApi` for contract/mapping failures, and the framework error boundary for unhandled exceptions.
- Do not report the same handled error again from QueryClient defaults, hooks, forms, and components.

## Transport Metadata Pass-Through

When provider-specific errors include useful metadata, adapters should preserve it:

- `message`: preserve only user-safe message
- `code`: preserve machine-readable code when present
- `status`: preserve HTTP status when present
- `requestId`: preserve request correlation identifier when present

This keeps UI handling consistent while still allowing support/debugging workflows.

## Reporting Handoff

Normalization and reporting are separate operations:

```text
transport error -> ApiClientError -> AppError -> safe UI handling
                     |
                     +-> one boundary-owned AppLogger record
```

Sentry, when enabled, is an `AppLogger`/error-boundary adapter. Feature code never imports it directly. Product analytics must not receive operational errors.

## Notifications (Toast) Are a Facade Concern

If you show errors via toast notifications, do it through a toast facade so feature code is not tied to a specific toast library.

Runtime placement (Next.js convention):

```text
src/common/toast/
  types.ts
  provider.ts
  adapters/
    <toast-lib>.ts
```

Framework-specific wiring:

- React forms: `client/frameworks/reactjs/forms-react-hook-form.md`
- React error handling facade: `client/frameworks/reactjs/error-handling.md`
