# Transaction Manager Architecture

> **Purpose**: This document defines the transaction management abstraction, its Drizzle implementation, and patterns for use across the application.

---

## 1. Overview

**Principles:**

- Transactions are managed through an abstract interface
- Implementation details (Drizzle, Prisma, etc.) are hidden from business logic
- Services own transactions for single-service writes
- Use cases own transactions for multi-service orchestration
- Repositories receive transaction context, never create transactions

**Key Components:**

| Component | Location | Responsibility |
|-----------|----------|----------------|
| `TransactionContext` | `shared/kernel/transaction.ts` | Type alias for transaction client |
| `TransactionManager` | `shared/kernel/transaction.ts` | Abstract interface |
| `DrizzleTransactionManager` | `shared/infra/db/transaction.ts` | Drizzle implementation |

---

## 2. Kernel Abstractions

These types belong in the kernel because they're framework-agnostic contracts used across all layers.

```typescript
// shared/kernel/transaction.ts

/**
 * TransactionContext represents an active database transaction.
 * This is a type alias that will be narrowed by the infrastructure layer.
 * 
 * In the kernel, we keep it abstract. The actual type comes from
 * the infrastructure (Drizzle, Prisma, etc.)
 */
export type TransactionContext = unknown;

/**
 * TransactionManager provides a framework-agnostic interface for
 * running code within a database transaction.
 * 
 * Usage:
 * ```typescript
 * const result = await transactionManager.run(async (tx) => {
 *   await repo1.create(data1, { tx });
 *   await repo2.create(data2, { tx });
 *   return result;
 * });
 * ```
 */
export interface TransactionManager {
  /**
   * Executes the given function within a transaction.
   * 
   * - If the function completes successfully, the transaction is committed
   * - If the function throws, the transaction is rolled back
   * - The transaction context (tx) should be passed to repositories via RequestContext
   * 
   * @param fn - Function to execute within the transaction
   * @returns The result of the function
   * @throws Re-throws any error from the function after rollback
   */
  run<T>(fn: (tx: TransactionContext) => Promise<T>): Promise<T>;
}
```

---

## 3. Request Context Integration

The `RequestContext` carries the transaction context through the call stack.

```typescript
// shared/kernel/context.ts

import type { TransactionContext } from './transaction';

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

---

## 4. Drizzle Implementation

### 4.1 Type Definitions

```typescript
// shared/infra/db/types.ts

import { NodePgDatabase } from 'drizzle-orm/node-postgres';
import * as schema from './schema';

/**
 * The main Drizzle database client type.
 */
export type DbClient = NodePgDatabase<typeof schema>;

/**
 * Drizzle transaction type - this is what gets passed to repositories.
 * It's the same interface as DbClient but represents an active transaction.
 */
export type DrizzleTransaction = Parameters<
  Parameters<DbClient['transaction']>[0]
>[0];
```

### 4.2 Transaction Manager Implementation

```typescript
// shared/infra/db/transaction.ts

import type { TransactionManager, TransactionContext } from '@/shared/kernel/transaction';
import type { DbClient, DrizzleTransaction } from './types';

/**
 * Drizzle-specific implementation of TransactionManager.
 * 
 * This class wraps Drizzle's transaction API to provide:
 * - Automatic commit on success
 * - Automatic rollback on error
 * - Type-safe transaction context
 */
export class DrizzleTransactionManager implements TransactionManager {
  constructor(private db: DbClient) {}

  /**
   * Executes the given function within a Drizzle transaction.
   * 
   * @example
   * ```typescript
   * const user = await transactionManager.run(async (tx) => {
   *   const user = await userRepo.create(userData, { tx });
   *   await workspaceRepo.addMember(workspaceId, user.id, { tx });
   *   return user;
   * });
   * ```
   */
  async run<T>(fn: (tx: TransactionContext) => Promise<T>): Promise<T> {
    return this.db.transaction(async (tx: DrizzleTransaction) => {
      return fn(tx as TransactionContext);
    });
  }
}
```

### 4.3 Database Client Setup

```typescript
// shared/infra/db/drizzle.ts

