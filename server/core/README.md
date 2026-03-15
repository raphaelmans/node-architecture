# Backend Core README

> High-level overview of the backend architecture, linking to detailed documentation for each concern.

## Architecture Summary

This backend follows a **disciplined layered architecture** with explicit boundaries, manual dependency injection, and clear separation of concerns.

Testability is a first-class quality gate: modules are expected to follow interface-driven boundaries and layer-appropriate tests.

```
┌─────────────────────────────────────────────────────────────┐
│                      Router/Controller                       │
│               (HTTP/tRPC/OpenAPI concerns)                   │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│        Use Case         │     │          Service            │
│  (Multi-service         │     │  (Single-service business   │
│   orchestration)        │     │   logic + transactions)     │
└───────────┬─────────────┘     └──────────────┬──────────────┘
            │                                  │
            └───────────────┬──────────────────┘
                            ▼
              ┌─────────────────────────┐
              │       Repository        │
              │  (Data access layer)    │
              └───────────┬─────────────┘
                          ▼
              ┌─────────────────────────┐
              │        Database         │
              └─────────────────────────┘
```

## Core Principles

| Principle                                | Description                                  |
| ---------------------------------------- | -------------------------------------------- |
| **Explicit over implicit**               | No magic, clear dependency flow              |
| **Composition over coupling**            | Small, focused units composed together       |
| **Manual DI with factories**             | Explicit wiring, easy testing                |
| **Infrastructure is replaceable**        | Business logic doesn't know about frameworks |
| **Business logic is framework-agnostic** | Services and use cases are pure TypeScript   |

## Technology Stack

| Concern    | Technology                               |
| ---------- | ---------------------------------------- |
| Runtime    | Node.js (serverless)                     |
| Framework  | Next.js                                  |
| API Layer  | tRPC (current), OpenAPI (migration path) |
| Database   | PostgreSQL                               |
| ORM        | Drizzle                                  |
| Validation | Zod (canonical contracts)                |
| Logging    | Pino                                     |
| Testing    | Vitest                                   |

## Layer Responsibilities

| Layer                 | Responsibility                                 | Transactions               |
| --------------------- | ---------------------------------------------- | -------------------------- |
| **Router/Controller** | HTTP concerns, input validation, error mapping | No                         |
| **Use Case**          | Multi-service orchestration, side effects      | Yes (owns)                 |
| **Service**           | Business logic, single-service operations      | Yes (owns or receives ctx) |
| **Repository**        | Data access, entity persistence                | No (receives context)      |

### Router Decision Flow

```
Is it a write operation?
├── No (read) → Call Service directly
└── Yes (write)
    └── Does it involve multiple services or side effects?
        ├── No → Call Service directly (service owns transaction)
        └── Yes → Call Use Case (use case owns transaction)
```

## Data Flow

### Entities vs DTOs

| Type       | Source      | Used By             | Purpose                         |
| ---------- | ----------- | ------------------- | ------------------------------- |
| **Entity** | drizzle-zod | Repository, Service | Internal data representation    |
| **DTO**    | Zod schemas | Router, Use Case    | API contracts, input validation |

**Rule**: Return entities by default. Use DTOs when transforming, omitting sensitive fields, or combining data.

### Request Flow Example

```
Client Request
     │
     ▼
┌────────────────────────────────────┐
│  tRPC Router OR OpenAPI Controller │ ─── Validates input (Zod)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Use Case     │ ─── Multi-service orchestration (if needed)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Service      │ ─── Business logic + transaction
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Repository    │ ─── Database access
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Database     │
└─────────────────┘
         │
         ▼
    Response (Entity or DTO)
```

## Folder Structure

Server-side code is organized under `src/lib/`, with `shared/` for cross-cutting concerns and `modules/` for domain logic.
Examples may use alias shortcuts such as `@/shared/*` and `@/modules/*`; those refer to `src/lib/shared/*` and `src/lib/modules/*`.

