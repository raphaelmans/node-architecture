# Backend Architecture Conventions

> Core architectural conventions defining layer responsibilities, dependency injection, and the kernel.

## Layer Responsibilities

### Routers/Controllers

**Responsibilities:**

- Handle HTTP/tRPC concerns only
- Parse requests into DTOs
- Call **one** use case or **one** service per operation
- Map results/errors to HTTP responses

**Rules:**

- No business logic
- No repository access
- No service-to-service orchestration
- Router handles null check for `findById` (throws `NotFoundError` if null)

```typescript
// lib/modules/user/user.router.ts

export const userRouter = router({
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input }) => {
      const user = await makeUserService().findById(input.id);
      if (!user) {
        throw new UserNotFoundError(input.id);
      }
      return wrapResponse(omitSensitive(user));
    }),
});
```

### Use Cases (Application Layer)

**What is a Use Case?**  
A use case represents a **business action or workflow**, not an HTTP endpoint.

**Responsibilities:**

- Orchestrate multiple services
- Own transaction boundaries for multi-service operations
- Coordinate side effects (email, audit, events)

**Rules:**

- Use cases may depend on multiple services
- Use cases do **not** know about HTTP or ORM details
- Use cases are class-based with an `execute` method

**When to create a use case:**

- Multi-service orchestration
- Side effects (email, audit, events)
- Complex workflows

**When NOT to create a use case:**

- Simple read-only queries (call service directly)
- Single-service writes (service owns the transaction)

```typescript
// lib/modules/user/use-cases/register-user.use-case.ts

export class RegisterUserUseCase {
  constructor(
    private userService: IUserService,
    private workspaceService: IWorkspaceService,
    private emailService: IEmailService,
    private transactionManager: TransactionManager,
  ) {}

  async execute(input: RegisterUserDTO): Promise<UserPublic> {
    const user = await this.transactionManager.run(async (tx) => {
      const user = await this.userService.create(input.userData, { tx });

      if (input.workspaceId) {
        await this.workspaceService.addMember(input.workspaceId, user.id, {
          tx,
        });
      }

      return user;
    });

    // Side effects outside transaction
    await this.emailService.sendWelcomeEmail(user.email, user.name);

    return omitSensitive(user);
  }
}
```

### Services (Domain Layer)

**Responsibilities:**

- Encapsulate business rules
- Operate on entities
- Remain stateless
- Own transactions for single-service writes

**Rules:**

- A service must not call another service
- No orchestration logic
- No infrastructure knowledge
- Accept optional `RequestContext` for external transaction participation

**Method patterns:**

- `create(data)` — owns its own transaction
- `create(data, ctx?)` — participates in external transaction if ctx provided, otherwise owns

```typescript
// lib/modules/user/services/user.service.ts

export class UserService implements IUserService {
  constructor(
    private userRepository: IUserRepository,
    private transactionManager: TransactionManager,
  ) {}

  async findById(id: string, ctx?: RequestContext): Promise<User | null> {
    return this.userRepository.findById(id, ctx);
  }

  async create(data: UserInsert, ctx?: RequestContext): Promise<User> {
    // If ctx has transaction, participate in it
    if (ctx?.tx) {
      return this.createInternal(data, ctx);
    }

    // Otherwise, own the transaction
    return this.transactionManager.run(async (tx) => {
      return this.createInternal(data, { tx });
    });
  }

  private async createInternal(
    data: UserInsert,
    ctx: RequestContext,
  ): Promise<User> {
    const existing = await this.userRepository.findByEmail(data.email, ctx);
    if (existing) {
      throw new UserEmailConflictError(data.email);
    }
    return this.userRepository.create(data, ctx);
  }
}
```

### Repositories (Data Access Layer)

**Responsibilities:**

- Handle persistence
- Translate between database records and entities

**Rules:**

- Repositories return entities, not DTOs
- ORM/database code lives here
- Accept transaction context via `RequestContext`
- Never create transactions

