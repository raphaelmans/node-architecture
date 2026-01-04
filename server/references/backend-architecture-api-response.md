# API Response Structure

> **Purpose**: This document defines the standard HTTP response structure, pagination patterns, and tRPC integration.

---

## 1. Overview

**Principles:**

- Envelope pattern for all responses
- OpenAPI-aligned structure
- Consistent shape for frontend consumption
- Pagination compatible with tRPC `useInfiniteQuery`

---

## 2. Success Response - Single Resource

```typescript
{
  data: T
}
```

**Example:**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john@example.com",
    "name": "John Doe",
    "role": "member",
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

**Not found:** Throw `NotFoundError` (do not return `{ data: null }`)

---

## 3. Success Response - List/Collection

```typescript
{
  data: T[],
  meta: {
    total: number,            // Total count in database
    limit: number,            // Requested limit
    cursor: number | null,    // Current offset (null for first page)
    nextCursor: number | null, // Next offset (null = no more pages)
    sort: 'asc' | 'desc'
  }
}
```

**Example:**

```json
{
  "data": [
    { "id": "...", "name": "John Doe", "email": "john@example.com" },
    { "id": "...", "name": "Jane Doe", "email": "jane@example.com" }
  ],
  "meta": {
    "total": 150,
    "limit": 20,
    "cursor": 40,
    "nextCursor": 60,
    "sort": "desc"
  }
}
```

**Empty results:**

```json
{
  "data": [],
  "meta": {
    "total": 0,
    "limit": 20,
    "cursor": null,
    "nextCursor": null,
    "sort": "desc"
  }
}
```

---

## 4. Error Response

Defined in [Error Handling Architecture](./backend-architecture-error-handling.md).

```typescript
{
  code: string,
  message: string,
  requestId: string,
  details?: Record<string, unknown>
}
```

**Example:**

```json
{
  "code": "USER_NOT_FOUND",
  "message": "User not found",
  "requestId": "req-abc-123",
  "details": {
    "userId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## 5. Pagination Types & Schemas

### 5.1 Input Schema

```typescript
// shared/kernel/pagination.ts

import { z } from 'zod';

/**
 * Standard pagination input schema.
 * Extend with endpoint-specific filters as needed.
 */
export const PaginationInputSchema = z.object({
  limit: z.number().min(1).max(100).default(20),
  cursor: z.number().nullish(),
  sort: z.enum(['asc', 'desc']).default('desc'),
  search: z.string().nullish(),
});

export type PaginationInput = z.infer<typeof PaginationInputSchema>;
```

### 5.2 Output Schema

```typescript
// shared/kernel/pagination.ts (continued)

/**
 * Pagination metadata schema.
 */
export const PaginationMetaSchema = z.object({
  total: z.number(),
  limit: z.number(),
  cursor: z.number().nullable(),
  nextCursor: z.number().nullable(),
  sort: z.enum(['asc', 'desc']),
});

export type PaginationMeta = z.infer<typeof PaginationMetaSchema>;

/**
 * Creates a paginated response schema for a given item type.
 */
export function createPaginatedSchema<T extends z.ZodType>(itemSchema: T) {
  return z.object({
    data: z.array(itemSchema),
    meta: PaginationMetaSchema,
  });
}

export type PaginatedResponse<T> = {
  data: T[];
  meta: PaginationMeta;
};
```

### 5.3 Single Resource Response Schema

```typescript
// shared/kernel/response.ts

import { z } from 'zod';

/**
 * Creates a single resource response schema.
 */
export function createResponseSchema<T extends z.ZodType>(dataSchema: T) {
  return z.object({
    data: dataSchema,
  });
}

export type ApiResponse<T> = {
  data: T;
};
```

---

## 6. Pagination Helper

```typescript
// shared/utils/pagination.ts

import type { PaginationInput, PaginationMeta, PaginatedResponse } from '@/shared/kernel/pagination';

/**
 * Builds a paginated response with computed nextCursor.
 *
 * @param data - Array of items for current page
 * @param total - Total count of items in database
 * @param input - Pagination input from request
 * @returns Paginated response with data and meta
 *
 * @example
 * const users = await db.select().from(users).limit(input.limit).offset(input.cursor ?? 0);
 * const total = await db.select({ count: count() }).from(users);
 * return buildPaginatedResponse(users, total, input);
 */
export function buildPaginatedResponse<T>(
  data: T[],
  total: number,
  input: PaginationInput,
): PaginatedResponse<T> {
  const limit = input.limit ?? 20;
  const cursor = input.cursor ?? null;
  const currentOffset = cursor ?? 0;
  const nextOffset = currentOffset + data.length;
  const nextCursor = nextOffset < total ? nextOffset : null;

  return {
    data,
    meta: {
      total,
      limit,
      cursor,
      nextCursor,
      sort: input.sort ?? 'desc',
    },
  };
}
```

---

## 7. Single Resource Response Helper

```typescript
// shared/utils/response.ts

import type { ApiResponse } from '@/shared/kernel/response';

/**
 * Wraps data in standard envelope.
 *
 * @example
 * return wrapResponse(user);
 * // { data: { id: '...', name: '...' } }
 */