import { drizzle } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';
import * as schema from './schema';
import type { DbClient } from './types';

/**
 * Global singleton for database pool (survives serverless warm starts).
 */
const globalForDb = globalThis as unknown as {
  pool: Pool | undefined;
};

/**
 * Create or reuse the connection pool.
 * 
 * In serverless environments:
 * - Pool is created on cold start
 * - Pool is reused during warm invocations
 * - Connection limits should match your serverless concurrency
 */
function createPool(): Pool {
  if (!globalForDb.pool) {
    globalForDb.pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      max: 10, // Adjust based on serverless concurrency limits
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 10000,
    });
  }
  return globalForDb.pool;
}

/**
 * The Drizzle database client instance.
 * This is what gets injected into repositories.
 */
export const db: DbClient = drizzle(createPool(), { schema });
```

---

## 5. Container Integration

The container provides the transaction manager as a shared dependency.

```typescript
// shared/infra/container.ts

import { db } from './db/drizzle';
import { DrizzleTransactionManager } from './db/transaction';
import type { TransactionManager } from '@/shared/kernel/transaction';
import type { DbClient } from './db/types';

export interface Container {
  db: DbClient;
  transactionManager: TransactionManager;
}

let container: Container | null = null;

/**
 * Returns the application container with shared infrastructure.
 * Uses lazy initialization for serverless compatibility.
 */
export function getContainer(): Container {
  if (!container) {
    container = {
      db,
      transactionManager: new DrizzleTransactionManager(db),
    };
  }
  return container;
}

/**
 * Resets the container (useful for testing).
 */
export function resetContainer(): void {
  container = null;
}
```

---

## 6. Usage Patterns

### 6.1 Repository: Receiving Transaction Context

Repositories accept optional `RequestContext` and use the transaction if provided.

```typescript
// modules/user/repositories/user.repository.ts

import { eq } from 'drizzle-orm';
import { users, User, UserInsert } from '@/shared/infra/db/schema';
import type { RequestContext } from '@/shared/kernel/context';
import type { DbClient, DrizzleTransaction } from '@/shared/infra/db/types';

export class UserRepository {
  constructor(private db: DbClient) {}

  /**
   * Gets the appropriate client - transaction if in context, otherwise db.
   */
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
    const result = await client
      .insert(users)
      .values(data)
      .returning();
    
    return result[0];
  }
}
```

### 6.2 Service: Owning Single-Service Transactions

Services create transactions for operations that involve multiple repository calls.

```typescript
// modules/user/services/user.service.ts

import type { TransactionManager } from '@/shared/kernel/transaction';
import type { RequestContext } from '@/shared/kernel/context';
import { ConflictError } from '@/shared/kernel/errors';
import { User, UserInsert } from '@/shared/infra/db/schema';
import type { IUserRepository } from '../repositories/user.repository.interface';

export class UserService {
  constructor(
    private userRepository: IUserRepository,
    private transactionManager: TransactionManager,
  ) {}

  /**
   * Creates a user with uniqueness check.
   * Service owns the transaction because this is a single-service write.
   */
  async create(data: UserInsert): Promise<User> {
    return this.transactionManager.run(async (tx) => {
      // Check uniqueness within transaction (prevents race conditions)
      const existing = await this.userRepository.findByEmail(data.email, { tx });
      if (existing) {
        throw new ConflictError('Email already in use', { email: data.email });
      }

      return this.userRepository.create(data, { tx });
    });
  }

  /**
   * Read operation - no transaction needed.
   */
  async findById(id: string, ctx?: RequestContext): Promise<User | null> {
    return this.userRepository.findById(id, ctx);
  }

  /**
   * For use case orchestration: accepts external transaction context.
   * Note the different method name to distinguish from self-managed transactions.
   */
  async createWithContext(data: UserInsert, ctx: RequestContext): Promise<User> {
    const existing = await this.userRepository.findByEmail(data.email, ctx);
    if (existing) {
      throw new ConflictError('Email already in use', { email: data.email });
    }
    return this.userRepository.create(data, ctx);
  }
}
```

### 6.3 Use Case: Owning Multi-Service Transactions

Use cases create transactions when orchestrating multiple services.

```typescript
// modules/user/use-cases/register-user.use-case.ts

