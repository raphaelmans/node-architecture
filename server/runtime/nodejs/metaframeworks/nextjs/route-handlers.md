# Next.js Route Handlers (route.ts)

> Conventions for non-tRPC endpoints implemented via Next.js App Router route handlers.

## Goals

- Return a consistent response envelope (success + error)
- Use typed errors (`AppError`) for known failures
- Include `requestId` in all error responses
- Avoid leaking internal details to the client
- Establish observability scope before calling application code
- Resolve a framework-neutral controller through its factory

## Standard Response Types

Route handlers should return:

- **Success (2xx)**: `ApiResponse<T>` — `{ data: T }`
- **Error (non-2xx)**: `ApiErrorResponse` — `{ code, message, requestId, details? }`

Both types are defined in `shared/kernel/response.ts`.

## Error Handling

Follow `server/core/error-handling.md`:

- Throw domain errors (`AppError` subclasses) for expected cases
- Use `handleError(error, requestId)` to map unknown errors to `{ code: "INTERNAL_ERROR" }`

```typescript
// shared/infra/http/request.ts

import { ValidationError } from "@/shared/kernel/errors";

export async function parseJsonRequestBody(
  request: Request,
): Promise<unknown> {
  try {
    return await request.json();
  } catch {
    throw new ValidationError("Malformed JSON request body");
  }
}
```

## Example: POST create route

```typescript
// app/api/users/route.ts

import { NextResponse } from "next/server";
import { handleError } from "@/shared/infra/http/error-handler";
import { parseJsonRequestBody } from "@/shared/infra/http/request";
import { withRequestObservability } from "@/shared/infra/observability/request-context";
import { parseRequestInput } from "@/shared/infra/http/validation";
import type { ApiErrorResponse, ApiResponse } from "@/shared/kernel/response";
import { wrapResponse } from "@/shared/utils/response";
import {
  CreateUserInputSchema,
  CreateUserResponseSchema,
  type CreateUserResponse,
} from "@/modules/user/shared/contracts";
import { makeCreateUserController } from "@/modules/user/factories/create-user.factory";

export async function POST(request: Request) {
  return withRequestObservability(request, async ({ requestId }) => {
    try {
      const body = await parseJsonRequestBody(request);
      const input = parseRequestInput(CreateUserInputSchema, body);
      const actor = await authenticateNextRequest(request);

      const result = await makeCreateUserController().execute(input, actor);
      const response = CreateUserResponseSchema.parse(result);

      return NextResponse.json<ApiResponse<CreateUserResponse>>(
        wrapResponse(response),
        { status: 201 },
      );
    } catch (error) {
      const { status, body } = handleError(error, requestId);

      return NextResponse.json<ApiErrorResponse>(body, { status });
    }
  });
}
```

`withRequestObservability` accepts or creates the application `requestId`, activates OpenTelemetry/async context, and logs the request lifecycle. The injected `AppLogger` reads that active context, so the route does not pass logging or tracing identifiers through controller, use-case, or service method parameters.

`parseJsonRequestBody` translates malformed JSON into a transport-neutral
`ValidationError`; `parseRequestInput` translates Zod input failures into the
same error family. A response-schema failure is intentionally not converted to
a 4xx error—it indicates a server contract bug and is sanitized as a 500.

The client `UserApi` imports `CreateUserInputSchema` and `CreateUserResponseSchema` from the same `shared/contracts/` module. The framework-neutral controller owns entity/result-to-response mapping; the route validates the resulting shared response before serialization.

The factory owns dependency wiring:

```typescript
// modules/user/factories/create-user.factory.ts

export function makeCreateUserController(): ICreateUserController {
  return new CreateUserController(
    new CreateUserUseCase(
      makeUserService(),
      getContainer().appLogger,
      getContainer().productAnalytics,
    ),
  );
}
```

- `AppLogger` is for operational logs.
- `ProductAnalytics` is for typed user/business events.
- `TransactionOptions` carries only an optional database transaction.
- None of these concerns are combined into one context or service locator.

## Notes

- `route.ts` is always the Next.js framework adapter, never the framework-neutral controller.
- Keep route handlers thin: extract/authenticate + validate input, call one controller, validate/serialize the response.
- Call one factory-created controller; do not instantiate or call services, use cases, repositories, or vendor adapters in the route.
- The controller converts capability-level null outcomes to `NotFoundError`; the route does not repeat that rule.
- Don’t include stack traces in the response.
- Do not manually create `traceId`/`spanId`; obtain them from the active OpenTelemetry span.
- Operational JSON records serialize trace context as `trace_id`, `span_id`, and `trace_flags`; the request ID uses the configured application namespace.
- Do not pass observability context through `TransactionOptions`.

## Response Type Derivation Rules (Required)

For external route handlers (`app/api/**/route.ts`), enforce compile-time response contracts from the canonical shared Zod contract.

- Preferred: infer/export the response type from `src/lib/modules/<module>/shared/contracts/`.
- Use one alias per route method when a file has multiple methods.
- Parse the result with the shared response schema before serialization.
- Transitional fallback: derive from a controller interface only while migrating that endpoint to a shared response contract.
- Never use `ApiResponse<unknown>` / `ApiResponse<any>` on externally consumed endpoints.

Pattern:

```typescript
import {
  ListPlacesResponseSchema,
  type ListPlacesResponse,
} from "@/modules/place/shared/contracts";

export async function GET(req: Request) {
  return withRequestObservability(req, async () => {
    const result = await makeListPlacesController().execute({}, actor);
    const response = ListPlacesResponseSchema.parse(result);
    return NextResponse.json<ApiResponse<ListPlacesResponse>>(
      wrapResponse(response),
    );
  });
}
```

Minimum contract gates:

```bash
rg -n "ApiResponse<unknown>|ApiResponse<any>" src/app/api --glob '**/route.ts'
rg -n "ApiResponse<\\{[^\\n}]*unknown" src/app/api --glob '**/route.ts'
```
