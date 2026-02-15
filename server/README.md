# Backend Architecture Documentation

> Disciplined layered architecture for Node.js backends with Next.js, Zod-first contracts, tRPC (current), and OpenAPI migration readiness.

See [../README.md](../README.md) for the unified project folder structure and full documentation index.

## Overview

This documentation describes a **production-ready backend architecture** that emphasizes:

- Explicit dependency injection with factories
- Clear layer boundaries and responsibilities
- Framework-agnostic business logic
- Type-safe API contracts with Zod-first schemas and transport adapters

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

## Technology Stack

> **Note:** This documentation serves as an architectural reference. Always check `package.json` for actual package versions in your project.

| Concern    | Technology                               |
| ---------- | ---------------------------------------- |
| Runtime    | Node.js (serverless)                     |
| Framework  | Next.js                                  |
| API Layer  | tRPC (current), OpenAPI (migration path) |
| Database   | PostgreSQL                               |
| ORM        | Drizzle                                  |
| Validation | Zod (canonical contracts)                |
| Logging    | Pino                                     |

## Documentation Structure

### Core Documentation (Agnostic)

| Document                                   | Description                                             |
| ------------------------------------------ | ------------------------------------------------------- |
| [Overview](./core/overview.md)             | Architecture summary, folder structure, quick reference |
| [Conventions](./core/conventions.md)       | Layer responsibilities, DI patterns, kernel rules       |
| [Error Handling](./core/error-handling.md) | Error classes, validation, response structure           |
| [Transaction](./core/transaction.md)       | Transaction manager, patterns, RequestContext           |
| [Testing Service Layer](./core/testing-service-layer.md) | MUST-level testability for controller/usecase/service/repository |
| [Logging](./core/logging.md)               | Pino configuration, levels, business events             |
| [API Contracts (Zod-First)](./core/api-contracts-zod-first.md) | Canonical contracts for tRPC/OpenAPI coexistence |
| [Zod -> OpenAPI Generation](./core/zod-openapi-generation.md) | Build-time public API spec generation standard |
| [API Response](./core/api-response.md)     | Envelope pattern, pagination helpers                    |
| [Endpoint Naming](./core/endpoint-naming.md) | Capability naming for tRPC and OpenAPI mapping       |
| [ID Generation](./core/id-generation.md)   | Database UUID strategy                                  |
| [Rate Limiting](./core/rate-limiting.md)   | Agnostic rate-limiting contract and boundaries          |
| [Async Jobs + Outbox](./core/async-jobs-outbox.md) | Transactional enqueue, retries, idempotency      |
| [Webhooks](./core/webhook/architecture.md) | Inbound webhook handling, idempotency                   |
| [Webhook Testing](./core/webhook/testing-overview.md) | Testing guide + Vendor Simulator              |

### Runtime + Library Documentation

| Document                                   | Description                                   |
| ------------------------------------------ | --------------------------------------------- |
| [Runtime Index](./runtime/README.md)       | Runtime hierarchy (`nodejs`, metaframeworks) |
| [Node.js Runtime](./runtime/nodejs/README.md) | Node.js runtime libraries and metaframeworks |
| [tRPC Integration](./runtime/nodejs/libraries/trpc/integration.md)  | Serverless patterns, routers, Drizzle setup   |
| [OpenAPI Integration](./runtime/nodejs/libraries/openapi/README.md) | OpenAPI adapter model over shared domain layers |
| [OpenAPI Parity Testing](./runtime/nodejs/libraries/openapi/parity-testing.md) | tRPC/OpenAPI coexistence quality gate |
| [tRPC Rate Limiting](./runtime/nodejs/libraries/trpc/rate-limiting.md) | Middleware tiers and enforcement patterns |
| [Authentication](./runtime/nodejs/libraries/trpc/authentication.md) | Session/JWT management, auth middleware, RBAC |
| [Supabase](./runtime/nodejs/libraries/supabase/README.md)           | Auth, Storage, Database integration patterns  |
| [Next.js](./runtime/nodejs/metaframeworks/nextjs/README.md)         | Route handler patterns and conventions         |
| [Express (placeholder)](./runtime/nodejs/metaframeworks/express/README.md) | Reserved metaframework slot           |
| [NestJS (placeholder)](./runtime/nodejs/metaframeworks/nestjs/README.md)    | Reserved metaframework slot           |

### Skills (AI-Assisted Development)

| Skill                                                | When to Use                                             |
| ---------------------------------------------------- | ------------------------------------------------------- |
| [backend-module](../skills/server/backend-module/SKILL.md)   | Creating new domain modules (entities, resources)       |
| [backend-feature](../skills/server/backend-feature/SKILL.md) | Adding features to existing modules (endpoints, fields) |

## Quick Start

### Layer Decision Flow

```
Is it a write operation?
├── No (read) → Call Service directly
└── Yes (write)
    └── Does it involve multiple services or side effects?
        ├── No → Call Service directly (service owns transaction)
        └── Yes → Call Use Case (use case owns transaction)
```

### Testing Baseline (MUST)