import type { TransactionManager } from '@/shared/kernel/transaction';
import type { IUserService } from '../services/user.service.interface';
import type { IWorkspaceService } from '@/modules/workspace/services/workspace.service.interface';
import type { IEmailService } from '@/shared/infra/email/email.service.interface';
import { RegisterUserDTO } from '../dtos/register-user.dto';
import { UserPublic } from '@/shared/infra/db/schema';
import { hashPassword } from '@/shared/utils/password';
import { generateId } from '@/shared/utils/id';

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
      const user = await this.userService.createWithContext(
        {
          id: generateId(),
          email: input.email,
          name: input.name,
          passwordHash,
        },
        { tx },
      );

      // Add to workspace within same transaction
      if (input.workspaceId) {
        await this.workspaceService.addMemberWithContext(
          input.workspaceId,
          user.id,
          { tx },
        );
      }

      return user;
    });

    // Side effects happen OUTSIDE the transaction
    // If email fails, user is still created (eventual consistency)
    await this.emailService.sendWelcomeEmail(user.email, user.name);

    // Return safe public view
    const { passwordHash: _, ...userPublic } = user;
    return userPublic;
  }
}
```

---

## 7. Transaction Patterns

### 7.1 Read Operations

**No transaction needed** - use direct repository calls.

```typescript
// Service
async findById(id: string): Promise<User | null> {
  return this.userRepository.findById(id);
}

// Router
getById: protectedProcedure
  .input(z.object({ id: z.string() }))
  .query(async ({ input }) => {
    return makeUserService().findById(input.id);
  }),
```

### 7.2 Single-Service Writes

**Service owns the transaction.**

```typescript
// Service
async create(data: UserInsert): Promise<User> {
  return this.transactionManager.run(async (tx) => {
    // All operations in same transaction
    const existing = await this.userRepository.findByEmail(data.email, { tx });
    if (existing) throw new ConflictError('Email exists');
    return this.userRepository.create(data, { tx });
  });
}

// Router - calls service directly
create: protectedProcedure
  .input(CreateUserSchema)
  .mutation(async ({ input }) => {
    return makeUserService().create(input);
  }),
```

### 7.3 Multi-Service Writes

**Use case owns the transaction.**

```typescript
// Use Case
async execute(input: TransferFundsDTO): Promise<void> {
  await this.transactionManager.run(async (tx) => {
    await this.accountService.debitWithContext(input.fromId, input.amount, { tx });
    await this.accountService.creditWithContext(input.toId, input.amount, { tx });
    await this.auditService.logTransferWithContext(input, { tx });
  });
}

// Router - calls use case
transfer: protectedProcedure
  .input(TransferFundsSchema)
  .mutation(async ({ input }) => {
    return makeTransferFundsUseCase().execute(input);
  }),
