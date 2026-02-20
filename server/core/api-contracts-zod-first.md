# API Contracts: Zod-First (tRPC Now, OpenAPI Ready)

> Canonical contract strategy for transport coexistence and migration.

## Purpose

Keep domain and service code transport-agnostic while supporting:

- tRPC as the current transport
- OpenAPI as a migration/parallel transport target

## Source of Truth

`Zod` schemas are the single source of truth for request/response contracts.

- Define schemas once (module-level or shared kernel as needed)
- Derive TypeScript types from schema inference
- Reuse the same schemas in both transport adapters

## Transport Policy

- Current primary transport: `tRPC`
- Migration target transport: `OpenAPI` (REST)
- During migration, both transports may coexist for selected features
- Transport-specific parsing/serialization stays in controller/router adapters only

Domain layers (`usecase`, `service`, `repository`) MUST NOT depend on transport types.

## Architecture

```text
                           Zod Schemas (Canonical)
                                     |
                +--------------------+--------------------+
                |                                         |
                v                                         v
      tRPC Router/Procedure Adapter             OpenAPI Controller/Route Adapter
                |                                         |
                +--------------------+--------------------+
                                     |
                                     v
                          usecase -> service -> repository
```

## Contract Location Guidance

- Shared cross-module contracts: `shared/kernel/schemas/*`
- Module-specific contracts: `modules/<module>/dtos/*` (or `schemas/*` if your module naming standard uses that)
- Keep contract ownership close to the feature unless shared reuse is proven

## Coexistence Rule (Parity Required)

When both transports expose the same business capability:

- Inputs must validate against the same Zod schema
- Error semantics must remain equivalent
- Success envelope/payload shape must remain equivalent by contract
- Add parity tests to prevent drift

See `server/runtime/nodejs/libraries/openapi/parity-testing.md`.

## OpenAPI/Swagger Generation

When publishing API docs/specs, generate OpenAPI from the same Zod contracts.

- Prefer build-time artifact generation (`openapi.json` / `openapi.yaml`)
- Keep generation strategy library-agnostic
- Do not maintain separate hand-written schemas for the same contract

See:

- `./zod-openapi-generation.md`

## References

- OpenAPI Specification: https://spec.openapis.org/oas/latest.html
- OpenAPI Paths Object: https://spec.openapis.org/oas/latest.html#paths-object
- OpenAPI Operation Object: https://spec.openapis.org/oas/latest.html#operation-object

## Adapter Boundary Enforcement

Zod-first contracts remain canonical, and adapter boundaries must expose them explicitly:

- Route/controller adapters should bind success envelopes to concrete response types.
- Avoid transport-level `unknown` response payload types for external APIs.
- OpenAPI operation responses must be derived from the same contract intent and stay synchronized with route behavior.

This keeps coexistence practical: same domain behavior, same validation intent, same envelope semantics across tRPC and OpenAPI.
