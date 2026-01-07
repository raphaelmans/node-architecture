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

export class UserRepository {
  async create(
    data: Omit<UserInsert, "id">,
    ctx?: RequestContext,
  ): Promise<User> {
    const client = ctx?.tx ?? this.db;

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
// modules/user/dtos/get-user.dto.ts

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

## Collision Retry Wrapper

UUID collisions are astronomically unlikely, but for absolute safety:

```typescript
// shared/utils/db.ts

import { ConflictError } from "@/shared/kernel/errors";

/**
 * Executes a database operation with retry on primary key collision.
 * Use for inserts where database generates the UUID.
 */
export async function withRetryOnCollision<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (isPrimaryKeyViolation(error) && attempt < maxRetries - 1) {
        continue; // Retry - database will generate new UUID
      }
      throw error;
    }
  }

  throw new ConflictError("Failed to insert after retries", {
    attempts: maxRetries,
  });
}

/**
 * Checks if error is a primary key violation.
 */
function isPrimaryKeyViolation(error: unknown): boolean {
  if (error && typeof error === "object" && "code" in error) {
    // PostgreSQL unique violation on primary key
    return error.code === "23505";
  }
  return false;
}
```

**Usage in repository:**

```typescript
// modules/user/repositories/user.repository.ts

import { withRetryOnCollision } from "@/shared/utils/db";

export class UserRepository {
  async create(data: UserInsert, ctx?: RequestContext): Promise<User> {
    const client = ctx?.tx ?? this.db;

    return withRetryOnCollision(async () => {
      const result = await client.insert(users).values(data).returning();

      return result[0];
    });
  }
}
```

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
// Example: Need ID before insert
const userId = generateId();
await Promise.all([
  userRepository.createWithId(userId, userData),
  auditService.log("user.created", { userId }), // Need ID immediately
]);
```

## Checklist

- [ ] All tables use `uuid('id').primaryKey().defaultRandom()`
- [ ] Insert types omit `id` field
- [ ] DTOs validate IDs with `z.string().uuid()`
- [ ] `withRetryOnCollision()` utility in `shared/utils/db.ts`
- [ ] `generateId()` utility available for edge cases
