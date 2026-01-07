# Transaction Management

> Transaction management abstraction, Drizzle implementation, and usage patterns.

## Principles

- Transactions are managed through an abstract interface
- Implementation details (Drizzle, Prisma, etc.) are hidden from business logic
- Services own transactions for single-service writes OR participate in external transactions
- Use cases own transactions for multi-service orchestration
- Repositories receive transaction context, never create transactions

## Key Components

| Component                   | Location                             | Responsibility                         |
| --------------------------- | ------------------------------------ | -------------------------------------- |
| `TransactionContext`        | `shared/kernel/transaction.ts`   | Type alias for transaction client      |
| `TransactionManager`        | `shared/kernel/transaction.ts`   | Abstract interface                     |
| `RequestContext`            | `shared/kernel/context.ts`       | Carries transaction through call stack |
| `DrizzleTransactionManager` | `shared/infra/db/transaction.ts` | Drizzle implementation                 |

## Kernel Abstractions

These types belong in the kernel because they're framework-agnostic contracts used across all layers.

```typescript
// shared/kernel/transaction.ts

/**
 * TransactionContext represents an active database transaction.
 * This is a type alias that will be narrowed by the infrastructure layer.
 */
export type TransactionContext = unknown;

/**
 * TransactionManager provides a framework-agnostic interface for
 * running code within a database transaction.
 */
export interface TransactionManager {
  /**
   * Executes the given function within a transaction.
   *
   * - If the function completes successfully, the transaction is committed
   * - If the function throws, the transaction is rolled back
   * - The transaction context (tx) should be passed to repositories via RequestContext
   */
  run<T>(fn: (tx: TransactionContext) => Promise<T>): Promise<T>;
}
```

## Request Context

The `RequestContext` carries the transaction context through the call stack.

```typescript
// shared/kernel/context.ts

import type { TransactionContext } from "./transaction";

/**
 * RequestContext is passed through layers to provide:
 * - Transaction context for database operations
 * - Future: tracing context, user context, etc.
 */
export interface RequestContext {
  /**
   * Active transaction context, if within a transaction.
   * Repositories use this to participate in the transaction.
   */
  tx?: TransactionContext;

  /**
   * Request ID for correlation in logs and error responses.
   */
  requestId?: string;

  // Future extensions:
  // traceId?: string;
  // spanId?: string;
}
```

## Drizzle Implementation

### Type Definitions

```typescript
// shared/infra/db/types.ts

import type { ExtractTablesWithRelations } from "drizzle-orm";
import type { PgTransaction } from "drizzle-orm/pg-core";
import type { PostgresJsQueryResultHKT } from "drizzle-orm/postgres-js";
import * as schema from "./schema";

type AppSchema = typeof schema;

/**
 * The main Drizzle database client type.
 * Import AppDatabase from drizzle.ts for the actual type.
 */
export type { AppDatabase as DbClient } from "./drizzle";

/**
 * Drizzle transaction type for postgres.js driver.
 * Used when passing transaction context to repositories.
 */
export type DrizzleTransaction = PgTransaction<
  PostgresJsQueryResultHKT,
  AppSchema,
  ExtractTablesWithRelations<AppSchema>
>;
```

### Transaction Manager Implementation

```typescript
// shared/infra/db/transaction.ts

import type {
  TransactionManager,
  TransactionContext,
} from "@/shared/kernel/transaction";
import type { DbClient, DrizzleTransaction } from "./types";

/**
 * Drizzle-specific implementation of TransactionManager.
 */
export class DrizzleTransactionManager implements TransactionManager {
  constructor(private db: DbClient) {}

  async run<T>(fn: (tx: TransactionContext) => Promise<T>): Promise<T> {
    return this.db.transaction(async (tx: DrizzleTransaction) => {
      return fn(tx as TransactionContext);
    });
  }
}
```

### Database Client Setup

Uses `postgres.js` driver for better serverless compatibility (recommended over `node-postgres`).

```typescript
// shared/infra/db/drizzle.ts

import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

/**
 * Create database connection - singleton pattern for development.
 * Uses postgres.js driver for better serverless compatibility.
 */
const createDatabase = () => {
  const isProduction = process.env.NODE_ENV === "production";
  const isVercel = process.env.VERCEL === "1";

  const connectionString = process.env.DATABASE_URL;

  if (!connectionString) {
    throw new Error("DATABASE_URL is not defined");
  }

  const client = postgres(connectionString, {
    connect_timeout: 30,
    idle_timeout: 20 * 60, // 20 minutes
    max_lifetime: 60 * 30, // 30 minutes
    max: isVercel ? 5 : 10, // Lower for serverless
    prepare: false,
    onnotice: isProduction ? () => {} : undefined,
  });

  return drizzle({ client, casing: "snake_case", schema });
};

// Use existing connection if available (development)
const db = global.__db ?? createDatabase();

// Store globally in development to prevent multiple instances during hot reload
if (process.env.NODE_ENV !== "production") {
  global.__db = db;
}

declare global {
  var __db: ReturnType<typeof createDatabase> | undefined;
}

export type AppDatabase = typeof db;

export { db };
```

