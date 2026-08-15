# ID Generation

> ID generation strategy using database-generated UUIDs.

## Overview

**Decision:** Use **PostgreSQL `gen_random_uuid()`** as the default for all entity IDs.

**Why database-generated UUIDs:**

- No application code needed
- Guaranteed uniqueness at database level
- Native `uuid` type with optimized storage
- Works automatically on insert

## Database Schema

Use Drizzle's `uuid` type with `defaultRandom()`:

```typescript
// shared/infra/db/schema.ts

import { pgTable, uuid, text, timestamp } from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: uuid("id").primaryKey().defaultRandom(),
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  passwordHash: text("password_hash").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});
```

This generates the SQL:

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ...
);
```

## Repository Pattern

Since the database generates IDs, repositories don't need to provide them:

```typescript
// modules/user/repositories/user.repository.ts

import type { TransactionOptions } from "@/shared/kernel/transaction";
import type { DbClient, DrizzleTransaction } from "@/shared/infra/db/types";

export class UserRepository {
  constructor(private readonly db: DbClient) {}

  private getClient(options?: TransactionOptions): DbClient | DrizzleTransaction {
    return (options?.tx as unknown as DrizzleTransaction) ?? this.db;
  }

  async create(
    data: Omit<UserInsert, "id">,
    options?: TransactionOptions,
  ): Promise<User> {
    const client = this.getClient(options);

    const result = await client
      .insert(users)
      .values(data) // No id needed - database generates it
      .returning();

    return result[0];
  }
}
```

## Entity Types

Update entity types to reflect optional ID on insert:

```typescript
// shared/infra/db/schema.ts

import { createSelectSchema, createInsertSchema } from "drizzle-zod";

// Select schema - id is always present
export const UserSchema = createSelectSchema(users);
export type User = z.infer<typeof UserSchema>;

// Insert schema - id is optional (database provides default)
export const UserInsertSchema = createInsertSchema(users).omit({ id: true });
export type UserInsert = z.infer<typeof UserInsertSchema>;
```

## Input Validation

For endpoints that receive IDs as input:

```typescript
// modules/user/shared/contracts/user.contract.ts

import { z } from "zod";

export const GetUserSchema = z.object({
  id: z.string().uuid(),
});

export const UpdateUserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100).optional(),
  email: z.string().email().optional(),
});
```

## Collision Policy

Do not add a generic retry wrapper for PostgreSQL error `23505`. That code means
**any** unique-constraint violation, not specifically a UUID primary-key
collision. Retrying it can hide a real email/slug conflict, and a retry inside
an already-aborted transaction cannot succeed.

Database-generated UUID collisions are sufficiently improbable that the
canonical behavior is:

1. perform the insert once;
2. inspect the exact constraint for known business uniqueness conflicts;
3. translate those conflicts to the corresponding domain error;
4. let an unexpected primary-key collision surface as an internal failure.

Constraint translation belongs in the repository and must compare an explicit
allowlisted constraint name, as described in
[Error Handling](./error-handling.md#database-error-translation). Never infer
"primary-key collision" from `23505` alone.

## Application-Side Generation (When Needed)

For cases where you need the ID before insert (rare):

```typescript
// shared/utils/id.ts

import { randomUUID } from "crypto";

/**
 * Generates a UUID v4.
 * Use only when you need the ID before database insert.
 */
export function generateId(): string {
  return randomUUID();
}
```

**When you might need this:**

- Creating related records where child needs parent ID before parent is inserted
- Generating IDs for external systems before persisting
- Idempotency keys

```typescript
// Example: use case needs the ID for two transactional records
const userId = generateId();
await transactionManager.run(async (tx) => {
  await userService.createWithId(userId, userData, { tx });
  await auditRecordWriter.append({ action: "user.created", userId }, { tx });
});
```

## Checklist

- [ ] All tables use `uuid('id').primaryKey().defaultRandom()`
- [ ] Insert types omit `id` field
- [ ] Shared API contracts validate IDs with `z.string().uuid()`
- [ ] Known unique constraints are translated by exact constraint name
- [ ] No generic retry is performed for PostgreSQL `23505`
- [ ] `generateId()` utility available for edge cases
