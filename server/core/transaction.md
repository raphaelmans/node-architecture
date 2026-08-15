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
| `TransactionContext`        | `shared/kernel/transaction.ts`   | Opaque active transaction client       |
| `TransactionOptions`        | `shared/kernel/transaction.ts`   | Optional transaction-only method input |
| `TransactionManager`        | `shared/kernel/transaction.ts`   | Abstract transaction runner            |
| `DrizzleTransactionManager` | `shared/infra/db/transaction.ts` | Drizzle implementation                 |

## Kernel Abstractions

These types belong in the kernel because they're framework-agnostic contracts used across all layers.

```typescript
// shared/kernel/transaction.ts

/**
 * TransactionContext represents an active database transaction.
 * The private brand prevents arbitrary request/context objects from being
 * passed accidentally. Infrastructure adapters explicitly bridge their
 * concrete transaction type at the database boundary.
 */
declare const transactionContextBrand: unique symbol;
export type TransactionContext = {
  readonly [transactionContextBrand]: "TransactionContext";
};

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
   * - The transaction context (tx) is passed explicitly via TransactionOptions
   */
  run<T>(fn: (tx: TransactionContext) => Promise<T>): Promise<T>;
}
```

## Transaction Options

`TransactionOptions` carries only the active database transaction through application and repository calls.

```typescript
// shared/kernel/transaction.ts

/**
 * Optional transaction participation for a service or repository method.
 */
export interface TransactionOptions {
  /**
   * Active transaction context, if within a transaction.
   * Repositories use this to participate in the transaction.
   */
  tx?: TransactionContext;
}
```

Do not add request, tracing, authentication, or logger fields here. Observability context is propagated independently as described in [Observability](./observability.md).

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
      return fn(tx as unknown as TransactionContext);
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

Repositories accept optional `TransactionOptions` and use the transaction if provided.

```typescript
// modules/user/repositories/user.repository.ts

import { eq } from "drizzle-orm";
import { users, User, UserInsert } from "@/shared/infra/db/schema";
import type { TransactionOptions } from "@/shared/kernel/transaction";
import type { DbClient, DrizzleTransaction } from "@/shared/infra/db/types";

export class UserRepository {
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

### Service: Optional Transaction Pattern

Services accept optional `TransactionOptions`. If provided with a transaction, they participate in it. Otherwise, they own their own transaction.

```typescript
// modules/user/services/user.service.ts

