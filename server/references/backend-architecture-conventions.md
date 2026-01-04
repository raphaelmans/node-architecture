# Backend Architecture Conventions

> **Purpose**: This document defines the architectural conventions for our Node.js backend.
> It exists to enforce **clarity, separation of concerns, testability, and long-term maintainability**.

This is a **living document**. Some decisions are intentionally deferred and listed at the end.

---

## 1. High-Level Architecture Overview

We follow a **disciplined layered architecture** with explicit orchestration and dependency boundaries.

```
Controller
  → Use Case (Application Layer)
    → Domain Service
      → Repository
```

### Core Principles

* Explicit over implicit
* Composition over coupling
* Manual Dependency Injection (DI)
* Infrastructure is replaceable
* Business logic is framework-agnostic

---

## 2. Layer Responsibilities (Detailed)

### 2.1 Controllers

**Responsibilities**:

* Handle HTTP concerns only
* Parse requests into DTOs
* Call **one** use case (writes) or **one** service (simple reads)
* Map results/errors to HTTP responses

**Rules**:

* No business logic
* No repository access
* No service-to-service orchestration

---

### 2.2 Use Cases (Application Layer)

**What is a Use Case?**
A use case represents a **business action or workflow**, not an HTTP endpoint.

**Responsibilities**:

* Orchestrate multiple services
* Own transaction boundaries
* Coordinate side effects (email, audit, events)

**Rules**:

* Use cases may depend on multiple services
* Use cases do **not** know about HTTP or ORM details
* Use cases are class-based

**When to create a use case**:

* Multi-service orchestration
* Side effects (email, audit, events)
* Complex workflows

**When NOT to create a use case**:

* Simple read-only queries (call service directly)
* Single-service writes (service owns the transaction)

---

### 2.3 Domain Services

**Responsibilities**:

* Encapsulate business rules
* Operate on entities
* Remain stateless

**Rules**:

* A service must not call another service
* No orchestration logic
* No infrastructure knowledge
* Accept optional transaction context

---

### 2.4 Repositories

**Responsibilities**:

* Handle persistence
* Translate between database records and entities

**Rules**:

* Repositories return entities, not DTOs
* ORM / database code lives here
* Accept transaction context

---

## 3. Dependency Injection & Factories

We use **manual DI with factories**.

**Why**:

* Explicit wiring
* Easy testing
* No hidden magic

**Rules**:

* No `new` across layers
* Factories own all object creation

Example flow:

```
Factory → builds Use Case
Use Case → receives Services
Service → receives Repositories
```

### 3.1 Factory Organization

**Structure**: Per-module factories with a shared composition root.

```
src/
├─ shared/
│  └─ infra/
│     └─ container.ts       # Composition root - shared infra
│
├─ modules/
│  └─ user/
│     └─ factories/
│        ├─ user.factory.ts # Module-specific wiring
│        └─ index.ts
```

**Composition root (shared infrastructure):**

```typescript
// shared/infra/container.ts

import { db } from './db/drizzle';
import { TransactionManager, DrizzleTransactionManager } from '@/shared/kernel/transaction';

export interface Container {
  db: typeof db;
  transactionManager: TransactionManager;
}

let container: Container | null = null;

export function getContainer(): Container {
  if (!container) {
    container = {
      db,
      transactionManager: new DrizzleTransactionManager(db),
    };
  }
  return container;
}
```

**Module factory (lazy singletons):**

```typescript
// modules/user/factories/user.factory.ts

import { getContainer } from '@/shared/infra/container';
import { UserRepository } from '../repositories/user.repository';
import { UserService } from '../services/user.service';
import { CreateUserUseCase } from '../use-cases/create-user.use-case';

let userRepository: UserRepository | null = null;
let userService: UserService | null = null;

export function makeUserRepository() {
  if (!userRepository) {
    userRepository = new UserRepository(getContainer().db);
  }
  return userRepository;
}

export function makeUserService() {
  if (!userService) {
    userService = new UserService(makeUserRepository());
  }
  return userService;
}

export function makeCreateUserUseCase() {
  return new CreateUserUseCase(
    makeUserService(),
    getContainer().transactionManager,
  );
}
```

**Key principles:**

* Container owns shared infrastructure (database, transaction manager, logger)
* Module factories own module-specific wiring
* Repositories and services are lazy singletons (stateless)
* Use cases are new instances per operation
* Factories are the *only* place dependencies are instantiated

---

## 4. Kernel (Shared Core)

### 4.1 What is the Kernel?

The **kernel** is the smallest, most stable core of the system.

It contains:

* Cross-cutting contracts
* Fundamental abstractions
* Zero domain or infrastructure logic

Think of it as the **laws of the system**.

---

### 4.2 Kernel Rules

* Kernel code:

  * Must be framework-agnostic
  * Must be infra-agnostic
  * Must be domain-agnostic

* Kernel may import:

  * TypeScript / Node built-ins
  * Approved libraries (see below)

* Kernel must NOT import:

  * `infra/`
  * `modules/`

### 4.3 Approved Kernel Dependencies

* **zod** — Schema validation and type inference
  * Used for: DTO validation, config parsing, runtime type checks
  * Allowed in: Controllers (request validation), Use Cases (input validation), Config loaders

---

### 4.4 Kernel Contents

```
shared/kernel/
├─ transaction.ts   # TransactionManager + TransactionContext
├─ errors.ts        # Base AppError definitions
```

**Why these belong in kernel**:

* They are universal contracts
* They are depended on by many layers
* They must remain stable over time

