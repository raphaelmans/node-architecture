# API Response Structure

> Standard HTTP response structure, pagination patterns, and tRPC integration.

## Principles

- Envelope pattern for all responses
- OpenAPI-aligned structure
- Consistent shape for frontend consumption
- Pagination compatible with tRPC `useInfiniteQuery`

## Success Response - Single Resource

```typescript
{
  data: T;
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

## Success Response - List/Collection

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

## Error Response

Defined in [Error Handling](./error-handling.md).

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

## Pagination Types & Schemas

### Input Schema

```typescript
// lib/shared/kernel/pagination.ts

import { z } from "zod";

/**
 * Standard pagination input schema.
 * Extend with endpoint-specific filters as needed.
 */
export const PaginationInputSchema = z.object({
  limit: z.number().min(1).max(100).default(20),
  cursor: z.number().nullish(),
  sort: z.enum(["asc", "desc"]).default("desc"),
  search: z.string().nullish(),
});

export type PaginationInput = z.infer<typeof PaginationInputSchema>;
```

### Output Schema

```typescript
// lib/shared/kernel/pagination.ts (continued)

/**
 * Pagination metadata schema.
 */
export const PaginationMetaSchema = z.object({
  total: z.number(),
  limit: z.number(),
  cursor: z.number().nullable(),
  nextCursor: z.number().nullable(),
  sort: z.enum(["asc", "desc"]),
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

### Single Resource Response Schema

```typescript
// lib/shared/kernel/response.ts

import { z } from "zod";

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

## Pagination Helper

```typescript
// lib/shared/utils/pagination.ts

import type {
  PaginationInput,
  PaginationMeta,
  PaginatedResponse,
} from "@/lib/shared/kernel/pagination";

/**
 * Builds a paginated response with computed nextCursor.
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
      sort: input.sort ?? "desc",
    },
  };
}
```

## Single Resource Response Helper

```typescript
// lib/shared/utils/response.ts

import type { ApiResponse } from "@/lib/shared/kernel/response";

/**
 * Wraps data in standard envelope.
 */
export function wrapResponse<T>(data: T): ApiResponse<T> {
  return { data };
}
```

## Endpoint-Specific Filters

Extend `PaginationInputSchema` for endpoint-specific filters:

```typescript
// lib/modules/user/dtos/list-users.dto.ts

import { z } from "zod";
import { PaginationInputSchema } from "@/lib/shared/kernel/pagination";

export const ListUsersInputSchema = PaginationInputSchema.extend({
  role: z.enum(["admin", "member"]).optional(),
  status: z.enum(["active", "inactive"]).optional(),
});

export type ListUsersInput = z.infer<typeof ListUsersInputSchema>;
```

## tRPC Integration

### Router Example

```typescript
// lib/modules/user/user.router.ts

import { router, protectedProcedure } from "@/lib/shared/infra/trpc";
import { z } from "zod";
import { ListUsersInputSchema } from "./dtos/list-users.dto";
import { makeUserService } from "./factories/user.factory";
import { wrapResponse } from "@/lib/shared/utils/response";
import { UserNotFoundError } from "./errors/user.errors";

export const userRouter = router({
  // Single resource - wrapped in envelope
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input }) => {
      const user = await makeUserService().findById(input.id);
      if (!user) {
        throw new UserNotFoundError(input.id);
      }
      return wrapResponse(omitSensitive(user));
    }),

  // List - returns paginated response
  list: protectedProcedure
    .input(ListUsersInputSchema)
    .query(async ({ input }) => {
      return makeUserService().list(input);
    }),
});
```

### Service Example

```typescript
// lib/modules/user/services/user.service.ts

import { users } from "@/lib/shared/infra/db/schema";
import { buildPaginatedResponse } from "@/lib/shared/utils/pagination";
import type { PaginatedResponse } from "@/lib/shared/kernel/pagination";
import type { ListUsersInput } from "../dtos/list-users.dto";
import type { User } from "@/lib/shared/infra/db/schema";

export class UserService {
  async list(input: ListUsersInput): Promise<PaginatedResponse<User>> {
    const { limit = 20, cursor, sort = "desc", search, role } = input;
    const offset = cursor ?? 0;

    // Build where conditions
    const conditions = [];

    if (search) {
      conditions.push(
        or(ilike(users.name, `%${search}%`), ilike(users.email, `%${search}%`)),
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
      .orderBy(sort === "desc" ? desc(users.createdAt) : asc(users.createdAt))
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

### Client Usage with `useInfiniteQuery`

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

## Search Implementation

Services decide which fields to search. The `search` parameter is a generic term.

```typescript
// UserService searches: name, email
if (search) {
  conditions.push(
    or(ilike(users.name, `%${search}%`), ilike(users.email, `%${search}%`)),
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

## Folder Structure

```
src/lib/
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

## Checklist

- [ ] `PaginationInputSchema` in `lib/shared/kernel/pagination.ts`
- [ ] `PaginationMetaSchema` in `lib/shared/kernel/pagination.ts`
- [ ] `createPaginatedSchema` helper for output validation
- [ ] `createResponseSchema` helper for single resource
- [ ] `buildPaginatedResponse` utility in `lib/shared/utils/pagination.ts`
- [ ] `wrapResponse` utility in `lib/shared/utils/response.ts`
- [ ] Endpoint DTOs extend `PaginationInputSchema` with custom filters
- [ ] Services implement search on relevant fields
- [ ] Routers return consistent envelope structure