```typescript
// lib/modules/user/repositories/user.repository.ts

export class UserRepository implements IUserRepository {
  constructor(private db: DbClient) {}

  private getClient(ctx?: RequestContext): DbClient | DrizzleTransaction {
    return (ctx?.tx as DrizzleTransaction) ?? this.db;
  }

  async findById(id: string, ctx?: RequestContext): Promise<User | null> {
    const client = this.getClient(ctx);
    const result = await client
      .select()
      .from(users)
      .where(eq(users.id, id))
      .limit(1);

    return result[0] ?? null;
  }

  async create(data: UserInsert, ctx?: RequestContext): Promise<User> {
    const client = this.getClient(ctx);
    const result = await client.insert(users).values(data).returning();

    return result[0];
  }
}
```

## Dependency Injection & Factories

We use **manual DI with factories**.

**Why:**

- Explicit wiring
- Easy testing
- No hidden magic

**Rules:**

- No `new` across layers
- Factories own all object creation

### Factory Organization

**Structure:** Per-module factories with a shared composition root.

```
src/lib/
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
// lib/shared/infra/container.ts

import { db } from "./db/drizzle";
import { DrizzleTransactionManager } from "./db/transaction";
import type { TransactionManager } from "@/lib/shared/kernel/transaction";

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
// lib/modules/user/factories/user.factory.ts

import { getContainer } from "@/lib/shared/infra/container";
import { UserRepository } from "../repositories/user.repository";
import { UserService } from "../services/user.service";
import { RegisterUserUseCase } from "../use-cases/register-user.use-case";

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
    userService = new UserService(
      makeUserRepository(),
      getContainer().transactionManager,
    );
  }
  return userService;
}

// Use cases: new instance per invocation
export function makeRegisterUserUseCase() {
  return new RegisterUserUseCase(
    makeUserService(),
    makeWorkspaceService(),
    makeEmailService(),
    getContainer().transactionManager,
  );
}
```

**Key principles:**

- Container owns shared infrastructure (database, transaction manager, logger)
- Module factories own module-specific wiring
- Repositories and services are lazy singletons (stateless)
- Use cases are new instances per operation
- Factories are the _only_ place dependencies are instantiated

## Kernel (Shared Core)

### What is the Kernel?

The **kernel** is the smallest, most stable core of the system.

It contains:

- Cross-cutting contracts
- Fundamental abstractions
- Zero domain or infrastructure logic

Think of it as the **laws of the system**.

### Kernel Rules

Kernel code:

- Must be framework-agnostic
- Must be infra-agnostic
- Must be domain-agnostic

Kernel may import:

- TypeScript / Node built-ins
- Approved libraries (see below)

Kernel must NOT import:

- `infra/`
- `modules/`

### Approved Kernel Dependencies

- **zod** — Schema validation and type inference
  - Used for: DTO validation, config parsing, runtime type checks

### Kernel Contents

```
lib/shared/kernel/
├─ dtos/              # Cross-module DTOs
│  ├─ common.ts       # Shared schemas (file upload, etc.)
│  └─ index.ts
├─ transaction.ts     # TransactionManager + TransactionContext
├─ context.ts         # RequestContext
├─ errors.ts          # Base AppError definitions
├─ pagination.ts      # Pagination types and schemas
├─ response.ts        # API response types
└─ auth.ts            # Session, UserRole, Permission types
```

**Why these belong in kernel:**

- They are universal contracts
- They are depended on by many layers
- They must remain stable over time

## DTOs vs Entities

### Entities

- Represent domain state
- Used internally (services, repositories)
- Contain business behavior
- Do NOT represent API contracts

**Approach:** Use Drizzle schema types for database records. Add domain entity classes only when you need behavior attached to data.

```typescript
// lib/shared/infra/db/schema.ts

import { pgTable, uuid, text, timestamp } from "drizzle-orm/pg-core";
import { createSelectSchema, createInsertSchema } from "drizzle-zod";

export const users = pgTable("users", {
  id: uuid("id").primaryKey().defaultRandom(),
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  passwordHash: text("password_hash").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

export const UserSchema = createSelectSchema(users);
export type User = z.infer<typeof UserSchema>;
```

### DTOs (Data Transfer Objects)

- Represent data crossing boundaries
- Used by controllers and use cases
- Shaped for API consumers
- Safe to change independently

**Zod-based DTO pattern:**

```typescript
// lib/modules/user/dtos/create-user.dto.ts

import { z } from "zod";

export const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  role: z.enum(["admin", "member"]).default("member"),
});

export type CreateUserDTO = z.infer<typeof CreateUserSchema>;
```

