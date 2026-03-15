# Backend Architecture Documentation

> Canonical backend architecture for Node.js services with layered domain logic, Zod-first contracts, and transport-specific adapters.

See [../README.md](../README.md) for the source-repo overview and [../legacy/README.md](../legacy/README.md) for historical references.

## Focus

This documentation emphasizes:

- Explicit dependency injection with factories
- Clear layer boundaries and responsibilities
- Framework-agnostic business logic
- Zod-first API contracts shared across transports
- Public error handling that is safe by default

## Technology Stack

| Concern | Technology |
| ------- | ---------- |
| Runtime | Node.js |
| Framework | Next.js |
| API Layer | tRPC, OpenAPI/REST migration path |
| Database | PostgreSQL |
| ORM | Drizzle |
| Validation | Zod |
| Logging | Pino |
| Testing | Vitest |

## Canonical Navigation

### Core

| Document | Description |
| -------- | ----------- |
| [Core Index](./core/README.md) | Architecture summary, folder structure, quick reference |
| [Conventions](./core/conventions.md) | Layer responsibilities, DI patterns, kernel rules |
| [Error Handling](./core/error-handling.md) | Public error policy, translation rules, response structure |
| [Transaction](./core/transaction.md) | Transaction manager, patterns, `RequestContext` |
| [Testing Service Layer](./core/testing-service-layer.md) | Layer-specific testing standard |
| [Logging](./core/logging.md) | Pino configuration, request correlation, business events |
| [API Contracts (Zod-First)](./core/api-contracts-zod-first.md) | Canonical contracts for transport coexistence |
| [Zod -> OpenAPI Generation](./core/zod-openapi-generation.md) | Build-time public spec generation |
| [API Response](./core/api-response.md) | Envelope pattern and pagination helpers |
| [Endpoint Naming](./core/endpoint-naming.md) | Capability naming across tRPC/OpenAPI |
| [ID Generation](./core/id-generation.md) | UUID strategy |
| [Rate Limiting](./core/rate-limiting.md) | Agnostic contract and boundaries |
| [Async Jobs + Outbox](./core/async-jobs-outbox.md) | Transactional enqueue and retries |
| [Event Patterns](./core/event-patterns.md) | Event logging, outbox, side-effect procedures |
| [Webhook Architecture](./core/webhook/README.md) | Inbound webhook handling and idempotency |
| [Webhook Testing](./core/webhook/testing/README.md) | Webhook testing strategy and simulator guidance |

### Runtime + Libraries

| Document | Description |
| -------- | ----------- |
| [Runtime Index](./runtime/README.md) | Runtime hierarchy |
| [Node.js Runtime](./runtime/nodejs/README.md) | Node.js libraries and metaframework docs |
| [tRPC Integration](./runtime/nodejs/libraries/trpc/integration.md) | Routers, context, formatter, Drizzle setup |
| [OpenAPI Integration](./runtime/nodejs/libraries/openapi/README.md) | OpenAPI adapter model over shared layers |
| [OpenAPI Parity Testing](./runtime/nodejs/libraries/openapi/parity-testing.md) | Dual-transport parity rules |
| [tRPC Rate Limiting](./runtime/nodejs/libraries/trpc/rate-limiting.md) | Middleware tiers and enforcement patterns |
| [Authentication](./runtime/nodejs/libraries/trpc/authentication.md) | Session/JWT management, middleware, RBAC |
| [Supabase](./runtime/nodejs/libraries/supabase/README.md) | Auth, storage, and database integration patterns |
| [Next.js](./runtime/nodejs/metaframeworks/nextjs/README.md) | Route-handler conventions and server runtime specifics |

## Quick Start

1. Start with [./core/README.md](./core/README.md).
2. Read [./core/conventions.md](./core/conventions.md) and [./core/error-handling.md](./core/error-handling.md) before adding new endpoints or repositories.
3. Add runtime-specific details from [./runtime/nodejs/README.md](./runtime/nodejs/README.md) only when the project actually uses them.
4. Use [../legacy/server/overview.md](../legacy/server/overview.md) only for historical context.

## Layer Decision Flow

```text
Is it a write operation?
  No  -> call a service directly
  Yes -> does it orchestrate multiple services or side effects?
           No  -> call a service directly
           Yes -> call a use case
```

## Folder Contract

All server-side code lives under `src/lib/`.

Examples throughout the docs may use alias shortcuts such as `@/shared/*` and `@/modules/*`.
Those refer to `src/lib/shared/*` and `src/lib/modules/*`.

```text
src/
  app/api/                       transport entrypoints
  lib/shared/                    kernel, infra, utilities
  lib/modules/<module>/          routers, services, repositories, use cases
  drizzle/migrations/            database migrations
```

## Error Contract Summary

- Repositories translate known database constraint errors to domain errors.
- Routers pass `cause` into transport errors and let the formatter control public exposure.
- tRPC docs use `message`, `data.appCode`, `data.requestId`, and optional safe `data.details`.
- 5xx responses never expose raw provider, SQL, stack, or constraint details.

## Historical Reference

Legacy backend material lives under [../legacy/server/overview.md](../legacy/server/overview.md).
It is reference-only and not canonical.
