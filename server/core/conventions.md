# Backend Architecture Conventions

> Core architectural conventions defining layer responsibilities, dependency injection, and the kernel.

## Layer Responsibilities

### Transport + Contract Strategy

- Contract source of truth is `Zod` schemas (see `./api-contracts-zod-first.md`).
- Current primary transport is `tRPC`; OpenAPI is supported as migration/coexistence transport.
- Transport adapters (tRPC routers, OpenAPI route handlers/controllers) must call the same usecase/service boundaries.
- Business/domain layers MUST NOT import transport-specific types.
- Capability naming and transport mapping rules are defined in `./endpoint-naming.md`.

### Canonical Layer Chain

All backend modules follow this chain:

`controller -> usecase (optional, for complex orchestration) -> service (SRP domain logic) -> repository`

Dependency and testing boundaries must align to this flow.

Canonical testing rules are defined in:

- [Testing Service Layer](./testing-service-layer.md)

### Routers/Controllers

**Responsibilities:**

- Handle HTTP/tRPC/OpenAPI concerns only
- Parse requests into DTOs
- Call **one** use case or **one** service per operation
- Map results/errors to HTTP responses

**Rules:**

- No business logic
- No repository access
- No service-to-service orchestration (exception: pre-fetch guards — see below)
- Router handles null check for `findById` (throws `NotFoundError` if null)
- Cross-cutting controls (auth, rate limiting) belong in transport middleware/procedures

**Pre-Fetch Guard Exception:**

Routers may call a second service for pre-fetch guards that are cross-cutting (e.g., resolving a user profile before delegating to the feature service). This is allowed when:

- The pre-fetch is stateless and read-only
- It serves as a guard or context enrichment, not orchestration
- It is systematic across all procedures in the router (not ad-hoc)

```typescript
// Allowed: systematic pre-fetch guard
const profile = await makeProfileService().getOrCreateProfile(ctx.userId);
const result = await makeReservationService().create(input, profile);
```

If the pre-fetch involves writes or side effects, use a use case instead.

```typescript
// modules/user/user.router.ts

import { z } from "zod";
import { S } from "@/shared/kernel/schemas";

export const userRouter = router({
  getById: protectedProcedure
    .input(z.object({ id: S.ids.generic }))
    .query(async ({ input }) => {
      const user = await makeUserService().findById(input.id);
      if (!user) {
        throw new UserNotFoundError(input.id);
      }
      return wrapResponse(omitSensitive(user));
    }),
});
```

**Per-Router Error Handler Pattern:**

When a module has many domain-specific errors that must map to distinct tRPC error codes (e.g., `NOT_FOUND`, `FORBIDDEN`, `BAD_REQUEST`), routers use a per-module error handler:

```typescript
function handleReservationError(error: unknown): never {
  if (error instanceof SlotNotAvailableError) {
    throw new TRPCError({ code: "BAD_REQUEST", cause: error });
  }
  if (error instanceof ReservationNotFoundError) {
    throw new TRPCError({ code: "NOT_FOUND", cause: error });
  }
  if (error instanceof ReservationAccessDeniedError) {
    throw new TRPCError({ code: "FORBIDDEN", cause: error });
  }
  // Unknown errors re-throw to the global formatter
  throw error;
}
```

Use this pattern when module-level domain errors need explicit tRPC code mapping (`NOT_FOUND`, `FORBIDDEN`, `BAD_REQUEST`) at the router boundary. For cross-module mapping rules, prefer a shared transport middleware/helper instead of repeating router-level `try/catch` in every procedure.

Rules for per-router error handlers:

- One `handle<Module>Error` function per router file
- Map only domain errors from that module's `errors/` folder
- Let the global formatter control the public message by passing `cause`
- Re-throw unknown errors (let the global formatter handle them)
- Apply `try/catch` only to procedures that need module-specific transport mapping

### Multiple Routers Per Module

Modules with distinct user roles or complex domains may expose multiple routers:

```
modules/reservation/
  reservation.router.ts          # Guest/player procedures
  reservation-coach.router.ts    # Coach-specific procedures
  reservation-owner.router.ts    # Owner-specific procedures
```