export function wrapResponse<T>(data: T): ApiResponse<T> {
  return { data };
}
```

---

## 8. Endpoint-Specific Filters

Extend `PaginationInputSchema` for endpoint-specific filters:

```typescript
// modules/user/dtos/list-users.dto.ts

import { z } from 'zod';
import { PaginationInputSchema } from '@/shared/kernel/pagination';

export const ListUsersInputSchema = PaginationInputSchema.extend({
  role: z.enum(['admin', 'member']).optional(),
  status: z.enum(['active', 'inactive']).optional(),
});

export type ListUsersInput = z.infer<typeof ListUsersInputSchema>;
```

---

## 9. tRPC Integration

### 9.1 Router Example

```typescript
// modules/user/user.router.ts

import { router, protectedProcedure } from '@/shared/infra/trpc';
import { z } from 'zod';
import { ListUsersInputSchema } from './dtos/list-users.dto';
import { makeUserService } from './factories/user.factory';
import { wrapResponse } from '@/shared/utils/response';

export const userRouter = router({
  // Single resource - wrapped in envelope
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input }) => {
      const user = await makeUserService().findByIdOrThrow(input.id);
      return wrapResponse(user);
    }),

  // List - returns paginated response
  list: protectedProcedure
    .input(ListUsersInputSchema)
    .query(async ({ input }) => {
      return makeUserService().list(input);
    }),
});
```

### 9.2 Service Example

```typescript
// modules/user/services/user.service.ts

import { eq, ilike, or, count, desc, asc } from 'drizzle-orm';
import { users } from '@/shared/infra/db/schema';
import { buildPaginatedResponse } from '@/shared/utils/pagination';
import type { PaginatedResponse } from '@/shared/kernel/pagination';
import type { ListUsersInput } from '../dtos/list-users.dto';
import type { User } from '@/shared/infra/db/schema';

export class UserService {
  // ...

  async list(input: ListUsersInput): Promise<PaginatedResponse<User>> {
    const { limit = 20, cursor, sort = 'desc', search, role } = input;
    const offset = cursor ?? 0;

    // Build where conditions
    const conditions = [];

    if (search) {
      conditions.push(
        or(
          ilike(users.name, `%${search}%`),
          ilike(users.email, `%${search}%`),
        ),
      );
    }

    if (role) {
      conditions.push(eq(users.role, role));
    }

    // Query with pagination
    const data = await this.db
      .select()
      .from(users)
      .where(conditions.length > 0 ? and(...conditions) : undefined)
      .orderBy(sort === 'desc' ? desc(users.createdAt) : asc(users.createdAt))
      .limit(limit)
      .offset(offset);

    // Get total count
    const [{ total }] = await this.db
      .select({ total: count() })
      .from(users)
      .where(conditions.length > 0 ? and(...conditions) : undefined);

    return buildPaginatedResponse(data, total, input);
  }
}
```

### 9.3 Client Usage with `useInfiniteQuery`

```typescript
// Client-side (React)

import { trpc } from '@/trpc/client';

function UserList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = trpc.user.list.useInfiniteQuery(
    {
      limit: 20,
      sort: 'desc',
      search: 'john',
    },
    {
      getNextPageParam: (lastPage) => lastPage.meta.nextCursor,
    },
  );

  // Flatten pages
  const users = data?.pages.flatMap((page) => page.data) ?? [];

  return (
    <div>
      {users.map((user) => (
        <UserCard key={user.id} user={user} />
      ))}

      {hasNextPage && (
        <button
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
        >
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

---

## 10. Search Implementation

Services decide which fields to search. The `search` parameter is a generic term.

```typescript
// UserService searches: name, email
if (search) {
  conditions.push(
    or(
      ilike(users.name, `%${search}%`),
      ilike(users.email, `%${search}%`),
    ),
  );
}

// WorkspaceService searches: name, description
if (search) {
  conditions.push(
    or(
      ilike(workspaces.name, `%${search}%`),
      ilike(workspaces.description, `%${search}%`),
    ),
  );
}
```

---

## 11. Folder Structure

```
src/
├─ shared/
│  ├─ kernel/
│  │  ├─ pagination.ts    # PaginationInput, PaginationMeta, schemas
│  │  └─ response.ts      # ApiResponse type, createResponseSchema
│  └─ utils/
│     ├─ pagination.ts    # buildPaginatedResponse helper
│     └─ response.ts      # wrapResponse helper
│
├─ modules/
│  └─ user/
│     └─ dtos/
│        └─ list-users.dto.ts  # Extends PaginationInputSchema
```

---

## 12. Checklist

- [ ] `PaginationInputSchema` in `shared/kernel/pagination.ts`
- [ ] `PaginationMetaSchema` in `shared/kernel/pagination.ts`
- [ ] `createPaginatedSchema` helper for output validation
- [ ] `createResponseSchema` helper for single resource
- [ ] `buildPaginatedResponse` utility in `shared/utils/pagination.ts`
- [ ] `wrapResponse` utility in `shared/utils/response.ts`
- [ ] Endpoint DTOs extend `PaginationInputSchema` with custom filters
- [ ] Services implement search on relevant fields
- [ ] Routers return consistent envelope structure