### 4.5 Error Handling

Custom error classes provide structured error handling with HTTP mapping.

**Base class and hierarchy:**

```typescript
// shared/kernel/errors.ts

export abstract class AppError extends Error {
  abstract readonly code: string;
  abstract readonly httpStatus: number;
  readonly details?: Record<string, unknown>;

  constructor(message: string, details?: Record<string, unknown>) {
    super(message);
    this.name = this.constructor.name;
    this.details = details;
    Error.captureStackTrace(this, this.constructor);
  }
}

// 400 - Bad Request
export class ValidationError extends AppError {
  readonly code = 'VALIDATION_ERROR';
  readonly httpStatus = 400;
}

// 401 - Unauthorized
export class AuthenticationError extends AppError {
  readonly code = 'AUTHENTICATION_ERROR';
  readonly httpStatus = 401;
}

// 403 - Forbidden
export class AuthorizationError extends AppError {
  readonly code = 'AUTHORIZATION_ERROR';
  readonly httpStatus = 403;
}

// 404 - Not Found
export class NotFoundError extends AppError {
  readonly code = 'NOT_FOUND';
  readonly httpStatus = 404;
}

// 409 - Conflict
export class ConflictError extends AppError {
  readonly code = 'CONFLICT';
  readonly httpStatus = 409;
}

// 422 - Unprocessable Entity (business rule violations)
export class BusinessRuleError extends AppError {
  readonly code = 'BUSINESS_RULE_VIOLATION';
  readonly httpStatus = 422;
}

// 500 - Internal (unexpected errors)
export class InternalError extends AppError {
  readonly code = 'INTERNAL_ERROR';
  readonly httpStatus = 500;
}
```

**Error handler (infra layer):**

```typescript
// shared/infra/http/error-handler.ts

import { AppError } from '@/shared/kernel/errors';

export function handleError(error: unknown): { status: number; body: object } {
  if (error instanceof AppError) {
    return {
      status: error.httpStatus,
      body: {
        code: error.code,
        message: error.message,
        ...(error.details && { details: error.details }),
      },
    };
  }

  console.error('Unexpected error:', error);
  return {
    status: 500,
    body: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
    },
  };
}
```

**Error flow by layer:**

* **Repositories** throw: `NotFoundError`, `ConflictError`
* **Services** throw: `BusinessRuleError`, `ValidationError`
* **Use Cases** let errors bubble up (or wrap if needed)
* **Controllers** catch and map via `handleError`

---

## 5. DTOs vs Entities

### 5.1 Entities

* Represent domain state
* Used internally (services, repositories)
* Contain business behavior
* Do NOT represent API contracts

**Approach**: Use Drizzle schema types for database records. Add domain entity classes only when you need behavior attached to data.

### 5.2 DTOs (Data Transfer Objects)

* Represent data crossing boundaries
* Used by controllers and use cases
* Shaped for API consumers
* Safe to change independently

**Zod-based DTO pattern:**

```typescript
// modules/user/dtos/create-user.dto.ts

import { z } from 'zod';

export const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  role: z.enum(['admin', 'member']).default('member'),
});

export type CreateUserDTO = z.infer<typeof CreateUserSchema>;
```

**Validation in controllers:**

```typescript
const parsed = CreateUserSchema.safeParse(req.body);
if (!parsed.success) {
  throw new ValidationError('Invalid input', { issues: parsed.error.issues });
}
```

### 5.3 Mapping Rules

* Controllers never receive entities
* Repositories never return DTOs
* Mapping happens in use cases (or mappers if needed)

---

## 6. Transaction Model

* **Use cases** own transaction boundaries for multi-service orchestration
* **Services** own transaction boundaries for single-service writes
* Infrastructure provides the implementation

Kernel abstraction:

```
TransactionManager.run(fn)
```

* Services and use cases receive `TransactionManager` via DI
* Services accept `ctx?: RequestContext` for transaction context
* Repositories apply transaction context from `ctx.tx`

---

## 7. Folder Architecture (Reference)

```
src/
├─ shared/
│  ├─ kernel/
│  │  ├─ transaction.ts
│  │  └─ errors.ts
│  ├─ infra/
│  │  └─ db/
│  └─ utils/
│
├─ modules/
│  └─ user/
│     ├─ user.routes.ts
│     ├─ user.controller.ts
│     ├─ dtos/
│     ├─ use-cases/
│     ├─ factories/
│     ├─ services/
│     ├─ repositories/
│     └─ entities/
│
├─ tests/
└─ index.ts
```

---

## 8. Non-Goals (For Now)

These are **explicitly deferred**:

* Async outbox pattern
* Event-driven architecture
* Microservices
* Full CQRS

They will be revisited when the system demands them.

---

## 9. Open Questions (To Answer in the Future)

These decisions should be revisited as the system evolves:

### Domain & Modeling

1. Entity immutability vs controlled mutation
2. Public vs internal ID strategy

### Transactions & Consistency

3. When to introduce the outbox pattern
4. Cross-module transaction boundaries

### Read Model

5. Dedicated read repositories or projections
6. Pagination and filtering standards

### API & Contracts

7. DTO versioning strategy

### Testing & Quality

8. Unit vs integration test ratios
9. Fixture and test data strategy

### Infra & Scale

10. Migration strategy
11. Observability standards

---

## 10. Final Note

These conventions exist to **reduce ambiguity and cognitive load**.

If a design decision feels unclear:

* default to explicitness
* avoid shortcuts
* document trade-offs

When in doubt, raise it early.