Each router is registered separately in `root.ts`. This pattern is allowed when:

- Procedures serve distinct user roles with different auth requirements
- The module is large enough that a single router becomes unwieldy
- Each router uses role-appropriate procedure bases (e.g., `protectedProcedure` vs `adminProcedure`)

### Admin Sub-Router Pattern

Modules with admin-facing procedures use an `admin/` sub-folder:

```
modules/court/
  court.router.ts
  admin/
    admin-court.router.ts       # Uses adminProcedure
```

Admin routers are composed under `appRouter.admin.*` in root.ts and use `adminProcedure` (which enforces `session.role === "admin"`).

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
- Constructor dependencies MUST be interface types (not concrete classes)

**When to create a use case:**

- Multi-service orchestration
- Side effects (email, audit, events)
- Complex workflows

For background delivery side effects, prefer transactional enqueue using the outbox pattern:
- [Async Jobs + Outbox](./async-jobs-outbox.md)

**When NOT to create a use case:**

- Simple read-only queries (call service directly)
- Single-service writes (service owns the transaction)

```typescript
// modules/user/use-cases/register-user.use-case.ts

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

- A service should not call another service (see exception below)
- No orchestration logic
- No infrastructure knowledge
- Accept optional `RequestContext` for external transaction participation
- Constructor dependencies MUST be interface types (not concrete classes)

**Service-to-Service Dependency Exception:**

In practice, some services accept other services as injected dependencies for **fire-and-forget side effects** that are tightly coupled to the domain operation (e.g., a notification delivery service, an audit/event service). This is allowed when:

- The dependency is injected via the constructor (not imported directly)
- The dependency is interface-typed
- The side effect does not affect the return value of the calling method
- The side effect is idempotent or eventually consistent

For multi-service orchestration that affects the primary return value, use a use case instead.

**Method patterns:**

- `create(data)` — owns its own transaction
- `create(data, ctx?)` — participates in external transaction if ctx provided, otherwise owns

```typescript
// modules/user/services/user.service.ts

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
- Repository interfaces MUST be defined and implemented explicitly

```typescript
// modules/user/repositories/user.repository.ts

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

**Pessimistic Locking (`FOR UPDATE`) Pattern:**

For contended-state entities (reservations, availability slots), repositories expose `findByIdForUpdate` variants:

```typescript
async findByIdForUpdate(id: string, ctx: RequestContext): Promise<Entity | null> {
  const tx = ctx.tx as DrizzleTransaction;
  const result = await tx
    .select()
    .from(entities)
    .where(eq(entities.id, id))
    .for("update")
    .limit(1);

  return result[0] ?? null;
}
```

Rules for `FOR UPDATE`:

- Only used within an active transaction (`ctx.tx` is required, not optional)
- Execute on the transaction client (`ctx.tx`) so row locks are held until transaction end
- Name methods `findByIdForUpdate`, `findByIdsForUpdate` to make locking intent explicit
- Use only for entities where concurrent writes could cause data corruption

**Repository Importing from `shared/domain.ts`:**

Repositories may import pure functions from `modules/<module>/shared/domain.ts` for in-memory post-query filtering when the filtering logic is domain-specific and cannot be expressed in SQL:

```typescript
import { filterBlockingOverlaps } from "../shared/domain";

async findConflicting(slotId: string, ctx?: RequestContext) {
  const rows = await this.getClient(ctx).select().from(slots).where(...);
  return filterBlockingOverlaps(rows); // pure domain filter
}
```

This is allowed because `shared/domain.ts` is pure and infrastructure-free.

## Dependency Injection & Factories

We use **manual DI with factories**.

**Why:**

- Explicit wiring
- Easy testing
- No hidden magic

**Rules:**

- No `new` across layers
- Factories own all object creation
- Factories MUST wire interfaces to implementations in one place for isolated testing

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
// shared/infra/container.ts

import { db } from "./db/drizzle";
import { DrizzleTransactionManager } from "./db/transaction";
import type { TransactionManager } from "@/shared/kernel/transaction";

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

import { getContainer } from "@/shared/infra/container";
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
- Use cases are new instances per invocation by default. When a use case is injected as a dependency of a service (rather than called directly from a router), it may be cached as a lazy singleton alongside the service.
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
shared/kernel/
├─ dtos/              # Cross-module DTOs
│  ├─ common.ts       # Shared schemas (file upload, etc.)
│  └─ index.ts
├─ transaction.ts     # TransactionManager + TransactionContext
├─ context.ts         # RequestContext
├─ errors.ts          # Base AppError definitions
├─ public-error.ts    # Public message policy helpers (getPublicErrorMessage, isInternalAppError)
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
// shared/infra/db/schema.ts

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
// modules/user/dtos/create-user.dto.ts

import { z } from "zod";
import { S } from "@/shared/kernel/schemas";

export const CreateUserSchema = z.object({
  email: S.common.email,
  name: S.common.requiredText,
  role: z.enum(["admin", "member"]).default("member"),
});

export type CreateUserDTO = z.infer<typeof CreateUserSchema>;
```