### Cross-Module DTOs

DTOs that are shared across multiple modules live in `lib/shared/kernel/dtos/`.

**When to use shared DTOs (`lib/shared/kernel/dtos/`):**

- Schemas used by multiple modules (e.g., file upload, image asset)
- Common input patterns (pagination is already in `lib/shared/kernel/pagination.ts`)
- DTOs consumed by the frontend

**When to use module DTOs (`lib/modules/<module>/dtos/`):**

- Input/output specific to one module
- DTOs that may change independently of other modules

**Example - shared DTO:**

```typescript
// lib/shared/kernel/dtos/common.ts

import { z } from "zod";

export const ImageAssetSchema = z.object({
  file: z.custom<File>().optional(),
  url: z.string(),
});

export type ImageAsset = z.infer<typeof ImageAssetSchema>;

export const FileUploadSchema = z.object({
  imageAsset: ImageAssetSchema,
});
```

**Example - module DTO using shared schema:**

```typescript
// lib/modules/user/dtos/update-user.dto.ts

import { z } from "zod";
import { ImageAssetSchema } from "@/lib/shared/kernel/dtos/common";

export const UpdateUserSchema = z.object({
  name: z.string().min(1).max(100).optional(),
  avatar: ImageAssetSchema.optional(),
});

export type UpdateUserDTO = z.infer<typeof UpdateUserSchema>;
```

### Mapping Rules

- Controllers never receive entities directly (omit sensitive fields first)
- Repositories never return DTOs
- Mapping happens in routers, use cases, or mappers

## Complete Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                           Factory                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ makeUserRepository() ──► UserRepository(db)             │   │
│  │         │                                               │   │
│  │         ▼                                               │   │
│  │ makeUserService() ──► UserService(                      │   │
│  │         │               userRepository,                 │   │
│  │         │               transactionManager)             │   │
│  │         │                                               │   │
│  │         ▼                                               │   │
│  │ makeRegisterUserUseCase() ──► RegisterUserUseCase(      │   │
│  │                                userService,             │   │
│  │                                workspaceService,        │   │
│  │                                emailService,            │   │
│  │                                transactionManager)      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Router/Controller                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │ Simple read:                                            │   │
│  │   userRouter.getById ──► UserService.findById()         │   │
│  │                                                         │   │
│  │ Simple write (single service):                          │   │
│  │   userRouter.create ──► UserService.create()            │   │
│  │                              │                          │   │
│  │                              ▼                          │   │
│  │                     UserRepository.create()             │   │
│  │                                                         │   │
│  │ Multi-service orchestration:                            │   │
│  │   userRouter.register ──► RegisterUserUseCase.execute() │   │
│  │                              │                          │   │
│  │                    ┌─────────┴─────────┐                │   │
│  │                    ▼                   ▼                │   │
│  │           UserService        WorkspaceService           │   │
│  │                    │                   │                │   │
│  │                    ▼                   ▼                │   │
│  │           UserRepository     WorkspaceRepository        │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Return Type Summary

| Layer             | Returns       | Type Source                      |
| ----------------- | ------------- | -------------------------------- |
| Repository        | Entity        | drizzle-zod `createSelectSchema` |
| Service           | Entity        | Same as Repository               |
| Use Case          | Entity or DTO | DTO when transforming/omitting   |
| Router/Controller | Entity or DTO | What API consumers see           |

**Rule:** Return entities by default. Introduce DTOs when you need to transform, omit sensitive fields, or combine data.

## Non-Goals (Deferred)

These are **explicitly deferred**:

- Async outbox pattern
- Event-driven architecture
- Microservices
- Full CQRS

They will be revisited when the system demands them.

## Checklist

- [ ] Repository interface defined with `ctx?: RequestContext`
- [ ] Service interface defined, accepts optional `ctx` for transaction participation
- [ ] Service receives `TransactionManager` via constructor
- [ ] Services own transactions for single-service writes
- [ ] Services participate in external transactions when ctx.tx provided
- [ ] Use cases only for multi-service orchestration or side effects
- [ ] Factory creates lazy singletons for repository/service
- [ ] Factory creates new instance for each use case
- [ ] Router handles null check and throws `NotFoundError`
- [ ] Sensitive fields omitted before returning to client
