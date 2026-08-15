# OpenAPI Integration (Node.js Runtime)

> Runtime-specific guidance for OpenAPI transport alongside existing tRPC transport.

## Status

- Current primary transport: `tRPC`
- OpenAPI: supported as migration/coexistence transport

This doc defines OpenAPI as a transport adapter over the same domain layers.

## Core Rules

- Reuse canonical Zod contracts from [API Contracts](../../../../core/api-contracts-zod-first.md)
- Follow [Zod to OpenAPI Generation](../../../../core/zod-openapi-generation.md) for spec/doc generation
- Follow capability naming from [Endpoint Naming](../../../../core/endpoint-naming.md)
- Follow the framework-neutral [Controller Standard](../../../../core/controllers.md)
- Keep OpenAPI route handlers thin (parse, validate, invoke the controller, serialize)
- Do not move business logic into route handlers
- Map `AppError.kind` once in shared HTTP infrastructure; do not repeat status mappings in controllers
- Follow shared envelope/error response guidance from [API Response](../../../../core/api-response.md)
- Establish the [Observability](../../../../core/observability.md) request scope before invoking application code
- Resolve the capability controller through a module factory; never construct inner dependencies in the route

## Architecture

```text
HTTP Request (OpenAPI route)
  -> request observability scope
  -> validate with shared input schema
  -> factory-created framework-neutral controller
  -> controller calls one service OR use case
  -> validate shared response schema
  -> shared HTTP error/envelope adapter
```

| Concern | Owner |
| --- | --- |
| HTTP method/path/status/headers | OpenAPI framework adapter |
| Input/output wire shape | Module `shared/contracts/` |
| Contract/command/result mapping | Framework-neutral controller |
| Workflow and transaction | Use case or single-domain service |
| Domain rules | Service |
| Persistence | Repository |
| HTTP mapping from domain errors | Shared HTTP adapter |
| Request/trace fields | Async observability scope + `AppLogger` adapter |

`TransactionContext` is passed only to database-participating methods. It is never merged with an HTTP request context or tracing context.

## Coexistence with tRPC

- tRPC and OpenAPI may expose the same capability during migration
- Both must call the same capability controller
- Both must satisfy parity tests before rollout

See [OpenAPI Parity Testing](./parity-testing.md).

## Example Mapping

| Capability | tRPC | OpenAPI |
| --- | --- | --- |
| Create profile | `profile.create` | `POST /profiles` |
| Update profile | `profile.update` | `PATCH /profiles/{profileId}` |

## References

- OpenAPI Specification: https://spec.openapis.org/oas/latest.html
- OpenAPI Initiative: https://www.openapis.org/

## Adapter Test Pattern

- Contract tests exercise each shared Zod input/response schema once.
- Route-adapter tests verify parsing, controller delegation, status/envelope mapping, and auth policy.
- Controller tests verify command/result mapping and one service/use-case call without framework types.
- Service/use-case tests remain transport-independent.
- Error-adapter tests exhaustively map every `AppError.kind` and sanitize unknown errors.
- Dual-exposed capabilities additionally follow [Parity Testing](./parity-testing.md).

## Endpoint Checklist

- [ ] Shared input and response contracts imported from the owning module
- [ ] Malformed JSON and Zod input failures translate to `ValidationError`
- [ ] Request observability scope established at the entrypoint
- [ ] One factory-created framework-neutral controller invoked
- [ ] Result parsed/mapped through the shared response schema
- [ ] Shared HTTP error mapping used
- [ ] No ORM/vendor type leaks into the public contract
- [ ] OpenAPI operation and runtime route changed together
- [ ] Contract, framework-adapter, controller, and application-layer tests present

## External Contract Hardening (Required)

For externally consumed OpenAPI surfaces:

- Success response schemas must be explicit per operation (or per clearly scoped response family).
- Do not publish operation success schemas with `data: unknown`.
- Keep envelope parity with runtime route handlers (`ApiResponse<T>` for 2xx, shared error envelope for non-2xx).
- Treat route behavior + OpenAPI document updates as a single change unit to avoid drift.

Practical rule:

- If route payload changes, update operation response schema in the same PR.
