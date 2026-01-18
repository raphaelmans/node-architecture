# Non-tRPC HTTP Clients with `ky`

> Conventions for browser-side HTTP clients that call Next.js `route.ts` endpoints.

## Goals

- Use a consistent HTTP client wrapper (`ky`)
- Decode the standard server envelope (`ApiResponse<T>` / `ApiErrorResponse>`)
- Throw typed, inspectable errors (aligned with server error-handling)
- Integrate cleanly with TanStack Query hooks

## Standard Response Envelope

Non-tRPC endpoints must follow the server conventions:

- **Success (2xx)**: `ApiResponse<T>` → `{ data: T }`
- **Error (non-2xx)**: `ApiErrorResponse` → `{ code, message, requestId, details? }`

Both are defined in `shared/kernel/response.ts`.

## Ky instance

Use a shared `ky` instance and disable `throwHttpErrors` so you can read error bodies:

```typescript
import ky from "ky";

export const api = ky.create({
  throwHttpErrors: false,
  timeout: 30_000,
});
```

## Typed client error

Throw a typed error so UI + hooks can inspect `code` and `requestId`.

```typescript
import type { ApiErrorResponse } from "@/shared/kernel/response";

export class ApiClientError extends Error {
  readonly code: string;
  readonly requestId: string;
  readonly httpStatus: number;
  readonly details?: Record<string, unknown>;

  constructor(args: {
    code: string;
    message: string;
    requestId: string;
    httpStatus: number;
    details?: Record<string, unknown>;
  }) {
    super(args.message);
    this.name = "ApiClientError";
    this.code = args.code;
    this.requestId = args.requestId;
    this.httpStatus = args.httpStatus;
    this.details = args.details;
  }
}

export const isApiClientError = (error: unknown): error is ApiClientError =>
  error instanceof ApiClientError;

const isApiErrorResponse = (value: unknown): value is ApiErrorResponse => {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.code === "string" &&
    typeof record.message === "string" &&
    typeof record.requestId === "string"
  );
};
```

## Example client function

```typescript
import type { ApiErrorResponse, ApiResponse } from "@/shared/kernel/response";

export async function previewGoogleLoc(url: string) {
  const response = await api.post("api/poc/google-loc", {
    json: { url },
  });

  const json = (await response.json()) as unknown;

  if (!response.ok) {
    if (isApiErrorResponse(json)) {
      throw new ApiClientError({
        code: json.code,
        message: json.message,
        requestId: json.requestId,
        httpStatus: response.status,
        details: json.details,
      });
    }

    throw new ApiClientError({
      code: "INTERNAL_ERROR",
      message: "Request failed",
      requestId: "unknown",
      httpStatus: response.status,
    });
  }

  const body = json as ApiResponse<{ lat?: number; lng?: number }>;
  return body.data;
}
```

## React Query integration

```typescript
import { useMutation } from "@tanstack/react-query";

export function useGoogleLocPreviewMutation() {
  return useMutation({
    mutationFn: ({ url }: { url: string }) => previewGoogleLoc(url),
  });
}
```

## Notes

- Do not leak internal error details in `message`; use `details` for additional context.
- Always include `requestId` in server responses so clients can show it or log it.
