# Backend Architecture Documentation

> Canonical backend architecture for Node.js services with layered domain logic, Zod-first contracts, and transport-specific adapters.

See [../README.md](../README.md) for the source-repo overview and [../legacy/README.md](../legacy/README.md) for historical references.

Interactive companion: [Server Architecture Field Guide](../assets/server-architecture-guide.html).

## Focus

This documentation emphasizes:

- Explicit dependency injection with factories
- Clear layer boundaries and responsibilities
- Framework-neutral controllers between transport adapters and application logic
- Framework-agnostic business logic
- Zod-first API contracts shared across transports
- Public error handling that is safe by default
- Separate operational logging, tracing, product analytics, and transaction contexts

## Technology Stack

| Concern | Technology |
| ------- | ---------- |
| Runtime | Node.js |
| Framework adapters | Next.js, Express, or Hono; tRPC/OpenAPI as applicable |
| API Layer | tRPC, OpenAPI/REST migration path |
| Database | PostgreSQL |
| ORM | Drizzle |
| Validation | Zod |
| Logging | Pino behind `AppLogger` |
| Tracing | OpenTelemetry context and semantic conventions |
| Testing | Vitest |

## Canonical Navigation

### Core

| Document | Description |
| -------- | ----------- |
| [Core Index](./core/README.md) | Architecture summary, folder structure, quick reference |
| [Conventions](./core/conventions.md) | Layer responsibilities, DI patterns, kernel rules |
| [Framework-Neutral Controllers](./core/controllers.md) | Portable capability boundary shared by Next.js, Express, Hono, tRPC, OpenAPI, and other adapters |
| [Error Handling](./core/error-handling.md) | Public error policy, translation rules, response structure |
| [Transaction](./core/transaction.md) | Transaction manager, patterns, transaction-only options |
| [Server Layer Testing](./core/testing-service-layer.md) | Adapter/controller/use-case/service/repository testing standard |
| [Observability](./core/observability.md) | Request/trace correlation, async propagation, logger DI |
| [Logging](./core/logging.md) | Operational logging contract and ownership |
| [Product Analytics](./core/product-analytics.md) | Typed analytics events, vendor adapters, composite delivery |
| [API Contracts (Zod-First)](./core/api-contracts-zod-first.md) | Canonical contracts for transport coexistence |
| [Zod -> OpenAPI Generation](./core/zod-openapi-generation.md) | Build-time public spec generation |
| [API Response](./core/api-response.md) | Envelope pattern and pagination helpers |
| [Endpoint Naming](./core/endpoint-naming.md) | Capability naming across tRPC/OpenAPI |
| [ID Generation](./core/id-generation.md) | UUID strategy |
| [Rate Limiting](./core/rate-limiting.md) | Agnostic contract and boundaries |
| [Async Jobs + Outbox](./core/async-jobs-outbox.md) | Transactional enqueue and retries |
| [Event Patterns](./core/event-patterns.md) | Domain event logs, outbox, analytics delivery, side-effect procedures |
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
| [Pino Logger Adapter](./runtime/nodejs/libraries/pino/README.md) | Node.js implementation of the core `AppLogger` port |
| [tRPC Rate Limiting](./runtime/nodejs/libraries/trpc/rate-limiting.md) | Middleware tiers and enforcement patterns |
| [Authentication](./runtime/nodejs/libraries/trpc/authentication.md) | Session/JWT management, middleware, RBAC |
| [Supabase](./runtime/nodejs/libraries/supabase/README.md) | Auth, storage, and database integration patterns |
| [Next.js](./runtime/nodejs/metaframeworks/nextjs/README.md) | Route-handler conventions and server runtime specifics |
| [Express](./runtime/nodejs/metaframeworks/express/README.md) | Thin Express routes and central error middleware over shared controllers |
| [Hono](./runtime/nodejs/metaframeworks/hono/README.md) | Thin Hono handlers, validation, and error mapping over shared controllers |

## Quick Start

1. Start with [./core/README.md](./core/README.md).
2. Read [./core/conventions.md](./core/conventions.md), [./core/controllers.md](./core/controllers.md), and [./core/error-handling.md](./core/error-handling.md) before adding new endpoints or repositories.
3. Add runtime-specific details from [./runtime/nodejs/README.md](./runtime/nodejs/README.md) only when the project actually uses them.
4. Use [../legacy/server/overview.md](../legacy/server/overview.md) only for historical context.

## Layer Decision Flow

```text
Framework adapter -> capability controller
  Controller asks: is it a write operation?
    No  -> call one service
    Yes -> does it orchestrate multiple services or side effects?
             No  -> call one service
             Yes -> call one use case
```

## Folder Contract

All server-side code lives under `src/lib/`.

Examples throughout the docs may use alias shortcuts such as `@/shared/*` and `@/modules/*`.
Those refer to `src/lib/shared/*` and `src/lib/modules/*`.

```text
src/
  app/api/                       Next.js entrypoints (when selected)
  routes/                        Express/Hono entrypoints (when selected)
  lib/shared/                    kernel, infra, utilities
  lib/modules/<module>/shared/contracts/  cross-runtime Zod API contracts
  lib/modules/<module>/          controllers, routers/adapters, services, repositories, use cases
  features/<feature>/            client feature APIs, query adapters, UI
  drizzle/migrations/            database migrations
```

Choose the entrypoint folder for the framework in use. The inward `lib/shared/` and `lib/modules/` architecture does not change.

Client and server import public request/response contracts from the owning module's `shared/contracts/` directory. Client code never imports database entities, repositories, services, or server-only command DTOs.

## Error Contract Summary

- Repositories translate known database constraint errors to domain errors.
- Shared transport middleware maps `AppError.kind` once and preserves the domain error as `cause` where the transport supports it.
- tRPC docs use `message`, `data.appCode`, `data.requestId`, and optional safe `data.details`.
- 5xx responses never expose raw provider, SQL, stack, or constraint details.

## Historical Reference

Legacy backend material lives under [../legacy/server/overview.md](../legacy/server/overview.md).
It is reference-only and not canonical.
