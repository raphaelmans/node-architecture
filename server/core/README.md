# Backend Core README

> High-level overview of the backend architecture, linking to detailed documentation for each concern.

## Architecture Summary

This backend follows a **disciplined layered architecture** with explicit boundaries, manual dependency injection, and clear separation of concerns.

Testability is a first-class quality gate: modules are expected to follow interface-driven boundaries and layer-appropriate tests.

```
┌─────────────────────────────────────────────────────────────┐
│                     Framework Adapter                       │
│       (Next.js/Express/Hono/tRPC/OpenAPI concerns)           │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Framework-Neutral Controller                   │
│       (contract/command/result mapping; plain TypeScript)    │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ├─ Simple capability ──► Service ──► Repository
              │                         │              │
              │                         │              └─► Database
              │                         │
              └─ Orchestrated capability
                    └─► Use Case ──► Service(s) ──► Repository(s)
                           │                                │
                           └─► Outbox/provider port         └─► Database
```

## Core Principles

| Principle                                | Description                                  |
| ---------------------------------------- | -------------------------------------------- |
| **Explicit over implicit**               | No magic, clear dependency flow              |
| **Composition over coupling**            | Small, focused units composed together       |
| **Manual DI with factories**             | Explicit wiring, easy testing                |
| **Infrastructure is replaceable**        | Business logic doesn't know about frameworks |
| **Application boundary is portable**     | Controllers, services, and use cases are plain TypeScript |

## Dependency Direction

```text
framework adapter -> controller
                         ├─> service -> repository/provider port
                         └─> use case -> service(s) -> repository/provider ports

Every inward layer may depend on shared/kernel and module shared/contracts.

infrastructure adapter -> implements a kernel/application port
factory/composition root -> constructs and connects all concrete objects
```

Dependencies point toward contracts and application/domain policy. The kernel never imports modules, infrastructure, Node.js, or a framework. Browser-safe shared contracts may import browser-safe kernel primitives; they never import server infrastructure. Factories/composition roots are the only places that construct across layers.

## Technology Stack

| Concern    | Technology                               |
| ---------- | ---------------------------------------- |
| Runtime    | Node.js (deployment model is adapter-specific) |
| Framework adapters | Next.js, Express, or Hono               |
| API Layer  | tRPC (current), OpenAPI (migration path) |
| Database   | PostgreSQL                               |
| ORM        | Drizzle                                  |
| Validation | Zod (canonical contracts)                |
| Logging    | Pino behind `AppLogger`                  |
| Tracing    | OpenTelemetry context + semantic conventions |
| Testing    | Vitest                                   |

## Layer Responsibilities

| Layer                 | Responsibility                                 | Transactions               |
| --------------------- | ---------------------------------------------- | -------------------------- |
| **Framework Adapter** | Framework request/context, input parsing, auth/rate limit, observability, envelope/status, central error mapping | No |
| **Controller**        | Framework-neutral contract/command/result mapping; calls one use case or service | No |
| **Use Case**          | Multi-service orchestration, side effects      | Yes (owns)                 |
| **Service**           | Business logic, single-service operations      | Yes (owns or receives transaction options) |
| **Repository**        | Data access, entity persistence                | No (receives transaction options) |

### Controller Decision Flow

```
Controller receives validated shared input
└── Is it a write operation?
    ├── No (read) → Controller calls Service
    └── Yes (write)
        └── Does it involve multiple services or side effects?
            ├── No → Controller calls Service (service owns transaction)
            └── Yes → Controller calls Use Case (use case owns transaction)
```

## Data Flow

### Entities vs Contracts

| Type | Source | Used By | Purpose |
| --- | --- | --- | --- |
| **Entity** | Drizzle/ORM schema | Repository, service | Internal persistence/domain representation |
| **Shared API contract** | Zod in `modules/<module>/shared/contracts/` | Client feature API, server adapter, controller | Serialized request/response boundary |
| **Internal command DTO** | Server module/use case | Use case/service | Optional server-only orchestration shape |

**Rule:** Never expose an entity as the API contract implicitly. Public endpoints validate/map through a shared response contract. A server-only command is introduced only when its shape differs from the public input contract.

