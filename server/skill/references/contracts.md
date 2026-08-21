# Contracts Slice

Use this slice for shared Zod wire contracts, validation boundaries, commands and view models, envelopes, pagination, endpoint naming, public errors, OpenAPI generation, and transport parity.

## Contract Ownership

Define each public capability once under its owning module:

```text
src/lib/modules/<module>/shared/contracts/   # single-project mapping
  create-<entity>.contract.ts
```

In a monorepo, use an activated `packages/contracts/<module>/` boundary when the schema crosses packages. Capability controllers and transport apps consume its public exports; client code never imports a server app or capability package for wire schemas.

Keep these schemas isomorphic: no server-only imports, database entities, environment reads, provider types, or transforms with hidden runtime dependencies.

Separate shapes deliberately:

```text
wire input -> controller -> server-only command -> service/use case
entity/result -> controller -> public response payload -> adapter envelope
```

Infer TypeScript wire types from the canonical schemas. Do not hand-maintain duplicate client, tRPC, REST, or OpenAPI DTOs.

## Adapter Validation

Parse untrusted input at the adapter and normalize parser failures:

```ts
const body = await parseJsonRequestBody(request);
const input = parseRequestInput(CreateUserInputSchema, body);
const result = await makeCreateUserController().execute(input, actor);
const payload = CreateUserResponseSchema.parse(result);
return json(wrapResponse(payload));
```

- Malformed JSON and Zod input failures become the shared `ValidationError`.
- Put a sanitized path/message projection in `publicDetails`; the second
  `AppError` constructor argument is internal logging context and is not sent
  to clients.
- Response-schema failures are server contract bugs and become sanitized 500 responses.
- Hono validator hooks must throw the shared error instead of returning a framework-default envelope.
- tRPC `.input()` may own wire parsing, but the procedure still calls the same controller and returns the same payload contract.

## Envelopes and Pagination

Use one success envelope:

```ts
type ApiResponse<T> = { data: T };
```

Use the canonical public error shape:

```ts
type ApiErrorResponse = {
  code: string;
  message: string;
  requestId: string;
  details?: Record<string, unknown>;
};
```

Expose `details` only when explicitly allowlisted and safe. Never serialize provider messages, SQL, constraints, stack traces, or raw validation objects.

For numeric pagination, use `limit`, `offset`, and `nextOffset` with a regular
query. Reserve `cursor` for opaque stable traversal keys. A tRPC
`useInfiniteQuery` capability must accept an optional field named `cursor` and
return an opaque `nextCursor`; never feed `nextOffset` into the infinite-query
contract. Validate collection payloads with the shared pagination
schema/helper rather than repeating envelope definitions.

## Error Contract

- Throw typed `AppError` subclasses for expected domain/application failures.
- Map `AppError.kind` centrally to HTTP or RPC status/code.
- Translate known database/provider failures at their adapter boundary.
- Preserve the domain error as `cause` when wrapping it for a transport such as tRPC.
- Sanitize unknown errors to a stable internal error code and safe message.
- Log errors once at the central owning boundary.

Use `NotFoundError` for missing resources, `ConflictError` for exact known uniqueness conflicts, `BusinessRuleError` for valid input that violates a domain rule, and gateway/unavailable/timeout errors for provider failures according to retry semantics.

## tRPC and OpenAPI Coexistence

Treat tRPC and OpenAPI as adapters over the same capability controller and contracts. Keep method/path/status concerns in OpenAPI and RPC path/procedure concerns in tRPC. Require parity fixtures for payloads, authorization, errors, and side effects before shifting traffic.

Generate OpenAPI from the canonical Zod schemas at build time. Fail CI when the generated artifact drifts; do not hand-edit generated specifications.

## Review Checklist

- One canonical input and payload schema exists per capability.
- Envelopes are kernel-owned and not nested inside payload schemas.
- Server-only commands and entities do not cross the wire boundary.
- Every adapter normalizes malformed input to the same error family.
- Response payloads are parsed before serialization.
- Public error messages and details are explicitly safe.
- Validation issue details use the allowlisted path/message projection.
- tRPC/OpenAPI variants share controllers and pass parity tests.
- Numeric offsets are not mislabeled as cursors.

## Derivation Sources

Derived from the Zod-first contract, API response, endpoint naming, error handling, OpenAPI generation, and OpenAPI runtime guides. Exact paths and fingerprints are maintained outside the portable skill package.
