# Next.js Route Handlers (route.ts)

> Conventions for non-tRPC endpoints implemented via Next.js App Router route handlers.

## Goals

- Return a consistent response envelope (success + error)
- Use typed errors (`AppError`) for known failures
- Include `requestId` in all error responses
- Avoid leaking internal details to the client

## Standard Response Types

Route handlers should return:

- **Success (2xx)**: `ApiResponse<T>` — `{ data: T }`
- **Error (non-2xx)**: `ApiErrorResponse` — `{ code, message, requestId, details? }`

Both types are defined in `shared/kernel/response.ts`.

## Error Handling

Follow `server/core/error-handling.md`:

- Throw domain errors (`AppError` subclasses) for expected cases
- Use `handleError(error, requestId)` to map unknown errors to `{ code: "INTERNAL_ERROR" }`

## Example: GET route with envelope + handleError

```typescript
// app/api/example/route.ts

import { NextResponse } from "next/server";
import { handleError } from "@/shared/infra/http/error-handler";
import type { ApiErrorResponse, ApiResponse } from "@/shared/kernel/response";
import { wrapResponse } from "@/shared/utils/response";

interface ExampleData {
  message: string;
}

export async function GET(req: Request) {
  const requestId = req.headers.get("x-request-id") ?? randomUUID();

  try {
    const data: ExampleData = { message: "Hello" };

    return NextResponse.json<ApiResponse<ExampleData>>(wrapResponse(data));
  } catch (error) {
    const { status, body } = handleError(error, requestId);

    return NextResponse.json<ApiErrorResponse>(body, { status });
  }
}
```

## Notes

- Keep route handlers thin: parse + validate input, call one service/use-case, return response.
- Don’t return `{ data: null }` for not-found. Throw `NotFoundError`.
- Don’t include stack traces in the response.

## Response Type Derivation Rules (Required)

For external route handlers (`app/api/**/route.ts`), enforce compile-time response contracts from domain boundaries.

- Preferred: derive response alias from service interface method return type.
- Use one alias per route method when a file has multiple methods.
- Transitional fallback: `ApiResponse<typeof result>` until interface aliasing is in place.
- Never use `ApiResponse<unknown>` / `ApiResponse<any>` on externally consumed endpoints.

Pattern:

```typescript
type ListPlacesResponse = Awaited<ReturnType<IPlaceService["list"]>>;

export async function GET(req: Request) {
  const result = await makePlaceService().list();
  return NextResponse.json<ApiResponse<ListPlacesResponse>>(wrapResponse(result));
}
```

Minimum contract gates:

```bash
rg -n "ApiResponse<unknown>|ApiResponse<any>" src/app/api --glob '**/route.ts'
rg -n "ApiResponse<\\{[^\\n}]*unknown" src/app/api --glob '**/route.ts'
```