```
src/
├─ app/
│  └─ api/
│     ├─ trpc/
│     │  └─ [trpc]/
│     │     └─ route.ts         # tRPC HTTP handler
│     └─ <resource>/route.ts    # Optional OpenAPI-style handler during migration
│
├─ lib/
│  ├─ shared/                    # Cross-cutting infrastructure
│  │  ├─ kernel/
│  │  │  ├─ context.ts          # RequestContext type
│  │  │  ├─ transaction.ts      # TransactionManager interface
│  │  │  ├─ auth.ts             # Session, UserRole, Permission types
│  │  │  ├─ errors.ts           # Base error classes
│  │  │  └─ public-error.ts     # Shared public message policy
│  │  ├─ infra/
│  │  │  ├─ db/
│  │  │  │  ├─ drizzle.ts       # Drizzle client (postgres.js driver)
│  │  │  │  ├─ transaction.ts   # DrizzleTransactionManager
│  │  │  │  ├─ types.ts         # DbClient, DrizzleTransaction types
│  │  │  │  └─ schema/          # Table definitions
│  │  │  │     ├─ index.ts
│  │  │  │     └─ <table>.ts
│  │  │  ├─ trpc/
│  │  │  │  ├─ trpc.ts          # tRPC init + middleware (inline)
│  │  │  │  ├─ root.ts          # Root router
│  │  │  │  └─ context.ts       # Request context creation
│  │  │  ├─ logger/
│  │  │  │  └─ index.ts         # Pino configuration
│  │  │  └─ supabase/           # Supabase client (if using)
│  │  │     ├─ create-client.ts
│  │  │     └─ types.ts
│  │  └─ utils/                  # Optional utility functions
│  ├─ modules/                   # Domain modules
│  │  └─ <module>/
│  │     ├─ <module>.router.ts  # tRPC router (may have multiple per module)
│  │     ├─ <module>.controller.ts # Optional OpenAPI controller/handler adapter
│  │     ├─ dtos/               # Input/output schemas
│  │     │  ├─ <action>.dto.ts
│  │     │  └─ index.ts
│  │     ├─ errors/             # Domain-specific errors
│  │     │  └─ <module>.errors.ts
│  │     ├─ use-cases/          # Multi-service orchestration
│  │     │  └─ <action>.use-case.ts
│  │     ├─ factories/          # Dependency creation
│  │     │  └─ <module>.factory.ts
│  │     ├─ services/           # Business logic
│  │     │  └─ <module>.service.ts
│  │     ├─ repositories/       # Data access
│  │     │  └─ <module>.repository.ts
│  │     ├─ shared/             # Isomorphic domain logic (optional)
│  │     │  └─ domain.ts
│  │     ├─ admin/              # Admin sub-router (optional)
│  │     ├─ lib/                # Module-internal utilities (optional)
│  │     ├─ ops/                # Side-effect triggers (optional)
│  │     ├─ http/               # Non-tRPC HTTP handlers (optional)
│  │     ├─ queues/             # Queue interface + implementation (optional)
│  │     └─ providers/          # Vendor adapter implementations (optional)
│  ├─ trpc/
│  │  └─ client.ts              # Client-side tRPC setup
│  └─ env/                      # Environment validation
│     └─ index.ts
│
├─ proxy.ts                     # Next.js 16+ proxy (session refresh, route protection)
│
└─ drizzle/
   └─ migrations/
```

> **Note:** In Next.js 16+, the file `middleware.ts` is renamed to `proxy.ts` and the export is renamed from `middleware` to `proxy`.

## Documentation Index

