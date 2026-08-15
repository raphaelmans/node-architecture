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
app.get("/users/:id", async (req, res) => {
  const input = GetUserInputSchema.parse(req.params);
  const actor = requireActor(req);

  const result = await makeGetUserController().execute(input, actor);
  const response = GetUserResponseSchema.parse(result);

  res.json({ data: response });
});

// Registered once after all routes. Express 5 forwards rejected async handlers here.
app.use(expressErrorMiddleware);
```

`expressErrorMiddleware` must use the shared `AppError.kind` mapping, include the request ID, sanitize unknown failures, and expose no stack or provider diagnostics.

## Rules

- Validate with module-owned shared Zod contracts.
- Establish request/trace observability middleware before routes.
- Resolve one capability controller factory per public route.
- Never resolve a service, use case, repository, or vendor directly from the route.
- Keep `TransactionContext` out of the Express request object.
- Test the Express adapter with a controller stub; test the controller separately.

## References

- [Framework-Neutral Controllers](../../../../core/controllers.md)
- [Express routing](https://expressjs.com/en/5x/starter/basic-routing/)
- [Express error handling](https://expressjs.com/en/guide/error-handling/)