### Request Flow Example

```
Client Request
     │
     ▼
┌────────────────────────────────────┐
│  Framework Adapter                 │ ─── Parses input (shared Zod contract)
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Framework-Neutral Controller      │ ─── Maps contract; calls one entry
└────────┬───────────────────────────┘
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
  Shared Response Contract
```

## Folder Structure

Server-side code is organized under `src/lib/`, with `shared/` for cross-cutting concerns and `modules/` for domain logic.
Examples may use alias shortcuts such as `@/shared/*` and `@/modules/*`; those refer to `src/lib/shared/*` and `src/lib/modules/*`.
Choose the entrypoint branch for the framework in use; a project does not need all adapter folders.

```
src/
├─ app/
│  └─ api/
│     ├─ trpc/
│     │  └─ [trpc]/
│     │     └─ route.ts         # tRPC over Next.js option
│     └─ <resource>/route.ts    # Next.js HTTP adapter option
│
├─ routes/                      # Express or Hono option
│  ├─ <resource>.express.ts
│  └─ <resource>.hono.ts
│
├─ lib/
│  ├─ shared/                    # Cross-cutting infrastructure
│  │  ├─ kernel/
│  │  │  ├─ transaction.ts      # TransactionManager + transaction-only options
│  │  │  ├─ logger.ts           # Operational AppLogger port
│  │  │  ├─ product-analytics.ts # Typed ProductAnalytics port
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
│  │  │  │  ├─ index.ts         # Pino configuration + AppLogger singleton
│  │  │  │  └─ pino-app-logger.ts # AppLogger adapter
│  │  │  ├─ observability/
│  │  │  │  └─ request-context.ts # Async request/trace correlation
│  │  │  ├─ analytics/
│  │  │  │  ├─ index.ts         # ProductAnalytics singleton
│  │  │  │  ├─ composite.ts     # Multi-destination analytics adapter
│  │  │  │  ├─ mixpanel.ts
│  │  │  │  └─ google-analytics.ts
│  │  │  └─ supabase/           # Supabase client (if using)
│  │  │     ├─ create-client.ts
│  │  │     └─ types.ts
│  │  └─ utils/                  # Optional utility functions
│  ├─ modules/                   # Domain modules
│  │  └─ <module>/
│  │     ├─ <module>.router.ts  # Framework-specific tRPC adapter
│  │     ├─ controllers/        # Framework-neutral public boundary
│  │     │  └─ <capability>.controller.ts
│  │     ├─ dtos/               # Server-only commands (optional)
│  │     │  ├─ <action>.command.ts
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
│  │     ├─ shared/             # Isomorphic contracts + domain logic
│  │     │  ├─ contracts/
│  │     │  │  ├─ <capability>.contract.ts
│  │     │  │  └─ index.ts
│  │     │  └─ domain.ts
│  │     ├─ admin/              # Admin sub-router (optional)
│  │     ├─ lib/                # Module-internal utilities (optional)
│  │     ├─ ops/                # Side-effect triggers (optional)
│  │     ├─ http/               # Non-tRPC framework-adapter helpers (optional)
│  │     ├─ queues/             # Queue interface + implementation (optional)
│  │     └─ providers/          # Vendor adapter implementations (optional)
│  ├─ trpc/
│  │  └─ client.ts              # Client-side tRPC setup
│  └─ env/                      # Environment validation
│     └─ index.ts
│
├─ proxy.ts                     # Next.js-only option (session/route middleware)
│
└─ drizzle/
   └─ migrations/
```

> **Next.js-only note:** In Next.js 16+, the file `middleware.ts` is renamed to `proxy.ts` and the export is renamed from `middleware` to `proxy`.

## Documentation Index

