# Backend Architecture Documentation

> Disciplined layered architecture for Node.js backends with Next.js, tRPC, Drizzle ORM, and PostgreSQL.

See [../README.md](../README.md) for the unified project folder structure and full documentation index.

## Overview

This documentation describes a **production-ready backend architecture** that emphasizes:

- Explicit dependency injection with factories
- Clear layer boundaries and responsibilities
- Framework-agnostic business logic
- Type-safe API contracts with tRPC and Zod

```
┌─────────────────────────────────────────────────────────────┐
│                      Router/Controller                       │
│                    (HTTP/tRPC concerns)                      │
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

| Concern    | Technology           |
| ---------- | -------------------- |
| Runtime    | Node.js (serverless) |
| Framework  | Next.js              |
| API Layer  | tRPC                 |
| Database   | PostgreSQL           |
| ORM        | Drizzle              |
| Validation | Zod                  |
| Logging    | Pino                 |

## Documentation Structure

### Core Documentation

| Document                                   | Description                                             |
| ------------------------------------------ | ------------------------------------------------------- |
| [Overview](./core/overview.md)             | Architecture summary, folder structure, quick reference |
| [Conventions](./core/conventions.md)       | Layer responsibilities, DI patterns, kernel rules       |
| [Error Handling](./core/error-handling.md) | Error classes, validation, response structure           |
| [Transaction](./core/transaction.md)       | Transaction manager, patterns, RequestContext           |
| [Logging](./core/logging.md)               | Pino configuration, levels, business events             |
| [API Response](./core/api-response.md)     | Envelope pattern, pagination helpers                    |
| [ID Generation](./core/id-generation.md)   | Database UUID strategy                                  |

### Integration Documentation

| Document                                   | Description                                   |
| ------------------------------------------ | --------------------------------------------- |
| [tRPC Integration](./trpc/integration.md)  | Serverless patterns, routers, Drizzle setup   |
| [Authentication](./trpc/authentication.md) | Session/JWT management, auth middleware, RBAC |
| [Webhooks](./webhook/architecture.md)      | Inbound webhook handling, idempotency         |
| [Supabase](./supabase/README.md)           | Auth, Storage, Database integration patterns  |

### Skills (AI-Assisted Development)

| Skill                                                | When to Use                                             |
| ---------------------------------------------------- | ------------------------------------------------------- |
| [backend-module](./skills/backend-module/SKILL.md)   | Creating new domain modules (entities, resources)       |
| [backend-feature](./skills/backend-feature/SKILL.md) | Adding features to existing modules (endpoints, fields) |

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
├─ app/api/trpc/[trpc]/route.ts    # tRPC HTTP handler
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

```typescript
// Success response
{
  "success": true,
  "data": { ... }
}

// Error response
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found"
  }
}
```

## Creating New Modules

See the [backend-module skill](./skills/backend-module/SKILL.md) for step-by-step instructions or use the scaffolding script:

```bash
python scripts/scaffold-module.py <module-name> <Entity>
```

## Non-Goals (Deferred)

These are explicitly out of scope for now:

- Async outbox pattern
- Event-driven architecture
- Microservices
- Full CQRS
- OpenTelemetry tracing (prepared for, not implemented)

## References

The `references/` folder contains the original detailed documentation that was consolidated into this structure. These files are preserved for historical context.