### Cross-Module DTOs

DTOs that are shared across multiple modules live in `shared/kernel/dtos/`.

**When to use shared DTOs (`shared/kernel/dtos/`):**

- Schemas used by multiple modules (e.g., file upload, image asset)
- Common input patterns (pagination is already in `shared/kernel/pagination.ts`)
- DTOs consumed by the frontend

**When to use module DTOs (`lib/modules/<module>/dtos/`):**

- Input/output specific to one module
- DTOs that may change independently of other modules

**Example - shared DTO:**

```typescript
// shared/kernel/dtos/common.ts

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
// modules/user/dtos/update-user.dto.ts

import { z } from "zod";
import { ImageAssetSchema } from "@/shared/kernel/dtos/common";

export const UpdateUserSchema = z.object({
  name: z.string().min(1).max(100).optional(),
  avatar: ImageAssetSchema.optional(),
});

export type UpdateUserDTO = z.infer<typeof UpdateUserSchema>;
```

## Extended Module Sub-Folders

Beyond the canonical structure (`dtos/`, `errors/`, `factories/`, `repositories/`, `services/`, `use-cases/`, `shared/`), modules may contain these additional sub-folders when the domain requires them:

| Sub-Folder | Purpose | When to Use |
| --- | --- | --- |
| `lib/` | Stateless utility/parsing functions internal to the module | Module needs non-domain parsers, formatters, or adapters (e.g., CSV/XLSX/ICS parsing, AI mapping) |
| `ops/` | One-off operational side-effect triggers | Module has domain-aware side effects triggered by other modules (e.g., posting a chat message when a reservation status changes) |
| `http/` | Non-tRPC inbound HTTP handlers | Module receives HTTP requests outside tRPC (e.g., queue-triggered dispatch endpoints, webhook handlers) |
| `queues/` | Queue interface + provider implementation | Module uses async job dispatch with an interface boundary (e.g., `INotificationDispatchQueue` + `QStashNotificationDispatchQueue`) |
| `providers/` | Vendor-specific adapter implementations | Module abstracts an external service with a swappable provider interface (e.g., `IChatProvider` with Stream Chat and Supabase backends) |
| `admin/` | Admin-gated router and related procedures | Module exposes admin-specific procedures using `adminProcedure` |
| `schemas/` | Validation schemas separate from DTOs | Module has many schemas that serve multiple layers |

Rules:

- These sub-folders are opt-in. Only create them when the module's complexity justifies them.
- `providers/` co-locate the interface and implementations together inside the module, not in `shared/infra/`. This keeps vendor-specific code contained.
- `queues/` follow the same interface + implementation pattern as `providers/`.
- `ops/` functions are typically called from services or use cases in other modules, not from routers directly.

## Module Shared Code (`lib/modules/<module>/shared/`)

Some modules need **shared, reusable code** that is still domain-specific (not kernel).

Convention:

- Put module-owned shared code in `lib/modules/<module>/shared/`.
- Treat it as potentially **isomorphic**: safe to import from both server and client code when needed.

Typical contents:

- Zod schemas + inferred types that represent module concepts
- deterministic calculations and invariants (pure functions)
- domain-specific error types that do not depend on server infrastructure

Rules:

