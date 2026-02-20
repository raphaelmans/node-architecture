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
export type AppError =
  | {
      kind: "network";
      message: string;
      cause?: unknown;
    }
  | {
      kind: "unauthorized" | "forbidden" | "not_found" | "rate_limited";
      message: string;
      status?: number;
      code?: string;
      requestId?: string;
      cause?: unknown;
    }
  | {
      kind: "validation";
      message: string;
      fieldErrors?: Record<string, string>;
      code?: string;
      requestId?: string;
      cause?: unknown;
    }
  | {
      kind: "unknown";
      message: string;
      cause?: unknown;
    };
```

## Adapter Pattern (Required)

Adapter signature:

- input: `unknown`
- output: `AppError`

```ts
export function toAppError(err: unknown): AppError;
```

Provider-specific checks live **only** inside adapters.

Runtime placement (Next.js convention):

```text
src/common/errors/
  app-error.ts
  to-app-error.ts
  adapters/
    trpc.ts
    ky.ts
```

## Error Types

| Error Type        | Source                 | Handling                        |
| ----------------- | ---------------------- | ------------------------------- |
| Validation errors | Schema boundary        | Field-level messages            |
| API errors        | `clientApi` / `featureApi` | Toast or root-level error    |
| Query errors      | Query adapter layer    | Error UI or retry               |
| Unexpected errors | Runtime exceptions     | Framework error boundary        |

## Rules

- Prefer typed, inspectable errors emitted from `clientApi`.
- Validation errors should be mapped close to the user’s input.
- Query adapter owns retry and invalidation policies; components only render states.
- Preserve safe metadata from transport errors when available: `message`, `code`, `status`, `requestId`.
- Treat `message` as public-safe text, not raw diagnostics.
- Treat response-decoding schema failures (for example `ZodError` while parsing API payloads) as transport contract violations; map to a safe `validation`/`api.invalid_response` message and keep detailed issues in non-UI metadata/logs.
- For internal/unexpected/server failures (`5xx` / `INTERNAL_*`), render a generic message (for example: `Something went wrong`).
- Normalize once at adapter boundary, then branch only on `AppError.kind`.
- Inject `toAppError` into `featureApi` classes so normalization behavior is testable and consistent.

## Transport Metadata Pass-Through

When provider-specific errors include useful metadata, adapters should preserve it:

- `message`: preserve only user-safe message
- `code`: preserve machine-readable code when present
- `status`: preserve HTTP status when present
- `requestId`: preserve request correlation identifier when present

This keeps UI handling consistent while still allowing support/debugging workflows.

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
