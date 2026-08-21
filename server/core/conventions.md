# Backend Architecture Conventions

> Core architectural conventions defining layer responsibilities, dependency injection, and the kernel.

## Layer Responsibilities

### Transport + Contract Strategy

- Contract source of truth is `Zod` schemas (see `./api-contracts-zod-first.md`).
- Current primary transport is `tRPC`; OpenAPI is supported as migration/coexistence transport.
- Transport adapters (tRPC routers, Next.js/OpenAPI route handlers, Express/Hono/Nest handlers) must call framework-neutral controllers.
- Business/domain layers MUST NOT import transport-specific types.
- Capability naming and transport mapping rules are defined in `./endpoint-naming.md`.

### Canonical Layer Chain

All backend modules follow this chain:

```text
framework adapter -> controller
                         ├─> service -> repository/provider
                         └─> use case -> service(s) -> repository/provider(s)
```

When a controller selects a use case, that use case coordinates one or more services. When it selects a service, the capability is a single-domain read or write.

Dependency and testing boundaries must align to this flow.

Canonical testing rules are defined in:

- [Testing Service Layer](./testing-service-layer.md)

Cross-cutting runtime standards are defined in:

- [Observability](./observability.md) — correlation, trace/span/event naming, and custom attribute namespace
- [Logging](./logging.md) — `AppLogger`, redaction requirements, and log ownership
- [Product Analytics](./product-analytics.md) — typed behavioral events and analytics adapters

### Framework Adapters

tRPC procedures, Next.js route handlers, Express/Hono/Nest handlers, and OpenAPI route registrations are framework-specific adapters. They are intentionally thin and replaceable.

**Responsibilities:**

- Extract framework request/context values
- Establish observability scope and apply transport middleware
- Authenticate credentials and produce a plain application `Actor`
- Parse untrusted input with the shared Zod contract
- Call one framework-neutral controller factory
- Validate the shared response contract and construct the transport envelope/status
- Let central transport error mapping handle failures

**Rules:**

- No command/result mapping that would need to be repeated in another transport
- No service, use-case, repository, database, or vendor construction/calls
- No module-specific error-to-HTTP/tRPC translation
- Cross-cutting controls (auth and rate limiting) stay in transport middleware/procedures

### Framework-Neutral Controllers

Every externally exposed HTTP/RPC capability has a plain TypeScript controller under `modules/<module>/controllers/`. See [Framework-Neutral Controllers](./controllers.md) for the complete standard.

**Responsibilities:**

- Accept shared contract types and plain application types only
- Map public input and actor data to an internal command when needed
- Call **one** use case or **one** service per operation
- Convert capability-level null outcomes into typed domain errors
- Map internal results/entities to the shared response shape

**Rules:**

- No imports from Next.js, tRPC, Express, Hono, NestJS, or framework request/response packages
- No HTTP status, header, cookie, envelope, or transport error decisions
- No repository access or service-to-service orchestration
- No generic request/transaction/telemetry context object

**Guard placement:**

- Cross-cutting authentication and coarse authorization-context enrichment belongs in reusable transport middleware.
- A capability-specific lookup or invariant belongs in the selected service/use case.
- If a capability needs two services, create a use case and inject it into the controller; do not add an ad-hoc pre-fetch in the framework adapter.

```typescript
// modules/user/user.router.ts

import { z } from "zod";
import { S } from "@/shared/kernel/schemas";
import { GetUserResponseSchema } from "./shared/contracts";

export const userRouter = router({
  getById: protectedProcedure
    .input(z.object({ id: S.ids.generic }))
    .query(async ({ input, ctx }) => {
      const result = await makeGetUserController().execute(
        input,
        toActor(ctx.session),
      );
      return GetUserResponseSchema.parse(result);
    }),
});
```

**Central Error Mapping:**

Domain errors carry a transport-neutral `AppError.kind`. Each transport maps that kind once:

```text
AppError.kind
  -> HTTP adapter: status code
  -> tRPC middleware: TRPCError code
  -> formatter: safe message + appCode + requestId
```

Routers do not repeat `try/catch` blocks or module-specific tRPC mappings. Unknown errors continue to the global formatter and become sanitized internal errors. See [Error Handling](./error-handling.md).

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

