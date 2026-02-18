# Error Handling (React) — Adapter + Facade

Standardize client error handling so UI code does **not** depend on transport/provider-specific error types (e.g. Axios, tRPC).

Core contract lives in `client/core/error-handling.md`.

## Purpose

- consistent UX (messages, retry, toasts)
- provider swap-ability
- simpler tests (fixtures can use `AppError`)

## Problem

Without a standard, components end up with scattered checks:

- `if (isAxiosError(err)) ...`
- `if (isTRPCClientError(err)) ...`

This leads to:

- duplicated logic
- inconsistent UX
- tight coupling to a library/provider

## Solution

We implement **two layers**.

### 1) Adapter (Required)

Convert provider-specific errors -> one app-level error contract.

- input: `unknown`
- output: `AppError`

Pattern: Adapter

### 2) Facade (Recommended)

Provide a small, consistent API for the rest of the app.

- `normalize(err) -> AppError`
- `message(appErr) -> string`
- `retryable(appErr) -> boolean`
- `applyToForm(appErr, setError)` (react-hook-form)
- `report(appErr)` (logger/Sentry/etc.)

Pattern: Facade (built on top of adapters)

## ASCII Diagram

Adapter (core):

```text
AxiosError / TRPCClientError / Unknown
              |
              v
        toAppError(err)          <-- ADAPTER
              |
              v
           AppError
              |
              v
         UI uses AppError only
```

Facade (preferred entry point):

```text
UI / Hooks / Forms
       |
       v
ErrorHandling Facade              <-- FACADE
(normalize, message, applyToForm)
       |
       v
 toAppError(...)                  <-- ADAPTER
```

## Usage Guidelines

### React Query hooks

- Normalize errors inside hooks or business components.
- Presentation components should never check provider-specific error types.

### Forms (react-hook-form)

- On submit error: normalize to `AppError`.
- If `kind === "validation"`: map field errors via `setError(...)`.
- Otherwise: show a safe user-facing message in UI/toast (generic fallback for internal failures).

### Global handling (optional)

- Centralize reporting/logging in QueryClient defaults (if desired).
- Avoid enforcing UI-specific behavior globally (forms often need local mapping).

## Toasts (Generic, Not Provider-Tied)

Do not bind feature code to a toast library. Use a small toast contract.

Runtime placement (Next.js convention):

```text
src/common/toast/
  types.ts
  provider.ts
  adapters/
    <toast-lib>.ts
```

Minimal contract example:

```ts
export type ToastVariant = "success" | "error" | "info";

export type ToastOptions = {
  title?: string;
  description?: string;
  durationMs?: number;
  variant?: ToastVariant;
};

export interface ToastFacade {
  show(opts: ToastOptions): void;
}
```

## `useCatchErrorToast` (Recommended Helper)

This wraps an async operation and:

- on success: shows a toast using the provided toast options
- on failure: normalizes the error to `AppError`, shows an error toast using the normalized message, and returns a typed result

Behavior notes:

- `successToast` is optional; omit it when you want error handling without success notification.
- Error toast behavior is driven by normalized `AppError` and remains toast-provider-agnostic.

### Result type

```ts
export type AsyncResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: AppError };
```

### Signature

```ts
export function useCatchErrorToast(): <T>(
  fn: () => Promise<T>,
  successToast?: ToastOptions,
) => Promise<AsyncResult<T>>;
```

### Example

```ts
const catchErrorToast = useCatchErrorToast();

const onSubmit = async (data: ProfileFormShape) => {
  const result = await catchErrorToast(
    async () => {
      await updateMut.mutateAsync(data);
      await onSubmitInvalidateQueries();
      await onSubmitRefetch();
      // Optional route transition:
      // router.push(appRoutes.dashboard);
    },
    { description: "Profile updated successfully!", durationMs: 2500 },
  );

  if (!result.ok) {
    // Error toast has already been shown using a safe AppError-derived message.
    // Optional: branch on result.error.kind for additional handling.
    return;
  }
};
```

Notes:

- The only place that knows about provider-specific errors is the adapter layer (`toAppError`).
- `useCatchErrorToast` uses the toast facade (`ToastFacade.show`) under the hood, so it stays toast-library-agnostic.
- Success toast fires only after the wrapped async callback resolves (for example after mutation + invalidate + refetch sequence).

## Do / Don't

Do:

- Normalize once -> `AppError`
- Keep provider checks inside adapters only
- Preserve only user-safe messages in `AppError.message`; use generic fallback for internal failures
- Use facade helpers for consistent UX

Don't:

- Sprinkle provider-specific checks across UI
- Put async error objects into Context to share them
- Leak provider-specific error shapes into views
