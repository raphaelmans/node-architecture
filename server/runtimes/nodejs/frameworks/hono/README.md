# Hono Framework Adapter

> Hono is an optional inbound adapter. Hono `Context`, request helpers, middleware, and response helpers remain outside application code.

For repository-aware generation, apply the [Hono Scaffolding](./scaffolding.md) specialization.

The controller/envelope rules below govern application-owned routes. [Better Auth native routes](../../libraries/better-auth/README.md) use its documented handler while retaining the provider protocol and required access restrictions.

## Canonical Flow

```text
Hono route + middleware
  -> framework-neutral controller
    -> one service OR one use case
```

```typescript
import { zValidator } from "@hono/zod-validator";
import type { ContentfulStatusCode } from "hono/utils/http-status";
import { toValidationError } from "@/shared/utils/validation";

const validateParams = zValidator("param", GetUserInputSchema, (result) => {
  if (!result.success) {
    throw toValidationError(result.error, "Invalid request parameters");
  }
});

function toHonoErrorStatus(status: number): ContentfulStatusCode {
  switch (status) {
    case 400:
    case 401:
    case 403:
    case 404:
    case 409:
    case 422:
    case 429:
    case 500:
    case 502:
    case 503:
    case 504:
      return status;
    default:
      return 500;
  }
}

app.get(
  "/users/:id",
  validateParams,
  async (c) => {
    const input = c.req.valid("param");
    const actor = c.get("actor"); // established by typed auth middleware

    const result = await makeGetUserController().execute(input, actor);
    const response = GetUserResponseSchema.parse(result);

    return c.json({ data: response });
  },
);

// Registered once. Validator errors are thrown into the same central mapping.
app.onError((error, c) => {
  const { status, body } = handleError(error, c.get("requestId"));
  return c.json(body, toHonoErrorStatus(status));
});
```

## Rules

- Hono middleware owns authentication, rate limiting, and observability scope.
- Services/use cases own ownership, tenant, domain-role, and operation-specific authorization.
- Every `zValidator` uses a hook that throws the shared `ValidationError`; do
  not allow its default response to bypass the canonical error envelope.
- Narrow the framework-neutral numeric HTTP status at the Hono boundary before
  passing it to typed response helpers such as `c.json()`.
- The route validates shared input, calls one controller, validates the shared response, and serializes with `c.json()`.
- Never pass Hono `Context` to a controller, use case, service, or repository.
- Never store `TransactionContext` in Hono context variables.
- On Node.js, observability may use the same OpenTelemetry/`AsyncLocalStorage` adapter as other Node frameworks. Other Hono runtimes require a runtime-specific implementation of the same core policy.
- Test the Hono adapter with a controller stub; test the controller separately.

## References

- [Framework-Neutral Controllers](../../../../core/controllers.md)
- [Hono validation](https://hono.dev/docs/guides/validation)
- [Hono context and JSON responses](https://hono.dev/docs/api/context)
- [Hono error handling](https://hono.dev/docs/api/hono#error-handling)
