# Zod to OpenAPI/Swagger Generation

> Canonical standard for generating public API documentation from Zod-first contracts.

## Purpose

Generate OpenAPI documentation from existing Zod schemas so the project can:

- keep one contract source of truth
- reduce schema drift between implementation and docs
- prepare for public API docs and SDK generation in the future

## Scope

This document defines:

- how to treat Zod schemas as canonical API contracts
- how to produce OpenAPI artifacts at build time
- how this coexists with both tRPC and OpenAPI transports

This document does not force one specific library implementation.

## Core Rules

- Zod schemas are the canonical source of interface/type contracts.
- OpenAPI specs MUST be derived from those Zod contracts.
- tRPC and OpenAPI are different transports and MUST remain separate adapter layers.
- Business/domain layers MUST NOT depend on transport-specific contract objects.
- If a capability is exposed in both transports, parity tests remain required.

See:

- `./api-contracts-zod-first.md`
- `../runtime/nodejs/libraries/openapi/parity-testing.md`

## Architecture

```text
Zod Schemas (canonical)
        |
        v
OpenAPI Generator (library-agnostic strategy)
        |
        v
openapi.json / openapi.yaml (build artifact)
        |
        +--> Swagger UI / ReDoc / external portal
        +--> SDK generation pipeline

tRPC transport ----------\
                          +--> same usecase/service/repository
OpenAPI transport -------/
```

## Recommended Generation Strategy

Keep the strategy library-agnostic:

1. Register/declare API operations from transport-facing contracts.
2. Reuse Zod schemas for request/response payloads.
3. Enrich schemas with documentation metadata (descriptions/examples).
4. Generate OpenAPI spec artifact in build/CI.

Optional implementation references:

- `zod-openapi`
- `@asteasolutions/zod-to-openapi`

Choose tooling based on team ergonomics, OAS support, and maintenance cost.

## Build-Time Artifact Standard (Default)

Default approach:

- generate spec at build time
- output artifact for future public docs

Suggested artifact paths:

- `openapi/openapi.json`
- optional `openapi/openapi.yaml`

Suggested command convention:

```bash
pnpm openapi:generate
```

## CI and Quality Gates

- generation command must pass in CI
- if artifact is committed, CI should detect drift
- dual-transport capabilities should pass parity tests before rollout

## Metadata Conventions (Recommended)

Add documentation metadata close to schema definitions:

- field/property descriptions
- request/response examples
- enum/value meaning where needed
- deprecation markers for phased migrations

Align operation names with:

- `./endpoint-naming.md`

## Transport Coexistence Notes

- Current primary transport is `tRPC`.
- OpenAPI can be introduced progressively for migration/public API use.
- Generated OpenAPI docs do not change domain architecture or service boundaries.

## References

- OpenAPI Specification: https://spec.openapis.org/oas/latest.html
- OpenAPI Paths Object: https://spec.openapis.org/oas/latest.html#paths-object
- OpenAPI Operation Object: https://spec.openapis.org/oas/latest.html#operation-object
- Swagger Docs: https://swagger.io/docs/
- zod-openapi (reference): https://www.npmjs.com/package/zod-openapi
- @asteasolutions/zod-to-openapi (reference): https://www.npmjs.com/package/@asteasolutions/zod-to-openapi
