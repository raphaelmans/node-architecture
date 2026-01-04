# Backend Architecture Overview

> **Purpose**: High-level overview of the backend architecture, linking to detailed documentation for each concern.

---

## 1. Architecture Summary

This backend follows a **disciplined layered architecture** with explicit boundaries, manual dependency injection, and clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                        Router/Controller                    │
│                    (HTTP/tRPC concerns)                     │
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

---

## 2. Core Principles

| Principle | Description |
|-----------|-------------|
| **Explicit over implicit** | No magic, clear dependency flow |
| **Composition over coupling** | Small, focused units composed together |
| **Manual DI with factories** | Explicit wiring, easy testing |
| **Infrastructure is replaceable** | Business logic doesn't know about frameworks |
| **Business logic is framework-agnostic** | Services and use cases are pure TypeScript |

---

## 3. Technology Stack

| Concern | Technology |
|---------|------------|
| Runtime | Node.js (serverless) |
| Framework | Next.js |
| API Layer | tRPC |
| Database | PostgreSQL |
| ORM | Drizzle |
| Validation | Zod |
| Logging | Pino |

---

## 4. Layer Responsibilities

| Layer | Responsibility | Transactions |
|-------|----------------|--------------|
| **Router/Controller** | HTTP concerns, input validation, error mapping | No |
| **Use Case** | Multi-service orchestration, side effects | Yes (owns) |
| **Service** | Business logic, single-service operations | Yes (owns) |
| **Repository** | Data access, entity persistence | No (receives context) |

**When to use a Use Case vs Service directly:**

| Scenario | Use |
|----------|-----|
| Simple read | Service |
| Single-service write | Service |
| Multi-service orchestration | Use Case |
| Side effects (email, events) | Use Case |

---

## 5. Data Flow

### Entities vs DTOs

| Type | Source | Used By | Purpose |
|------|--------|---------|---------|
| **Entity** | drizzle-zod | Repository, Service | Internal data representation |
| **DTO** | Zod schemas | Router, Use Case | API contracts, input validation |

**Rule**: Return entities by default. Use DTOs when transforming, omitting sensitive fields, or combining data.

### Request Flow Example

```
Client Request
     │
     ▼
┌─────────────────┐
│  tRPC Router    │ ─── Validates input (Zod)
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

---

## 6. Key Patterns

### Dependency Injection

- **Factories** create all dependencies
- **Lazy singletons** for repositories and services
- **New instances** for use cases

```typescript
// Factory creates dependencies
makeUserService() → UserService(userRepository, transactionManager)
```

### Error Handling

- **Custom error classes** with HTTP status mapping
- **Domain-specific errors** per module
- **Error handler** attaches `requestId`, logs appropriately
- **Client receives**: `code`, `message`, `requestId`, optional `details`

```typescript
throw new UserNotFoundError(userId);
// → { code: 'USER_NOT_FOUND', message: 'User not found', requestId: '...' }
```

### Logging

- **Pino** for structured JSON logging
- **Child loggers** with request context
- **Business events** at service layer (`user.created`, `payment.processed`)
- **Request lifecycle** at middleware layer

```typescript
logger.info({ event: 'user.created', userId }, 'User created');
```

---

## 7. Folder Structure

```
src/
├─ app/
│  └─ api/
│     └─ trpc/
│        └─ [trpc]/
│           └─ route.ts
│
├─ shared/
│  ├─ kernel/
│  │  ├─ context.ts          # RequestContext
│  │  ├─ transaction.ts      # TransactionManager
│  │  └─ errors.ts           # Base error classes
│  ├─ infra/
│  │  ├─ db/
│  │  │  ├─ drizzle.ts       # Drizzle client
│  │  │  └─ schema.ts        # Table + entity definitions
│  │  ├─ trpc/
│  │  │  ├─ trpc.ts          # tRPC initialization
│  │  │  ├─ root.ts          # Root router
│  │  │  ├─ context.ts       # Request context
│  │  │  └─ middleware/
│  │  ├─ logger/
│  │  │  └─ index.ts         # Pino configuration
│  │  └─ container.ts        # Composition root
│  └─ utils/
│     ├─ validation.ts       # Zod helpers
│     └─ sanitize.ts         # Data sanitization
│
├─ modules/
│  └─ <module>/
│     ├─ <module>.router.ts  # tRPC router
│     ├─ dtos/               # Input/output schemas
│     ├─ errors/             # Domain-specific errors
│     ├─ use-cases/          # Multi-service orchestration
│     ├─ factories/          # Dependency creation
│     ├─ services/           # Business logic
│     └─ repositories/       # Data access
│
├─ drizzle/
│  └─ migrations/
│
└─ trpc/
   └─ client.ts
```

---

## 8. Documentation Index

| Document | Description |
|----------|-------------|
| [Backend Architecture Conventions](./backend-architecture-conventions.md) | Core principles, layer responsibilities, kernel |
| [Next.js + tRPC Specifics](./backend-architecture-nextjs-trpc.md) | Serverless considerations, tRPC integration |
| [Factory to Repository Flow](./backend-architecture-factory-flow.md) | Complete dependency flow with code examples |
| [Error Handling](./backend-architecture-error-handling.md) | Error classes, error flow, response structure |
| [Logging](./backend-architecture-logging.md) | Pino configuration, log levels, business events |
| [Open Items](./backend-architecture-open-items.md) | Gaps and decisions yet to be made |

---

## 9. Quick Reference

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
log.info('Processing request');

// Business event
logger.info({ event: 'user.created', userId }, 'User created');
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

---

## 10. Non-Goals (Deferred)

These are explicitly out of scope for now:

- Async outbox pattern
- Event-driven architecture
- Microservices
- Full CQRS
- OpenTelemetry tracing (prepared for, not implemented)

---

## 11. Checklist for New Modules

- [ ] Create module folder under `src/modules/<module>/`
- [ ] Define entities in `shared/infra/db/schema.ts`
- [ ] Create repository interface and implementation
- [ ] Create service interface and implementation
- [ ] Create domain-specific errors in `errors/`
- [ ] Create DTOs with Zod schemas
- [ ] Create factory with lazy singletons
- [ ] Create tRPC router
- [ ] Add router to root router