```

### 7.4 Transaction + Side Effects

**Side effects happen outside the transaction.**

```typescript
async execute(input: RegisterUserDTO): Promise<UserPublic> {
  // Transaction: database operations
  const user = await this.transactionManager.run(async (tx) => {
    const user = await this.userService.createWithContext(userData, { tx });
    await this.workspaceService.addMemberWithContext(wsId, user.id, { tx });
    return user;
  });

  // Side effects: after transaction commits
  await this.emailService.sendWelcomeEmail(user.email, user.name);
  await this.analyticsService.trackRegistration(user.id);

  return user;
}
```

---

## 8. Error Handling in Transactions

### 8.1 Automatic Rollback

Drizzle automatically rolls back on any thrown error.

```typescript
await this.transactionManager.run(async (tx) => {
  await this.userRepository.create(user1, { tx });
  await this.userRepository.create(user2, { tx }); // Throws ConflictError
  // Transaction is rolled back, user1 is NOT created
});
```

### 8.2 Explicit Validation Before Commit

Validate everything before making changes when possible.

```typescript
await this.transactionManager.run(async (tx) => {
  // Validate first
  const fromAccount = await this.accountRepository.findByIdOrThrow(fromId, { tx });
  const toAccount = await this.accountRepository.findByIdOrThrow(toId, { tx });
  
  if (fromAccount.balance < amount) {
    throw new BusinessRuleError('Insufficient funds');
  }

  // Then mutate
  await this.accountRepository.debit(fromId, amount, { tx });
  await this.accountRepository.credit(toId, amount, { tx });
});
```

### 8.3 Handling Partial Failures

For operations that can partially succeed, handle explicitly.

```typescript
async execute(input: BulkCreateDTO): Promise<BulkResult> {
  const results: BulkResult = { success: [], failed: [] };

  // Option 1: All-or-nothing (single transaction)
  await this.transactionManager.run(async (tx) => {
    for (const item of input.items) {
      await this.itemService.createWithContext(item, { tx });
    }
  });

  // Option 2: Best-effort (individual transactions)
  for (const item of input.items) {
    try {
      const created = await this.itemService.create(item);
      results.success.push(created);
    } catch (error) {
      results.failed.push({ item, error: error.message });
    }
  }

  return results;
}
```

---

## 9. Testing Transactions

### 9.1 Mocking TransactionManager

```typescript
// tests/mocks/transaction.mock.ts

import type { TransactionManager, TransactionContext } from '@/shared/kernel/transaction';

/**
 * Mock transaction manager that executes functions without a real transaction.
 * Useful for unit tests where you want to test business logic in isolation.
 */
export class MockTransactionManager implements TransactionManager {
  async run<T>(fn: (tx: TransactionContext) => Promise<T>): Promise<T> {
    // Execute without real transaction - pass empty object as context
    return fn({} as TransactionContext);
  }
}
```

### 9.2 Integration Tests with Real Transactions

```typescript
// tests/integration/user.service.test.ts

import { getContainer, resetContainer } from '@/shared/infra/container';
import { UserService } from '@/modules/user/services/user.service';
import { UserRepository } from '@/modules/user/repositories/user.repository';

describe('UserService', () => {
  let userService: UserService;

  beforeEach(() => {
    resetContainer();
    const container = getContainer();
    const userRepository = new UserRepository(container.db);
    userService = new UserService(userRepository, container.transactionManager);
  });

  afterEach(async () => {
    // Clean up test data
    await getContainer().db.delete(users);
  });

  it('rolls back on conflict', async () => {
    // Create first user
    await userService.create({ email: 'test@example.com', name: 'Test' });

    // Attempt duplicate - should rollback
    await expect(
      userService.create({ email: 'test@example.com', name: 'Test 2' })
    ).rejects.toThrow(ConflictError);

    // Verify only one user exists
    const count = await getContainer().db.select().from(users);
    expect(count).toHaveLength(1);
  });
});
```

---

## 10. Folder Structure

```
src/
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
│     │  └─ user.service.ts      # Owns single-service transactions
│     └─ use-cases/
│        └─ register-user.use-case.ts  # Owns multi-service transactions
```

---

## 11. Checklist

- [ ] `TransactionManager` interface defined in `shared/kernel/transaction.ts`
- [ ] `TransactionContext` type alias in kernel (framework-agnostic)
- [ ] `DrizzleTransactionManager` implementation in `shared/infra/db/transaction.ts`
- [ ] `RequestContext` includes optional `tx` field
- [ ] Repositories accept `ctx?: RequestContext` parameter
- [ ] Repositories use `ctx?.tx ?? this.db` pattern
- [ ] Services receive `TransactionManager` via constructor
- [ ] Services own transactions for single-service writes
- [ ] Services expose `*WithContext` methods for use case orchestration
- [ ] Use cases own transactions for multi-service orchestration
- [ ] Side effects happen outside transactions
- [ ] Container provides `transactionManager` as shared dependency