| Document                                    | Description                                 |
| ------------------------------------------- | ------------------------------------------- |
| [Conventions](./conventions.md)             | Layer responsibilities, DI, kernel rules    |
| [Framework-Neutral Controllers](./controllers.md) | Portable boundary between framework adapters and application logic |
| [Error Handling](./error-handling.md)       | Error classes, flow, response structure     |
| [Transaction](./transaction.md)             | Transaction manager, patterns, context      |
| [Testing Service Layer](./testing-service-layer.md) | MUST-level testability standards per layer |
| [Testing — Vitest Runner](../../client/core/testing-vitest.md) | Vitest runner configuration (shared with client) |
| [Event Patterns](./event-patterns.md) | Domain event log, notification outbox, side-effect procedures, command/query separation |
| [Observability](./observability.md)         | Request/trace correlation, async propagation, logger DI |
| [Logging](./logging.md)                     | Operational logging contract and ownership |
| [Product Analytics](./product-analytics.md) | Typed product events, adapters, and delivery semantics |
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
| [Express](../runtime/nodejs/metaframeworks/express/README.md)       | Express adapter boundary          |
| [Hono](../runtime/nodejs/metaframeworks/hono/README.md)             | Hono adapter boundary             |

## Quick Reference

### Error Handling

```typescript
// Throw domain error
throw new UserNotFoundError(userId);

// Validation with Zod
const input = CreateUserInputSchema.parse(data);
```

### Logging

```typescript
// Factory injects the vendor-neutral logger port
const useCase = new CreateUserUseCase(userService, appLogger, productAnalytics);

// Operational log (debugging/operations)
appLogger.info(
  {
    "otel.event.name": "user.created",
    "code.function.name": "CreateUserUseCase.execute",
    "user.id": userId,
  },
  "User created",
);

// Product event (behavior analytics)
await productAnalytics.track({
  name: "user_created",
  userId,
  properties: { signupMethod: "email" },
});
```

### Factory Usage

```typescript
// Simple read → Controller → Service
const user = await makeGetUserController().execute({ id }, actor);

// Simple write → Controller → Service
const user = await makeCreateUserController().execute(data, actor);

// Multi-service → Controller → Use Case
const result = await makeRegisterUserController().execute(input, actor);
```

## Implemented Event-Driven Patterns

The following are production-complete (see `server/core/event-patterns.md`):

- **Domain event log** — append-only event tables for real-time broadcasting (e.g., `availability_change_event`)
- **Notification outbox** — transactional enqueue + async QStash dispatch with retry/backoff
- **Side-effect procedures** — best-effort post-commit ops for external integrations (chat messages)
- **Command/query separation** — framework-adapter `.query`/`.mutation` split, role-specific service classes, `mut`/`query` naming on client API interfaces

## Non-Goals (Deferred)

These remain out of scope:

- Formal event bus / pub-sub system
- Separate read models / materialized projections (full CQRS)
- Microservices
- A mandated OpenTelemetry exporter/backend (the propagation contract is defined; runtime exporter choice remains project-specific)

## Checklist for New Modules

- [ ] Create module folder under `src/lib/modules/<module>/`
- [ ] Define entities in `src/lib/shared/infra/db/schema.ts`
- [ ] Create repository interface and implementation
- [ ] Create service interface and implementation
- [ ] Create domain-specific errors in `errors/`
- [ ] Define public input/response Zod contracts in `shared/contracts/`
- [ ] Import the same contracts from client `featureApi` and server transport adapters
- [ ] Add a server-only command DTO only when internal orchestration differs from the public input
- [ ] Create one framework-neutral controller per public capability
- [ ] Controller maps shared input/output and calls one use case or service
- [ ] Create factory with lazy singletons
- [ ] Create transport adapter (`tRPC`, `OpenAPI`, or both)
- [ ] Transport adapter calls a controller factory only
- [ ] Register the adapter with the shared transport error mapping; do not map domain errors per route
- [ ] Add adapter to transport root/route registration
- [ ] If both transports exist, add parity tests
- [ ] Add `shared/domain.ts` for isomorphic pure domain logic (if needed)
- [ ] Add `admin/` sub-folder with `adminProcedure` if admin-facing (if needed)
- [ ] Add `providers/` with interface + implementations for external services (if needed)
- [ ] Add `queues/` with interface + implementation for async dispatch (if needed)
- [ ] Inject `AppLogger` for operational logs (if needed); never import Pino in application layers
- [ ] Inject `ProductAnalytics` for product events (if needed); use outbox delivery when loss is unacceptable