- Use interface-based dependencies for service/usecase/repository boundaries.
- Follow `controller -> usecase (optional) -> service -> repository`.
- Add layer tests with appropriate doubles/fixtures per `core/testing-service-layer.md`.
- When capability exists in both tRPC and OpenAPI, enforce parity tests.

### Factory Usage

```typescript
// Simple read → Service
const user = await makeUserService().findById(id);

// Simple write → Service
const user = await makeUserService().create(data);

// Multi-service orchestration → Use Case
const result = await makeRegisterUserUseCase().execute(input);
```

### Error Handling

```typescript
// Throw domain error
throw new UserNotFoundError(userId);

// Router handles null from service
const user = await makeUserService().findById(id);
if (!user) {
  throw new UserNotFoundError(id);
}
```

### Logging

```typescript
// Business event
logger.info({ event: "user.created", userId }, "User created");

// Request-scoped logger
const log = createRequestLogger({ requestId, userId });
log.info("Processing request");
```

## Folder Structure

All server-side code lives under `src/lib/`.

```
src/
├─ app/
│  └─ api/
│     ├─ trpc/[trpc]/route.ts      # tRPC HTTP handler
│     └─ <resource>/route.ts       # Optional OpenAPI-style route handler during migration
├─ lib/                             # All server-side code
│  ├─ shared/
│  │  ├─ kernel/                    # Core types and interfaces
│  │  │  ├─ dtos/                   # Cross-module DTOs
│  │  │  ├─ context.ts              # RequestContext
│  │  │  ├─ transaction.ts          # TransactionManager
│  │  │  ├─ pagination.ts           # Pagination types
│  │  │  ├─ response.ts             # Response types
│  │  │  └─ errors.ts               # Base error classes
│  │  ├─ infra/                     # Infrastructure implementations
│  │  │  ├─ db/                     # Drizzle client, schema
│  │  │  ├─ trpc/                   # tRPC setup, middleware
│  │  │  ├─ logger/                 # Pino configuration
│  │  │  └─ container.ts            # Composition root
│  │  └─ utils/                     # Shared utilities
│  ├─ modules/
│  │  └─ <module>/
│  │     ├─ <module>.router.ts      # tRPC router
│  │     ├─ <module>.controller.ts  # Optional OpenAPI controller/handler adapter
│  │     ├─ dtos/                   # Module-specific DTOs
│  │     ├─ errors/                 # Domain-specific errors
│  │     ├─ use-cases/              # Multi-service orchestration
│  │     ├─ factories/              # Dependency creation
│  │     ├─ services/               # Business logic
│  │     └─ repositories/           # Data access
│  └─ trpc/
│     └─ client.ts                  # tRPC client
└─ drizzle/migrations/              # Database migrations
```

## Core Principles

| Principle                                | Description                                  |
| ---------------------------------------- | -------------------------------------------- |
| **Explicit over implicit**               | No magic, clear dependency flow              |
| **Composition over coupling**            | Small, focused units composed together       |
| **Manual DI with factories**             | Explicit wiring, easy testing                |
| **Infrastructure is replaceable**        | Business logic doesn't know about frameworks |
| **Business logic is framework-agnostic** | Services and use cases are pure TypeScript   |

## Key Patterns

### Transaction Context

Services accept optional `ctx?: RequestContext`:

- If `ctx.tx` provided → participate in external transaction
- If no `ctx.tx` → service owns its own transaction

```typescript
async create(data: EntityInsert, ctx?: RequestContext): Promise<Entity> {
  if (ctx?.tx) {
    return this.createInternal(data, ctx);
  }
  return this.transactionManager.run((tx) => this.createInternal(data, { tx }));
}
```

### Lazy Singleton Factories

```typescript
let userService: UserService | null = null;

export function makeUserService() {
  if (!userService) {
    userService = new UserService(
      makeUserRepository(),
      getContainer().transactionManager,
    );
  }
  return userService;
}
```

### Response Envelope

Non-tRPC HTTP endpoints use the standard envelope defined in `core/api-response.md`:

```typescript
// Success response
{
  "data": { ... }
}

// Error response (non-2xx)
{
  "code": "USER_NOT_FOUND",
  "message": "User not found",
  "requestId": "req-abc-123",
  "details": { ... }
}
```

## Creating New Modules

See the [backend-module skill](../skills/server/backend-module/SKILL.md) for step-by-step instructions or use the scaffolding script:

```bash
python scripts/scaffold-module.py <module-name> <Entity>
```

## Non-Goals (Deferred)

These are explicitly out of scope for now:

- Event-driven architecture
- Microservices
- Full CQRS
- OpenTelemetry tracing (prepared for, not implemented)

## Drafts

The `drafts/` folder contains detailed legacy references from earlier documentation.
These documents are **non-canonical** and may be outdated.

If anything conflicts, follow the canonical docs under:

- `server/core/`
- `server/core/webhook/`
- `server/runtime/nodejs/libraries/trpc/`
- `server/runtime/nodejs/libraries/openapi/`
- `server/runtime/nodejs/libraries/supabase/`
- `server/runtime/nodejs/metaframeworks/nextjs/`

Start here: [server/drafts/overview.md](./drafts/overview.md)