- Simple read-only queries (controller calls one service)
- Single-service writes (controller calls one service; service owns the transaction)

```typescript
// modules/user/use-cases/register-user.use-case.ts

export class RegisterUserUseCase {
  constructor(
    private userService: IUserService,
    private workspaceService: IWorkspaceService,
    private notificationOutbox: INotificationOutbox,
    private transactionManager: TransactionManager,
  ) {}

  async execute(command: RegisterUserCommand): Promise<User> {
    const user = await this.transactionManager.run(async (tx) => {
      const user = await this.userService.create(command.userData, { tx });

      if (command.workspaceId) {
        await this.workspaceService.addMember(command.workspaceId, user.id, {
          tx,
        });
      }

      await this.notificationOutbox.enqueueWelcomeEmail(user, { tx });

      return user;
    });

    return user;
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

- A service does not call another service
- No orchestration logic
- No infrastructure knowledge
- Accept optional `TransactionOptions` for external transaction participation
- Receive `AppLogger` only through interface-typed constructor injection when operational business logs are needed
- Constructor dependencies MUST be interface types (not concrete classes)

External side effects (including product analytics), cross-service coordination, and delivery policies belong in a use case. If delivery must survive process failure, the use case records outbox intent inside its transaction. A truly best-effort post-commit effect must be caught and logged so it cannot turn a committed operation into an apparent failure.

**Method patterns:**

- `create(data)` — owns its own transaction
- `create(data, options?)` — participates when `options.tx` is provided, otherwise owns

```typescript
// modules/user/services/user.service.ts

export class UserService implements IUserService {
  constructor(
    private userRepository: IUserRepository,
    private transactionManager: TransactionManager,
  ) {}

  async findById(id: string, options?: TransactionOptions): Promise<User | null> {
    return this.userRepository.findById(id, options);
  }

  async create(data: UserInsert, options?: TransactionOptions): Promise<User> {
    // If options has a transaction, participate in it
    if (options?.tx) {
      return this.createInternal(data, options);
    }

    // Otherwise, own the transaction
    return this.transactionManager.run(async (tx) => {
      return this.createInternal(data, { tx });
    });
  }