import type { TransactionManager } from "@/shared/kernel/transaction";
import type { TransactionOptions } from "@/shared/kernel/transaction";
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
  async findById(id: string, options?: TransactionOptions): Promise<User | null> {
    return this.userRepository.findById(id, options);
  }

  /**
   * Write operation with optional transaction participation.
   * - If options.tx provided: participates in external transaction
   * - If no options.tx: owns its own transaction
   */
  async create(data: UserInsert, options?: TransactionOptions): Promise<User> {
    if (options?.tx) {
      return this.createInternal(data, options);
    }

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
      throw new ConflictError("Email already in use", { email: data.email });
    }
    return this.userRepository.create(data, options);
  }

  /**
   * Update with optional context.
   */
  async update(
    id: string,
    data: Partial<UserInsert>,
    options?: TransactionOptions,
  ): Promise<User> {
    const exec = async (options: TransactionOptions): Promise<User> => {
      if (data.email) {
        const existing = await this.userRepository.findByEmail(data.email, options);
        if (existing && existing.id !== id) {
          throw new ConflictError("Email already in use", {
            email: data.email,
          });
        }
      }
      return this.userRepository.update(id, data, options);
    };

    if (options?.tx) {
      return exec(options);
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
import type { INotificationOutbox } from "@/modules/notification/outbox/notification-outbox.interface";
import type { RegisterUserCommand } from "../dtos/register-user.command";
import type { User } from "../entities/user";

export class RegisterUserUseCase {
  constructor(
    private userService: IUserService,
    private workspaceService: IWorkspaceService,
    private notificationOutbox: INotificationOutbox,
    private transactionManager: TransactionManager,
  ) {}

  async execute(command: RegisterUserCommand): Promise<User> {
    // Use case owns the transaction for multi-service orchestration
    const user = await this.transactionManager.run(async (tx) => {
      const passwordHash = await hashPassword(command.password);

      // Create user within transaction
      const user = await this.userService.create(
        {
          email: command.email,
          name: command.name,
          passwordHash,
        },
        { tx },
      );

      // Add to workspace within same transaction
      if (command.workspaceId) {
        await this.workspaceService.addMember(command.workspaceId, user.id, {
          tx,
        });
      }

      // Required delivery intent commits atomically with the business write.
      await this.notificationOutbox.enqueueWelcomeEmail(user, { tx });

      return user;
    });

    return user;
  }
}
```

## Transaction Patterns Summary

### Read Operations

**No transaction needed** - use direct repository calls.

```typescript
// Service
async findById(id: string, options?: TransactionOptions): Promise<User | null> {
  return this.userRepository.findById(id, options);
}

// Framework-neutral controller
async execute(input: GetUserInput): Promise<GetUserResponse> {
  const user = await this.userService.findById(input.id);
  if (!user) throw new UserNotFoundError(input.id);
  return toUserResponse(user);
}

// Framework adapter
getById: protectedProcedure
  .input(z.object({ id: z.string() }))
  .query(async ({ input }) => {
    const result = await makeGetUserController().execute(input);
    return wrapResponse(GetUserResponseSchema.parse(result));
  }),
```

### Single-Service Writes

**Service owns the transaction** (or participates if `options.tx` is provided).

```typescript
// Service
async create(data: UserInsert, options?: TransactionOptions): Promise<User> {
  if (options?.tx) {
    return this.createInternal(data, options);
  }
  return this.transactionManager.run((tx) => this.createInternal(data, { tx }));
}

// Framework adapter -> controller -> service
create: protectedProcedure
  .input(CreateUserInputSchema)
  .mutation(async ({ input }) => {
    const result = await makeCreateUserController().execute(input);
    return wrapResponse(CreateUserResponseSchema.parse(result));
  }),
```

### Multi-Service Writes

**Use case owns the transaction.**

```typescript
// Use Case
async execute(command: TransferFundsCommand): Promise<void> {
  await this.transactionManager.run(async (tx) => {
    await this.accountService.debit(command.fromId, command.amount, { tx });
    await this.accountService.credit(command.toId, command.amount, { tx });
    await this.auditService.logTransfer(command, { tx });
  });
}

// Framework adapter -> controller -> use case
transfer: protectedProcedure
  .input(TransferFundsSchema)
  .mutation(async ({ input }) => {
    const result = await makeTransferFundsController().execute(input);
    return wrapResponse(TransferFundsResponseSchema.parse(result));
  }),
```

The route schema is the shared wire contract. The framework-neutral controller maps it to the optional server-only `TransferFundsCommand` before calling the use case.

### Transaction + Side Effects

**External IO happens outside the database transaction. Required delivery intent is persisted inside it through an outbox.**

```typescript
import { APP_ATTRIBUTES } from "@/shared/infra/observability/attributes";

async execute(command: RegisterUserCommand): Promise<User> {
  // Transaction: database operations
  const user = await this.transactionManager.run(async (tx) => {
    const user = await this.userService.create(command.userData, { tx });
    await this.workspaceService.addMember(command.workspaceId, user.id, { tx });
    await this.notificationOutbox.enqueueWelcomeEmail(user, { tx });
    return user;
  });

  // Best-effort effect after commit; failure cannot change business success.
  try {
    await this.productAnalytics.track({
      name: "user_created",
      userId: user.id,
      properties: { signupMethod: "email" },
    });
  } catch (error) {
    this.logger.warn(
      {
        err: error,
        "otel.event.name": "product_analytics.delivery_failed",
        [APP_ATTRIBUTES.targetUserId]: user.id,
        [APP_ATTRIBUTES.productEventName]: "user_created",
      },
      "Product analytics delivery failed",
    );
  }

  return user;
}
```

The worker sends the welcome email after commit from the outbox record. The direct analytics call is best-effort. If analytics delivery must be guaranteed too, enqueue its canonical payload in the same transaction. See [Async Jobs + Outbox](./async-jobs-outbox.md) and [Product Analytics](./product-analytics.md).

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
│  │  ├─ transaction.ts      # TransactionManager, TransactionContext, TransactionOptions
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
│     │  └─ user.repository.ts   # Receives options?.tx
│     ├─ services/
│     │  └─ user.service.ts      # Accepts transaction options, owns or participates
│     └─ use-cases/
│        └─ register-user.use-case.ts  # Owns multi-service transactions
```

## Checklist

- [ ] `TransactionManager` interface defined in `shared/kernel/transaction.ts`
- [ ] `TransactionContext` type alias in kernel (framework-agnostic)
- [ ] `DrizzleTransactionManager` implementation in `shared/infra/db/transaction.ts`
- [ ] `TransactionOptions` contains only an optional `tx` field
- [ ] Repositories accept `options?: TransactionOptions` parameter
- [ ] Repositories use a typed `getClient(options)` boundary to bridge the
  opaque context to the concrete database transaction
- [ ] Services receive `TransactionManager` via constructor
- [ ] Services accept optional `options?: TransactionOptions` for all write methods
- [ ] Services own transactions when no options.tx provided
- [ ] Services participate in external transactions when options.tx provided
- [ ] Use cases own transactions for multi-service orchestration
- [ ] External IO happens after commit; required delivery intent is enqueued transactionally
- [ ] Container provides `transactionManager` as shared dependency
- [ ] Request/trace/logger fields are propagated separately from transaction options