## Container Integration

```typescript
// shared/infra/container.ts

import { db } from "./db/drizzle";
import { DrizzleTransactionManager } from "./db/transaction";
import type { TransactionManager } from "@/shared/kernel/transaction";

export interface Container {
  db: DbClient;
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

## Usage Patterns

### Repository: Receiving Transaction Context

Repositories accept optional `RequestContext` and use the transaction if provided.

```typescript
// modules/user/repositories/user.repository.ts

import { eq } from "drizzle-orm";
import { users, User, UserInsert } from "@/shared/infra/db/schema";
import type { RequestContext } from "@/shared/kernel/context";
import type { DbClient, DrizzleTransaction } from "@/shared/infra/db/types";

export class UserRepository {
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

### Service: Optional Context Pattern

Services accept optional `RequestContext`. If provided with a transaction, they participate in it. Otherwise, they own their own transaction.

```typescript
// modules/user/services/user.service.ts

import type { TransactionManager } from "@/shared/kernel/transaction";
import type { RequestContext } from "@/shared/kernel/context";
import { ConflictError } from "@/shared/kernel/errors";
import { User, UserInsert } from "@/shared/infra/db/schema";
import type { IUserRepository } from "../repositories/user.repository.interface";

export class UserService {
  constructor(
    private userRepository: IUserRepository,
    private transactionManager: TransactionManager,
  ) {}

  /**
   * Read operation - no transaction needed.
   */
  async findById(id: string, ctx?: RequestContext): Promise<User | null> {
    return this.userRepository.findById(id, ctx);
  }

  /**
   * Write operation with optional context.
   * - If ctx.tx provided: participates in external transaction
   * - If no ctx.tx: owns its own transaction
   */
  async create(data: UserInsert, ctx?: RequestContext): Promise<User> {
    if (ctx?.tx) {
      return this.createInternal(data, ctx);
    }

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
      throw new ConflictError("Email already in use", { email: data.email });
    }
    return this.userRepository.create(data, ctx);
  }

  /**
   * Update with optional context.
   */
  async update(
    id: string,
    data: Partial<UserInsert>,
    ctx?: RequestContext,
  ): Promise<User> {
    const exec = async (ctx: RequestContext): Promise<User> => {
      if (data.email) {
        const existing = await this.userRepository.findByEmail(data.email, ctx);
        if (existing && existing.id !== id) {
          throw new ConflictError("Email already in use", {
            email: data.email,
          });
        }
      }
      return this.userRepository.update(id, data, ctx);
    };

    if (ctx?.tx) {
      return exec(ctx);
    }
    return this.transactionManager.run((tx) => exec({ tx }));
  }
}
```

### Use Case: Owning Multi-Service Transactions

Use cases create transactions when orchestrating multiple services.

```typescript
// modules/user/use-cases/register-user.use-case.ts

import type { TransactionManager } from "@/shared/kernel/transaction";
import type { IUserService } from "../services/user.service.interface";
import type { IWorkspaceService } from "@/modules/workspace/services/workspace.service.interface";
import type { IEmailService } from "@/shared/infra/email/email.service.interface";
import { RegisterUserDTO } from "../dtos/register-user.dto";

export class RegisterUserUseCase {
  constructor(
    private userService: IUserService,
    private workspaceService: IWorkspaceService,
    private emailService: IEmailService,
    private transactionManager: TransactionManager,
  ) {}

  async execute(input: RegisterUserDTO): Promise<UserPublic> {
    // Use case owns the transaction for multi-service orchestration
    const user = await this.transactionManager.run(async (tx) => {
      const passwordHash = await hashPassword(input.password);

      // Create user within transaction
      const user = await this.userService.create(
        {
          email: input.email,
          name: input.name,
          passwordHash,
        },
        { tx },
      );

      // Add to workspace within same transaction
      if (input.workspaceId) {
        await this.workspaceService.addMember(input.workspaceId, user.id, {
          tx,
        });
      }

      return user;
    });

    // Side effects happen OUTSIDE the transaction
    await this.emailService.sendWelcomeEmail(user.email, user.name);

    return omitSensitive(user);
  }
}
```

## Transaction Patterns Summary

### Read Operations

**No transaction needed** - use direct repository calls.

```typescript
// Service
async findById(id: string, ctx?: RequestContext): Promise<User | null> {
  return this.userRepository.findById(id, ctx);
}

// Router
getById: protectedProcedure
  .input(z.object({ id: z.string() }))
  .query(async ({ input }) => {
    return makeUserService().findById(input.id);
  }),
```

### Single-Service Writes

**Service owns the transaction** (or participates if ctx.tx provided).

```typescript
// Service
async create(data: UserInsert, ctx?: RequestContext): Promise<User> {
  if (ctx?.tx) {
    return this.createInternal(data, ctx);
  }
  return this.transactionManager.run((tx) => this.createInternal(data, { tx }));
}

// Router - calls service directly
create: protectedProcedure
  .input(CreateUserSchema)
  .mutation(async ({ input }) => {
    return makeUserService().create(input);
  }),
```

### Multi-Service Writes

**Use case owns the transaction.**

```typescript
// Use Case
async execute(input: TransferFundsDTO): Promise<void> {
  await this.transactionManager.run(async (tx) => {
    await this.accountService.debit(input.fromId, input.amount, { tx });
    await this.accountService.credit(input.toId, input.amount, { tx });
    await this.auditService.logTransfer(input, { tx });
  });
}

// Router - calls use case
transfer: protectedProcedure
  .input(TransferFundsSchema)
  .mutation(async ({ input }) => {
    return makeTransferFundsUseCase().execute(input);
  }),
```

### Transaction + Side Effects

**Side effects happen outside the transaction.**

```typescript
async execute(input: RegisterUserDTO): Promise<UserPublic> {
  // Transaction: database operations
  const user = await this.transactionManager.run(async (tx) => {
    const user = await this.userService.create(userData, { tx });
    await this.workspaceService.addMember(wsId, user.id, { tx });
    return user;
  });

  // Side effects: after transaction commits
  await this.emailService.sendWelcomeEmail(user.email, user.name);
  await this.analyticsService.trackRegistration(user.id);

  return user;
}
```

## Error Handling in Transactions

### Automatic Rollback

Drizzle automatically rolls back on any thrown error.

```typescript
await this.transactionManager.run(async (tx) => {
  await this.userRepository.create(user1, { tx });
  await this.userRepository.create(user2, { tx }); // Throws ConflictError
  // Transaction is rolled back, user1 is NOT created
});
```

### Explicit Validation Before Commit

Validate everything before making changes when possible.

```typescript
await this.transactionManager.run(async (tx) => {
  // Validate first
  const fromAccount = await this.accountRepository.findById(fromId, { tx });
  const toAccount = await this.accountRepository.findById(toId, { tx });

  if (!fromAccount) throw new AccountNotFoundError(fromId);
  if (!toAccount) throw new AccountNotFoundError(toId);
  if (fromAccount.balance < amount) {
    throw new BusinessRuleError("Insufficient funds");
  }

  // Then mutate
  await this.accountRepository.debit(fromId, amount, { tx });
  await this.accountRepository.credit(toId, amount, { tx });
});
```

## Testing Transactions

### Mocking TransactionManager

```typescript
// tests/mocks/transaction.mock.ts

import type {
  TransactionManager,
  TransactionContext,
} from "@/shared/kernel/transaction";

export class MockTransactionManager implements TransactionManager {
  async run<T>(fn: (tx: TransactionContext) => Promise<T>): Promise<T> {
    return fn({} as TransactionContext);
  }
}
```

### Integration Tests

```typescript
describe("UserService", () => {
  let userService: UserService;

  beforeEach(() => {
    resetContainer();
    const container = getContainer();
    const userRepository = new UserRepository(container.db);
    userService = new UserService(userRepository, container.transactionManager);
  });

  afterEach(async () => {
    await getContainer().db.delete(users);
  });

  it("rolls back on conflict", async () => {
    await userService.create({ email: "test@example.com", name: "Test" });

    await expect(
      userService.create({ email: "test@example.com", name: "Test 2" }),
    ).rejects.toThrow(ConflictError);

    const count = await getContainer().db.select().from(users);
    expect(count).toHaveLength(1);
  });
});
```

## Folder Structure

```
src/lib/
├─ shared/
│  ├─ kernel/
│  │  ├─ transaction.ts      # TransactionManager interface, TransactionContext type
│  │  ├─ context.ts          # RequestContext interface
│  │  └─ errors.ts           # Base error classes
│  └─ infra/
│     ├─ db/
│     │  ├─ drizzle.ts       # Database client setup
│     │  ├─ transaction.ts   # DrizzleTransactionManager implementation
│     │  ├─ types.ts         # DbClient, DrizzleTransaction types
│     │  └─ schema.ts        # Table definitions
│     └─ container.ts        # Composition root
│
├─ modules/
│  └─ user/
│     ├─ repositories/
│     │  └─ user.repository.ts   # Receives ctx?.tx
│     ├─ services/
│     │  └─ user.service.ts      # Accepts optional ctx, owns or participates
│     └─ use-cases/
│        └─ register-user.use-case.ts  # Owns multi-service transactions
```

## Checklist

- [ ] `TransactionManager` interface defined in `shared/kernel/transaction.ts`
- [ ] `TransactionContext` type alias in kernel (framework-agnostic)
- [ ] `DrizzleTransactionManager` implementation in `shared/infra/db/transaction.ts`
- [ ] `RequestContext` includes optional `tx` field
- [ ] Repositories accept `ctx?: RequestContext` parameter
- [ ] Repositories use `ctx?.tx ?? this.db` pattern
- [ ] Services receive `TransactionManager` via constructor
- [ ] Services accept optional `ctx?: RequestContext` for all write methods
- [ ] Services own transactions when no ctx.tx provided
- [ ] Services participate in external transactions when ctx.tx provided
- [ ] Use cases own transactions for multi-service orchestration
- [ ] Side effects happen outside transactions
- [ ] Container provides `transactionManager` as shared dependency