  private async createInternal(
    data: UserInsert,
    options: TransactionOptions,
  ): Promise<User> {
    const existing = await this.userRepository.findByEmail(data.email, options);
    if (existing) {
      throw new UserEmailConflictError(data.email);
    }
    return this.userRepository.create(data, options);
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
- Accept transaction context via `TransactionOptions`
- Never create transactions
- Repository interfaces MUST be defined and implemented explicitly

```typescript
// modules/user/repositories/user.repository.ts

export class UserRepository implements IUserRepository {
  constructor(private db: DbClient) {}

  private getClient(options?: TransactionOptions): DbClient | DrizzleTransaction {
    return (options?.tx as unknown as DrizzleTransaction) ?? this.db;
  }

  async findById(id: string, options?: TransactionOptions): Promise<User | null> {
    const client = this.getClient(options);
    const result = await client
      .select()
      .from(users)
      .where(eq(users.id, id))
      .limit(1);

    return result[0] ?? null;
  }

  async create(data: UserInsert, options?: TransactionOptions): Promise<User> {
    const client = this.getClient(options);
    const result = await client.insert(users).values(data).returning();

    return result[0];
  }
}
```

**Pessimistic Locking (`FOR UPDATE`) Pattern:**

For contended-state entities (reservations, availability slots), repositories expose `findByIdForUpdate` variants:

```typescript
async findByIdForUpdate(id: string, options: TransactionOptions): Promise<Entity | null> {
  const tx = options.tx as unknown as DrizzleTransaction;
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

- Only used within an active transaction (`options.tx` is required, not optional)
- Execute on the transaction client (`options.tx`) so row locks are held until transaction end
- Name methods `findByIdForUpdate`, `findByIdsForUpdate` to make locking intent explicit
- Use only for entities where concurrent writes could cause data corruption

**Repository Importing from `shared/domain.ts`:**

Repositories may import pure functions from `modules/<module>/shared/domain.ts` for in-memory post-query filtering when the filtering logic is domain-specific and cannot be expressed in SQL:

```typescript
import { filterBlockingOverlaps } from "../shared/domain";

async findConflicting(slotId: string, options?: TransactionOptions) {
  const rows = await this.getClient(options).select().from(slots).where(...);
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

- Do not construct cross-layer dependencies outside factories/composition roots
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
import { appLogger } from "./logger";
import { productAnalytics } from "./analytics";
import type { TransactionManager } from "@/shared/kernel/transaction";
import type { AppLogger } from "@/shared/kernel/logger";
import type { ProductAnalytics } from "@/shared/kernel/product-analytics";

export interface Container {
  db: typeof db;
  transactionManager: TransactionManager;
  appLogger: AppLogger;
  productAnalytics: ProductAnalytics;
}

let container: Container | null = null;

export function getContainer(): Container {
  if (!container) {
    container = {
      db,
      transactionManager: new DrizzleTransactionManager(db),
      appLogger,
      productAnalytics,
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
import { RegisterUserController } from "../controllers/register-user.controller";

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
    makeNotificationOutbox(),
    getContainer().transactionManager,
  );
}

// Framework adapters resolve controllers, never inner layers directly.
export function makeRegisterUserController() {
  return new RegisterUserController(
    makeRegisterUserUseCase(),
  );
}
```

**Key principles:**

- Container owns shared infrastructure (database, transaction manager, logger, analytics adapters)
- Module factories own module-specific wiring
- Repositories and services are lazy singletons (stateless)
- Use cases and controllers are new instances per factory call by default. Services do not depend on use cases; controllers select the appropriate use case or service.
- Framework adapters invoke controller factories only.
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

- TypeScript types and runtime-neutral language features
- Approved isomorphic libraries (see below)

Kernel must NOT import:

- `infra/`
- `modules/`

### Approved Kernel Dependencies

- **zod** — Schema validation and type inference
  - Used for: shared contracts and runtime type checks

Kernel modules that are imported by the client must remain browser-safe. Node built-ins, environment access, and `server-only` markers belong in infrastructure/runtime modules, not the kernel.

### Kernel Contents

```
shared/kernel/
├─ contracts/         # Universal transport primitives only
│  └─ index.ts
├─ transaction.ts     # TransactionManager + TransactionContext + TransactionOptions
├─ logger.ts          # AppLogger interface
├─ product-analytics.ts # ProductAnalytics interface + event contracts
├─ errors.ts          # Base AppError definitions
├─ public-error.ts    # Public message policy helpers (getPublicErrorMessage, isInternalAppError)
├─ pagination.ts      # Pagination types and schemas
├─ response.ts        # API response types
├─ schemas.ts         # Browser-safe reusable Zod primitives
└─ auth.ts            # Session, UserRole, Permission types
```

**Why these belong in kernel:**

- They are universal contracts
- They are depended on by many layers
- They must remain stable over time

## Contracts, Commands, and Entities

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

### Shared API Contracts

- Represent data crossing boundaries
- Used by clients, framework adapters, and framework-neutral controllers
- Shaped for API consumers
- Validated at both sides of the network boundary

For a single-project Next.js repository containing both client and server code, module-owned wire contracts use this mapping:

```text
src/lib/modules/<module>/shared/contracts/
```

For a monorepo topology, move the same role to `packages/contracts/<module>/` when it crosses package boundaries. A new module places capability application behavior in `packages/capabilities/<module>/` and concrete infrastructure in activated adapter packages by default; preserve cohesive existing app-local ownership until migration is explicit. Deployable composition roots select the adapters. See [Monorepo Package Boundaries](../../monorepo/core/package-boundaries.md).

**Zod-based contract pattern:**

```typescript
// src/lib/modules/user/shared/contracts/create-user.contract.ts

import { z } from "zod";

export const CreateUserInputSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
});

export const CreateUserResponseSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string(),
  createdAt: z.string().datetime(),
});

