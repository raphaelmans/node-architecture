# OpenAPI Integration (Node.js Runtime)

> Runtime-specific guidance for OpenAPI transport alongside existing tRPC transport.

## Status

- Current primary transport: `tRPC`
- OpenAPI: supported as migration/coexistence transport

This doc defines OpenAPI as a transport adapter over the same domain layers.

## Core Rules

- Reuse canonical Zod contracts from `server/core/api-contracts-zod-first.md`
- Follow `server/core/zod-openapi-generation.md` for spec/doc generation standard
- Follow capability naming from `server/core/endpoint-naming.md`
- Keep controller/route handlers thin (parse, validate, invoke, map)
- Do not move business logic into route handlers
- Keep transport errors mapped to the shared app error contract
- Follow shared envelope/error response guidance from `server/core/api-response.md`

## Architecture

```text
HTTP Request (OpenAPI route)
  -> validate with shared Zod schema
  -> call usecase/service
  -> map domain result/error to HTTP response
```

## Coexistence with tRPC

- tRPC and OpenAPI may expose the same capability during migration
- Both must call the same usecase/service path
- Both must satisfy parity tests before rollout

See `./parity-testing.md`.

## Example Mapping

| Capability | tRPC | OpenAPI |
| --- | --- | --- |
| Create profile | `profile.create` | `POST /profiles` |
| Update profile | `profile.update` | `PATCH /profiles/{profileId}` |

## References

- OpenAPI Specification: https://spec.openapis.org/oas/latest.html
- OpenAPI Initiative: https://www.openapis.org/

## External Contract Hardening (Required)

For externally consumed OpenAPI surfaces:

- Success response schemas must be explicit per operation (or per clearly scoped response family).
- Do not publish operation success schemas with `data: unknown`.
- Keep envelope parity with runtime route handlers (`ApiResponse<T>` for 2xx, shared error envelope for non-2xx).
- Treat route behavior + OpenAPI document updates as a single change unit to avoid drift.

Practical rule:

- If route payload changes, update operation response schema in the same PR.
