# Express Framework Adapter

> Express is an optional inbound adapter. It does not replace or redefine the core controller/use-case/service/repository architecture.

## Canonical Flow

```text
Express route + middleware
  -> framework-neutral controller
    -> one service OR one use case
```

The Express layer owns `Request`, `Response`, middleware ordering, input parsing, authentication extraction, request observability, the success envelope, and central HTTP error mapping. No Express type crosses the controller boundary.

```typescript
// Express 5
import { parseRequestInput } from "@/shared/infra/http/validation";

app.get("/users/:id", async (req, res) => {
  const input = parseRequestInput(GetUserInputSchema, req.params);
  const actor = requireActor(req);

  const result = await makeGetUserController().execute(input, actor);
  const response = GetUserResponseSchema.parse(result);

  res.json({ data: response });
});

// Registered once after all routes. Express 5 forwards rejected async handlers here.
app.use(expressErrorMiddleware);
```

`parseRequestInput` converts a failed Zod parse to the shared
`ValidationError`; it never lets a raw `ZodError` reach the generic error
middleware. The parser is transport infrastructure because malformed request
encoding and input are transport concerns.

```typescript
export function expressErrorMiddleware(error, req, res, _next) {
  const { status, body } = handleError(error, req.observability.requestId);
  res.status(status).json(body);
}
```

`expressErrorMiddleware` uses the shared `AppError.kind` mapping, includes the
request ID, sanitizes unknown failures, and exposes no stack or provider
diagnostics. This guide assumes Express 5; Express 4 requires an async-handler
wrapper that forwards rejected promises to `next(error)`.

## Rules

- Validate with module-owned shared Zod contracts.
- Normalize Zod failures to `ValidationError` before central HTTP mapping.
- Establish request/trace observability middleware before routes.
- Resolve one capability controller factory per public route.
- Never resolve a service, use case, repository, or vendor directly from the route.
- Keep `TransactionContext` out of the Express request object.
- Test the Express adapter with a controller stub; test the controller separately.

## References

- [Framework-Neutral Controllers](../../../../core/controllers.md)
- [Express routing](https://expressjs.com/en/5x/starter/basic-routing/)
- [Express error handling](https://expressjs.com/en/guide/error-handling/)