export type CreateUserInput = z.infer<typeof CreateUserInputSchema>;
export type CreateUserResponse = z.infer<typeof CreateUserResponseSchema>;
```

Naming and ownership rules:

- Shared wire schemas use `<Capability>InputSchema` and `<Capability>ResponseSchema`.
- Shared wire types are inferred and use `<Capability>Input` and `<Capability>Response`.
- Application-wide primitives such as pagination and response envelopes stay in `shared/kernel/`.
- Module-owned contracts do not move to the kernel merely because the frontend imports them.
- Server-only commands/internal DTOs may remain in `lib/modules/<module>/dtos/` or beside their use case.
- Client-only form schemas and view models remain in `src/features/<feature>/`.
- Database/ORM entities are never imported into shared contracts or client code.

See [API Contracts: Zod-First](./api-contracts-zod-first.md) for the complete dependency and mapping rules.

## Extended Module Sub-Folders

Beyond the canonical structure (`controllers/`, `dtos/`, `errors/`, `factories/`, `repositories/`, `services/`, `use-cases/`, `shared/`), modules may contain these additional sub-folders when the domain requires them:

| Sub-Folder | Purpose | When to Use |
| --- | --- | --- |
| `lib/` | Stateless utility/parsing functions internal to the module | Module needs non-domain parsers, formatters, or adapters (e.g., CSV/XLSX/ICS parsing, AI mapping) |
| `ops/` | One-off operational side-effect triggers | Module has domain-aware side effects triggered by other modules (e.g., posting a chat message when a reservation status changes) |
| `http/` | Non-tRPC framework-adapter helpers | Module receives HTTP requests outside tRPC (for example queue dispatch or webhook entrypoints); helpers contain transport mechanics and delegate to a controller/specialized handler |
| `queues/` | Queue interface + provider implementation | Module uses async job dispatch with an interface boundary (e.g., `INotificationDispatchQueue` + `QStashNotificationDispatchQueue`) |
| `providers/` | Vendor-specific adapter implementations | Module abstracts an external service with a swappable provider interface (e.g., `IChatProvider` with Stream Chat and Supabase backends) |
| `admin/` | Admin-gated router and related procedures | Module exposes admin-specific procedures using `adminProcedure` |
| `schemas/` | Validation schemas separate from DTOs | Module has many schemas that serve multiple layers |

Rules:

- These sub-folders are opt-in. Only create them when the module's complexity justifies them.
- `providers/` co-locate the interface and implementations together inside the module, not in `shared/infra/`. This keeps vendor-specific code contained.
- `queues/` follow the same interface + implementation pattern as `providers/`.
- `ops/` functions are called from use cases after commit, not from routers or services directly.

## Module Shared Code (`lib/modules/<module>/shared/`)

Some modules need **shared, reusable code** that is still domain-specific (not kernel).

Convention:

- Put module-owned shared code in the topology's resolved isomorphic boundary (`lib/modules/<module>/shared/` in one project or an activated contract/domain package when cross-package).
- Treat it as potentially **isomorphic**: safe to import from both server and client code when needed.

Typical contents:

- `contracts/` containing Zod request/response schemas and inferred wire types
- deterministic calculations and invariants (pure functions)
- domain-specific error types that do not depend on server infrastructure

Rules:

- Must not import `shared/infra/*` (DB, logger, auth, tRPC init).
- Must not depend on framework-only code.
- Keep it pure and portable. Extract a workspace package only when current reuse, ownership, or runtime isolation activates that boundary.
- Cross-runtime API contracts specifically belong in `shared/contracts/`; do not duplicate them in client feature folders or server `dtos/`.

Example:

- `modules/user/shared/contracts/create-user.contract.ts`
- `modules/user/shared/domain.ts`

### Mapping Rules

- Controllers map entities/internal results to shared response shapes; framework adapters validate and serialize those shapes
- Repositories never return DTOs
- Public input-to-command and result-to-response mapping happens in controllers or dedicated pure mappers called by controllers

## Complete Dependency Graph

```
Next.js / tRPC / OpenAPI adapter
  -> make<Capability>Controller()
       -> <Capability>Controller
            ├─ simple read/write -> <Module>Service
            │                         -> <Module>Repository
            │
            └─ orchestration     -> <Capability>UseCase
                                      -> Service A -> Repository A
                                      -> Service B -> Repository B
                                      -> Outbox/provider port

Factory/composition root constructs the complete graph:

makeRegisterUserController()
  -> RegisterUserController(
       RegisterUserUseCase(
         UserService(UserRepository(db), transactionManager),
         WorkspaceService(WorkspaceRepository(db), transactionManager),
         notificationOutbox,
         transactionManager,
       ),
     )
```

## Return Type Summary

| Layer | Returns | Type source |
| --- | --- | --- |
| Repository | Entity/record | Drizzle/ORM schema |
| Service | Entity or internal domain result | Repository/domain model |
| Use case | Internal application result | Use-case contract |
| Controller | Shared response shape | `modules/<module>/shared/contracts/` |
| Framework adapter | Kernel envelope + validated shared response payload | `shared/kernel/` + `modules/<module>/shared/contracts/` |

**Rule:** Entities may flow internally, but every public transport maps and validates output through a shared response contract before serialization.

## Implemented Event-Driven Patterns

See [Event Patterns](./event-patterns.md) for production-complete patterns:

- Domain event log (append-only event tables for real-time broadcasting)
- Notification outbox (transactional enqueue + async dispatch)
- Side-effect procedures (`ops/` for best-effort post-commit work)
- Command/query separation (framework-adapter-level, service-level, client API-level)

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
- [ ] `getClient(options)` bridges the opaque context only at the repository boundary
- [ ] Methods that may participate in a transaction accept `options?: TransactionOptions`
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
- [ ] Read methods: pass transaction `options` through when provided
- [ ] Write methods: check `options?.tx` - participate if present, otherwise create transaction
- [ ] Operational business events use injected `AppLogger`
- [ ] Does not emit product analytics or call external providers; those belong in a use case
- [ ] Event names: `<entity>.<past_tense_action>` format
- [ ] Returns `null` for not found when absence is an internal result (controller decides the public capability error)
- [ ] No service-to-service calls; cross-service work belongs in a use case

### Use Case Layer (`use-cases/<name>.use-case.ts`)

- [ ] Only created for multi-service orchestration or side effects
- [ ] Constructor accepts **interface** types (not concrete classes)
- [ ] Constructor accepts `TransactionManager`
- [ ] Constructor accepts interface-typed `AppLogger`/`ProductAnalytics` only when used
- [ ] Throws **domain errors** (NOT generic `Error`)
- [ ] Required external delivery intent is enqueued INSIDE the transaction through an outbox port
- [ ] Direct external calls occur only AFTER commit and are caught/logged as best-effort
- [ ] DB operations occur INSIDE the transaction
- [ ] Operational logs use injected `AppLogger`; product events use injected `ProductAnalytics`

```typescript
// CORRECT - domain error
if (!result) throw new EntityNotFoundError(id);

// WRONG - generic error
if (!result) throw new Error('Entity not found');
```

### Factory Layer (`factories/<module>.factory.ts`)

- [ ] Lazy singleton for DB-backed modules (repository, service)
- [ ] Request-scoped for request-dependent modules (auth with cookies)
- [ ] Exposes one controller factory per public capability
- [ ] Framework adapters use controller factories only
- [ ] Returns interface type in JSDoc/type hints
- [ ] Uses `getContainer()` for shared dependencies

### Shared API Contract (`shared/contracts/`)

- [ ] One Zod schema source for each public input and response
- [ ] Types are inferred as `<Capability>Input` and `<Capability>Response`
- [ ] Both client `featureApi` and server transport import the same contract
- [ ] Contract models the serialized wire shape, including ISO datetime strings
- [ ] No imports from DB, server infrastructure, framework code, environment, or client UI
- [ ] Sensitive/internal entity fields are absent from response schemas

### Server-Only Command DTO (`dtos/`, Optional)

- [ ] Exists only when internal orchestration differs from the public input contract
- [ ] Is mapped explicitly from the shared input contract
- [ ] Is never imported by client code

### Controller Layer (`controllers/<capability>.controller.ts`)

- [ ] Plain TypeScript with no Next.js, tRPC, Express, Hono, NestJS, or transport imports
- [ ] Accepts shared input types and plain application types such as `Actor`
- [ ] Constructor accepts one service or use-case interface
- [ ] Maps shared input to an internal command when shapes differ
- [ ] Calls exactly one use case or service
- [ ] Converts capability-level null outcomes into typed domain errors
- [ ] Maps internal result/entity values to the shared response shape
- [ ] Accepts no request, observability, transaction, or service-locator context object

### Framework Adapter Layer (`<module>.router.ts`, `app/api/**/route.ts`)

- [ ] Uses appropriate procedure base (`publicProcedure`, `protectedProcedure`, `adminProcedure`, or rate-limited variant)
- [ ] Input validated with `.input(ZodSchema)`
- [ ] Calls one controller factory: `make<Capability>Controller()`
- [ ] Never calls or constructs a service, use case, repository, or provider directly
- [ ] No business logic
- [ ] No direct logging (handled by middleware)
- [ ] Shared response schema validates the controller result before serialization
- [ ] Domain errors bubble to the shared transport error middleware/handler
- [ ] No repeated `try/catch` solely for status/code translation
- [ ] Central mapping derives transport codes from `AppError.kind`
- [ ] No raw error messages from libraries/DB in `TRPCError` message field

### Transport Infrastructure (`shared/infra/trpc/`, OpenAPI/HTTP route adapters)

Common:

- [ ] Zod schema contracts reused from canonical contract definitions
- [ ] No business logic in transport adapter
- [ ] Framework adapter calls a framework-neutral controller only
- [ ] Request-scoped metadata (`requestId`) present in error mapping
- [ ] Auth/rate-limit enforcement applied at transport boundary
- [ ] Async observability scope established before application code runs

tRPC-specific:

- [ ] Logger middleware applied to ALL procedures
- [ ] Every procedure inherits central application-error mapping and request logging
- [ ] `publicProcedure = baseProcedure`
- [ ] `protectedProcedure = baseProcedure.use(authMiddleware)`
- [ ] `adminProcedure = protectedProcedure.use(adminMiddleware)` (requires `session.role === "admin"`)
- [ ] `rateLimitedProcedure(tier)` — factory returning rate-limited public procedure
- [ ] `protectedRateLimitedProcedure(tier)` — factory returning rate-limited protected procedure
- [ ] `adminRateLimitedProcedure(tier)` — factory returning rate-limited admin procedure
- [ ] Error formatter uses contextual `AppLogger`; correlation is added by the logger adapter
- [ ] Known errors (`AppError`) logged at `warn` level
- [ ] Unknown errors logged at `error` level
- [ ] Context includes contextual `log`, `requestId`, `clientIdentifier`, `clientIdentifierSource`, `cookies`, `origin`
- [ ] Context creation enriches session with role from `user_roles` table when authenticated
- [ ] Application services receive the contextual `AppLogger` through factories, not transport context parameters

OpenAPI-specific:

- [ ] Route handlers validate inputs with shared Zod schemas and call the same controller as other transports
- [ ] Error mapping returns shared error contract (`code`, `message`, `requestId`, `details?`)
- [ ] Response payload shape follows shared API contract guidance

```typescript
import { APP_ATTRIBUTES } from "@/shared/infra/observability/attributes";

// Error response includes requestId; contextual logger adds its namespaced form.
ctx?.log.warn(
  {
    err: cause,
    "error.type": cause.code,
    [APP_ATTRIBUTES.errorDetails]: cause.details,
  },
  cause.message,
);
```

### Root Router Registration

- [ ] tRPC router imported in `shared/infra/trpc/root.ts` (if tRPC is enabled)
- [ ] OpenAPI framework adapter wired in runtime router tree (if OpenAPI is enabled)

### Testability Standard (MUST)

- [ ] Layer tests exist for all implemented layers in the module:
  - framework-adapter tests
  - controller tests
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
- [ ] Operational business events logged through injected `AppLogger`
- [ ] Product events emitted through `ProductAnalytics`, not `AppLogger`
- [ ] No logging in repository layer
- [ ] No generic `Error` throws in use cases
- [ ] Request-scoped logs receive the namespaced request ID and trace context from `AppLogger`