- Must not import `shared/infra/*` (DB, logger, auth, tRPC init).
- Must not depend on framework-only code.
- Keep it pure and portable so it can be extracted to a workspace package later.

Example (pattern reference):

- `modules/webhooks/shared/webhook.schemas.ts`
- `modules/webhooks/shared/webhook.errors.ts`

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

## Implemented Event-Driven Patterns

See [Event Patterns](./event-patterns.md) for production-complete patterns:

- Domain event log (append-only event tables for real-time broadcasting)
- Notification outbox (transactional enqueue + async dispatch)
- Side-effect procedures (`ops/` for best-effort post-commit work)
- Command/query separation (router-level, service-level, client API-level)

See [Async Jobs + Outbox](./async-jobs-outbox.md) for the conceptual outbox pattern.

## Non-Goals (Deferred)

These remain **explicitly deferred**:

- Formal event bus / pub-sub system
- Separate read models / materialized projections (full CQRS)
- Microservices

---

## Layer-by-Layer Checklist

Use this comprehensive checklist for EVERY module to ensure nothing is missed.

### Errors Layer (`errors/<module>.errors.ts`)

```typescript
// Template - EVERY error class MUST follow this
export class <Entity><ErrorType>Error extends <BaseError> {
  readonly code = '<MODULE>_<ERROR_TYPE>';  // REQUIRED
  constructor(<entityId>: string) {
    super('<User-safe message>', { <entityId> });
  }
}
```

- [ ] Each error extends appropriate base (`NotFoundError`, `ConflictError`, `AuthenticationError`, etc.)
- [ ] Each error has `readonly code = '<MODULE>_<ERROR_TYPE>'` (SCREAMING_SNAKE_CASE)
- [ ] Code is unique across the entire application
- [ ] Constructor passes IDs to details object
- [ ] Message is user-safe (no internal details, stack traces)

### Repository Layer (`repositories/<module>.repository.ts`)

- [ ] Interface `I<Entity>Repository` defined with all method signatures
- [ ] Class implements interface: `implements I<Entity>Repository`
- [ ] Constructor accepts `DbClient`
- [ ] `getClient(ctx)` helper: `return (ctx?.tx as DrizzleTransaction) ?? this.db`
- [ ] All methods accept `ctx?: RequestContext`
- [ ] Returns `null` for not found (never throws)
- [ ] Known database constraint violations caught and translated to domain errors
- [ ] Raw database error messages never propagated as-is
- [ ] No business logic
- [ ] No logging

### Service Layer (`services/<module>.service.ts`)

- [ ] Interface `I<Entity>Service` defined with all method signatures
- [ ] Class implements interface: `implements I<Entity>Service`
- [ ] Constructor accepts **interface** types: `I<Entity>Repository` (not concrete)
- [ ] Constructor accepts `TransactionManager`
- [ ] Read methods: pass `ctx` through to repository
- [ ] Write methods: check `ctx?.tx` - participate if exists, else create transaction
- [ ] Business events logged: `logger.info({ event: '<entity>.<action>', ... }, 'Message')`
- [ ] Event names: `<entity>.<past_tense_action>` format
- [ ] Returns `null` for not found (router handles throwing)
- [ ] No service-to-service calls (exception: injected fire-and-forget side-effect services)

### Use Case Layer (`use-cases/<name>.use-case.ts`)

- [ ] Only created for multi-service orchestration or side effects
- [ ] Constructor accepts **interface** types (not concrete classes)
- [ ] Constructor accepts `TransactionManager`
- [ ] Throws **domain errors** (NOT generic `Error`)
- [ ] External service calls OUTSIDE transaction
- [ ] DB operations INSIDE transaction
- [ ] Side effects AFTER transaction commits
- [ ] No logging (services log the events)

```typescript
// CORRECT - domain error
if (!result) throw new EntityNotFoundError(id);

// WRONG - generic error
if (!result) throw new Error('Entity not found');
```

### Factory Layer (`factories/<module>.factory.ts`)

- [ ] Lazy singleton for DB-backed modules (repository, service)
- [ ] Request-scoped for request-dependent modules (auth with cookies)
- [ ] Returns interface type in JSDoc/type hints
- [ ] Uses `getContainer()` for shared dependencies

