# Hono Framework Adapter

> Hono is an optional inbound adapter. Hono `Context`, request helpers, middleware, and response helpers remain outside application code.

## Canonical Flow

```text
Hono route + middleware
  -> framework-neutral controller
    -> one service OR one use case
```

```typescript
import { zValidator } from "@hono/zod-validator";

app.get(
  "/users/:id",
  zValidator("param", GetUserInputSchema),
  async (c) => {
    const input = c.req.valid("param");
    const actor = c.get("actor"); // established by typed auth middleware

    const result = await makeGetUserController().execute(input, actor);
    const response = GetUserResponseSchema.parse(result);

    return c.json({ data: response });
  },
);

// Registered once. It derives HTTP status from AppError.kind and sanitizes 5xx.
app.onError(honoErrorHandler);
```

## Rules

- Hono middleware owns authentication, rate limiting, and observability scope.
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