| Document                                    | Description                                 |
| ------------------------------------------- | ------------------------------------------- |
| [Conventions](./conventions.md)             | Layer responsibilities, DI, kernel rules    |
| [Error Handling](./error-handling.md)       | Error classes, flow, response structure     |
| [Transaction](./transaction.md)             | Transaction manager, patterns, context      |
| [Testing Service Layer](./testing-service-layer.md) | MUST-level testability standards per layer |
| [Testing — Vitest Runner](../../client/core/testing-vitest.md) | Vitest runner configuration (shared with client) |
| [Event Patterns](./event-patterns.md) | Domain event log, notification outbox, side-effect procedures, command/query separation |
| [Logging](./logging.md)                     | Pino configuration, levels, business events |
| [API Contracts (Zod-First)](./api-contracts-zod-first.md) | Canonical transport-agnostic contract source |
| [Zod -> OpenAPI Generation](./zod-openapi-generation.md) | Standard for generated public API docs/spec artifacts |
| [API Response](./api-response.md)           | Envelope pattern, pagination                |
| [Endpoint Naming](./endpoint-naming.md)     | Naming and mapping rules for tRPC and OpenAPI |
| [ID Generation](./id-generation.md)         | Database UUID strategy                      |
| [Rate Limiting](./rate-limiting.md)         | Agnostic limits, identifiers, error contract |
| [Async Jobs + Outbox](./async-jobs-outbox.md) | Transactional enqueue + retry model       |
| [Webhooks](./webhook/README.md)             | Inbound webhook handling                    |
| [Webhook Testing](./webhook/testing/README.md) | Testing strategy + Vendor Simulator     |
| [tRPC Integration](../runtime/nodejs/libraries/trpc/integration.md)  | Serverless, routers, procedures   |
| [OpenAPI Integration](../runtime/nodejs/libraries/openapi/README.md) | OpenAPI adapter over shared domain layers |
| [OpenAPI Parity Testing](../runtime/nodejs/libraries/openapi/parity-testing.md) | Dual-transport parity rules |
| [tRPC Rate Limiting](../runtime/nodejs/libraries/trpc/rate-limiting.md) | Middleware tier patterns        |
| [Authentication](../runtime/nodejs/libraries/trpc/authentication.md) | Session management, authorization |
| [Supabase](../runtime/nodejs/libraries/supabase/README.md)           | Vendor integration patterns       |
| [Next.js](../runtime/nodejs/metaframeworks/nextjs/README.md)         | Metaframework route handling      |

## Quick Reference

### Error Handling

```typescript
// Throw domain error
throw new UserNotFoundError(userId);

// Validation with Zod
const input = validate(CreateUserSchema, data);
```

### Logging

```typescript
// Request logger
const log = createRequestLogger({ requestId, userId });
log.info("Processing request");

// Business event
logger.info({ event: "user.created", userId }, "User created");
```

### Factory Usage

```typescript
// Simple read → Service
const user = await makeUserService().findById(id);

// Simple write → Service
const user = await makeUserService().create(data);

// Multi-service → Use Case
const result = await makeRegisterUserUseCase().execute(input);
```

## Implemented Event-Driven Patterns

The following are production-complete (see `server/core/event-patterns.md`):

- **Domain event log** — append-only event tables for real-time broadcasting (e.g., `availability_change_event`)
- **Notification outbox** — transactional enqueue + async QStash dispatch with retry/backoff
- **Side-effect procedures** — best-effort post-commit ops for external integrations (chat messages)
- **Command/query separation** — router `.query`/`.mutation` split, role-specific service classes, `mut`/`query` naming on client API interfaces

## Non-Goals (Deferred)

These remain out of scope:

- Formal event bus / pub-sub system
- Separate read models / materialized projections (full CQRS)
- Microservices
- OpenTelemetry tracing (prepared for, not implemented)

## Checklist for New Modules

- [ ] Create module folder under `src/lib/modules/<module>/`
- [ ] Define entities in `src/lib/shared/infra/db/schema.ts`
- [ ] Create repository interface and implementation
- [ ] Create service interface and implementation
- [ ] Create domain-specific errors in `errors/`
- [ ] Create DTOs with Zod schemas
- [ ] Create factory with lazy singletons
- [ ] Create transport adapter (`tRPC`, `OpenAPI`, or both)
- [ ] If module-specific transport mapping is needed, add per-router error handler mapping domain errors to tRPC codes
- [ ] Add adapter to transport root/route registration
- [ ] If both transports exist, add parity tests
- [ ] Add `shared/domain.ts` for isomorphic pure domain logic (if needed)
- [ ] Add `admin/` sub-folder with `adminProcedure` if admin-facing (if needed)
- [ ] Add `providers/` with interface + implementations for external services (if needed)
- [ ] Add `queues/` with interface + implementation for async dispatch (if needed)