### DTO Layer (`dtos/`)

- [ ] Zod schemas for all inputs
- [ ] Type exported: `export type <Name>DTO = z.infer<typeof <Name>Schema>`
- [ ] Index file exports all schemas and types
- [ ] Validation rules match business requirements
- [ ] Sensitive fields excluded from output DTOs

### Router Layer (`<module>.router.ts`)

- [ ] Uses appropriate procedure base (`publicProcedure`, `protectedProcedure`, `adminProcedure`, or rate-limited variant)
- [ ] Input validated with `.input(ZodSchema)`
- [ ] Calls factory: `make<Entity>Service()` or `make<UseCase>()`
- [ ] Handles null: `if (!entity) throw new EntityNotFoundError(id)`
- [ ] One service OR one use case per endpoint (pre-fetch guard exception allowed)
- [ ] No business logic
- [ ] No direct logging (handled by middleware)
- [ ] Sensitive fields omitted before returning
- [ ] If module-specific transport mapping is needed, add a per-router error handler (`handle<Module>Error`)
- [ ] Apply `try/catch` only to procedures that need that custom mapping; let other errors bubble to formatter
- [ ] Per-router error handler passes `cause` field so global formatter controls exposure
- [ ] No raw error messages from libraries/DB in `TRPCError` message field

### Transport Infrastructure (`shared/infra/trpc/`, OpenAPI handlers/controllers)

Common:

- [ ] Zod schema contracts reused from canonical contract definitions
- [ ] No business logic in transport adapter
- [ ] Request-scoped metadata (`requestId`) present in error mapping
- [ ] Auth/rate-limit enforcement applied at transport boundary

tRPC-specific:

- [ ] Logger middleware applied to ALL procedures
- [ ] `publicProcedure = loggedProcedure`
- [ ] `protectedProcedure = loggedProcedure.use(authMiddleware)`
- [ ] `adminProcedure = protectedProcedure.use(adminMiddleware)` (requires `session.role === "admin"`)
- [ ] `rateLimitedProcedure(tier)` — factory returning rate-limited public procedure
- [ ] `protectedRateLimitedProcedure(tier)` — factory returning rate-limited protected procedure
- [ ] `adminRateLimitedProcedure(tier)` — factory returning rate-limited admin procedure
- [ ] Error formatter logs include `requestId`
- [ ] Known errors (`AppError`) logged at `warn` level
- [ ] Unknown errors logged at `error` level
- [ ] Context includes `log` (child logger with requestId), `clientIdentifier`, `clientIdentifierSource`, `cookies`, `origin`
- [ ] Context creation enriches session with role from `user_roles` table when authenticated

OpenAPI-specific:

- [ ] Route handlers/controllers validate inputs with shared Zod schemas
- [ ] Error mapping returns shared error contract (`code`, `message`, `requestId`, `details?`)
- [ ] Response payload shape follows shared API contract guidance

```typescript
// Error formatter MUST include requestId
ctx?.log.warn(
  { err: cause, code: cause.code, details: cause.details, requestId },
  cause.message,
);
```

### Root Router Registration

- [ ] tRPC router imported in `shared/infra/trpc/root.ts` (if tRPC is enabled)
- [ ] OpenAPI route/controller wired in runtime router tree (if OpenAPI is enabled)

### Testability Standard (MUST)

- [ ] Layer tests exist for all implemented layers in the module:
  - controller/router tests
  - use case tests (if use case exists)
  - service tests
  - repository tests
- [ ] Test doubles (stub/spy/mock/fake) are chosen per boundary and documented in tests
- [ ] Fixture-based regression tests exist for unstable boundary contracts
- [ ] Dual-transport capabilities include parity tests (tRPC vs OpenAPI)
- [ ] Test structure follows `core/testing-service-layer.md`

### Final Module Verification

- [ ] TypeScript compiles without errors
- [ ] All interfaces have implementations
- [ ] Layer test suites pass for implemented layers
- [ ] All error classes have unique codes
- [ ] Business events logged in service layer
- [ ] No logging in repository layer
- [ ] No generic `Error` throws in use cases
- [ ] `requestId` included in all error logs
