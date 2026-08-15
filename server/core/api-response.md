# API Response Structure

> Standard response contract and pagination patterns across tRPC and OpenAPI adapters.

## Principles

- Envelope pattern for all responses
- OpenAPI-aligned structure
- Consistent shape for frontend consumption
- Explicit offset pagination for regular queries and an explicit cursor
  contract when a tRPC capability needs `useInfiniteQuery`
- Contract schemas are defined once (Zod-first) and reused by both transports

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
    offset: number,            // Current numeric offset
    nextOffset: number | null, // Next offset (null = no more pages)
    sort: 'asc' | 'desc'
  }
}
```

This is explicitly offset pagination. Do not call a numeric offset a
`cursor`. When a capability needs stable traversal under concurrent inserts,
define an opaque cursor from a deterministic sort key instead of reusing these
fields.

Use this offset contract with a regular tRPC `useQuery` or REST/OpenAPI query.
tRPC exposes `useInfiniteQuery` only when a procedure input accepts an optional
field named `cursor`; an infinite capability therefore needs a separate,
cursor-based contract and must not pass `nextOffset` as its page parameter.

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
    "offset": 40,
    "nextOffset": 60,
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
    "offset": 0,
    "nextOffset": null,
    "sort": "desc"
  }
}
```

## Error Response

Defined in [Error Handling](./error-handling.md) and typed as `ApiErrorResponse` in `shared/kernel/response.ts`.

`message` must always be public-safe text. Internal diagnostics (SQL/provider errors, stack traces) must never be serialized to clients.

```typescript
{
  code: string,
  message: string,
  requestId: string,
  details?: Record<string, unknown> // explicitly allowlisted public context only
}
```

**Example:**

```json
{
  "code": "USER_NOT_FOUND",
  "message": "User not found",
  "requestId": "req-abc-123"
}

{
  "code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred",
  "requestId": "req-abc-123"
}
```

For OpenAPI-style Next.js route handlers (`app/api/**/route.ts`), return `ApiResponse<T>` for 2xx responses and `ApiErrorResponse` for non-2xx. See [`../runtime/nodejs/metaframeworks/nextjs/route-handlers.md`](../runtime/nodejs/metaframeworks/nextjs/route-handlers.md) for a complete template.

## Pagination Types & Schemas

### Input Schema

```typescript
// shared/kernel/pagination.ts

import { z } from "zod";

/**
 * Standard pagination input schema.
 * Extend with endpoint-specific filters as needed.
 */
export const PaginationInputSchema = z.object({
  limit: z.number().min(1).max(100).default(20),
  offset: z.number().int().min(0).default(0),
  sort: z.enum(["asc", "desc"]).default("desc"),
  search: z.string().nullish(),
});

export type PaginationInput = z.infer<typeof PaginationInputSchema>;
```

### Output Schema

```typescript
// shared/kernel/pagination.ts (continued)

/**
 * Pagination metadata schema.
 */
export const PaginationMetaSchema = z.object({
  total: z.number(),
  limit: z.number(),
  offset: z.number().int().min(0),
  nextOffset: z.number().int().min(0).nullable(),
  sort: z.enum(["asc", "desc"]),
});

export type PaginationMeta = z.infer<typeof PaginationMetaSchema>;

/**
 * Creates a paginated response schema for a given item type.
 */
export function createPaginatedResponseSchema<T extends z.ZodType>(itemSchema: T) {
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
// shared/kernel/response.ts

import { z } from "zod";

export type ApiResponse<T> = {
  data: T;
};

export interface ApiErrorResponse {
  code: string;
  message: string; // Public-safe user-facing message
  requestId: string;
  details?: Record<string, unknown>; // never implicit internal diagnostics
}

/**
 * Creates a single resource response schema.
 */
export function createResponseSchema<T extends z.ZodType>(dataSchema: T) {
  return z.object({
    data: dataSchema,
  });
}
```

## Pagination Helper

```typescript
// shared/utils/pagination.ts

import type {
  PaginationInput,
  PaginationMeta,
  PaginatedResponse,
} from "@/shared/kernel/pagination";

/**
 * Builds an offset-paginated response with computed nextOffset.
 */
export function buildPaginatedResponse<T>(
  data: T[],
  total: number,
  input: PaginationInput,
): PaginatedResponse<T> {
  const limit = input.limit ?? 20;
  const currentOffset = input.offset ?? 0;
  const nextOffset = currentOffset + data.length;
  const followingOffset = nextOffset < total ? nextOffset : null;

  return {
    data,
    meta: {
      total,
      limit,
      offset: currentOffset,
      nextOffset: followingOffset,
      sort: input.sort ?? "desc",
    },
  };
}
```

## Single Resource Response Helper

```typescript
// shared/utils/response.ts

import type { ApiResponse } from "@/shared/kernel/response";

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
// modules/user/shared/contracts/list-users.contract.ts

import { z } from "zod";
import { PaginationInputSchema } from "@/shared/kernel/pagination";

export const ListUsersInputSchema = PaginationInputSchema.extend({
  role: z.enum(["admin", "member"]).optional(),
  status: z.enum(["active", "inactive"]).optional(),
});

export type ListUsersInput = z.infer<typeof ListUsersInputSchema>;
```

## Transport Examples

### tRPC Router Example

```typescript
// modules/user/user.router.ts

import { router, protectedProcedure } from "@/shared/infra/trpc";
import { z } from "zod";
import {
  GetUserResponseSchema,
  ListUsersInputSchema,
  ListUsersResponseSchema,
} from "./shared/contracts";
import {
  makeGetUserController,
  makeListUsersController,
} from "./factories/user.factory";
import { wrapResponse } from "@/shared/utils/response";

export const userRouter = router({
  // Single resource - wrapped in envelope
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input, ctx }) => {
      const result = await makeGetUserController().execute(
        input,
        toActor(ctx.session),
      );
      const response = GetUserResponseSchema.parse(result);
      return wrapResponse(response);
    }),

  // List - returns paginated response
  list: protectedProcedure
    .input(ListUsersInputSchema)
    .query(async ({ input, ctx }) => {
      const page = await makeListUsersController().execute(
        input,
        toActor(ctx.session),
      );
      return {
        ...page,
        data: ListUsersResponseSchema.parse(page.data),
      };
    }),
});
```

Here, `GetUserResponseSchema` validates the single-resource payload and `ListUsersResponseSchema` validates the list payload. The kernel envelope/pagination types supply `{ data }` and `{ data, meta }`.

### Shared Service Example

```typescript
// modules/user/services/user.service.ts

import { users } from "@/shared/infra/db/schema";
import { buildPaginatedResponse } from "@/shared/utils/pagination";
import type { PaginatedResponse } from "@/shared/kernel/pagination";
import type { ListUsersInput } from "../shared/contracts";
import type { User } from "@/shared/infra/db/schema";

export class UserService {
  async list(input: ListUsersInput): Promise<PaginatedResponse<User>> {
    const { limit = 20, offset = 0, sort = "desc", search, role } = input;

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

### tRPC Client Usage with an Offset Query

```typescript
// Client-side (React)

import { trpc } from '@/trpc/client';
import { useState } from 'react';

function UserList() {
  const [offset, setOffset] = useState(0);
  const query = trpc.user.list.useQuery({
    limit: 20,
    offset,
    sort: 'desc',
    search: 'john',
  });

  const users = query.data?.data ?? [];
  const nextOffset = query.data?.meta.nextOffset ?? null;

  return (
    <div>
      {users.map((user) => (
        <UserCard key={user.id} user={user} />
      ))}

      {nextOffset !== null && (
        <button
          onClick={() => setOffset(nextOffset)}
          disabled={query.isFetching}
        >
          {query.isFetching ? 'Loading...' : 'Next page'}
        </button>
      )}
    </div>
  );
}
```

For an infinite list, define a different input such as
`{ limit, cursor?: string }` and return an opaque `nextCursor`. The cursor must
encode the deterministic sort position (for example, `createdAt` plus `id`),
not a numeric offset. Then pass `lastPage.meta.nextCursor` from
`getNextPageParam`.

### OpenAPI Route Handler Example

```typescript
// app/api/profiles/route.ts

import { NextResponse } from "next/server";
import type { ApiResponse, ApiErrorResponse } from "@/shared/kernel/response";
import { wrapResponse } from "@/shared/utils/response";
import { handleError } from "@/shared/infra/http/error-handler";
import { parseRequestInput } from "@/shared/infra/http/validation";
import { withRequestObservability } from "@/shared/infra/observability";

export async function GET(req: Request) {
  return withRequestObservability(req, async ({ requestId }) => {
    try {
      const input = parseRequestInput(
        ListProfilesInputSchema,
        /* parsed query */,
      );
      const actor = await authenticateNextRequest(req);
      const result = await makeListProfilesController().execute(input, actor);
      const response = ListProfilesResponseSchema.parse(result);
      return NextResponse.json<ApiResponse<typeof response>>(
        wrapResponse(response),
      );
    } catch (error) {
      const { status, body } = handleError(error, requestId);
      return NextResponse.json<ApiErrorResponse>(body, { status });
    }
  });
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
│     └─ shared/
│        └─ contracts/
│           └─ list-users.contract.ts  # Shared input + response schemas
```

## Checklist

- [ ] `PaginationInputSchema` in `shared/kernel/pagination.ts`
- [ ] `PaginationMetaSchema` in `shared/kernel/pagination.ts`
- [ ] `createPaginatedResponseSchema` helper for the kernel-owned envelope
- [ ] `createResponseSchema` helper for single resource
- [ ] `buildPaginatedResponse` utility in `shared/utils/pagination.ts`
- [ ] `wrapResponse` utility in `shared/utils/response.ts`
- [ ] Endpoint input contracts extend `PaginationInputSchema` with custom filters
- [ ] Endpoint response contracts compose the shared pagination/response schemas
- [ ] Services implement search on relevant fields
- [ ] Routers return consistent envelope structure

## External Route Contract Hardening (Required)

For externally consumed HTTP endpoints (for example mobile/public APIs), route adapters MUST keep success contracts explicit at compile time.

- Do not use `ApiResponse<unknown>` or `ApiResponse<any>`.
- Do not hide payload types inside wrappers such as `{ data: { method: unknown } }`.
- Prefer response types inferred from the shared capability contract:

```typescript
type GetThingResponse = z.infer<typeof GetThingResponseSchema>;
const response = GetThingResponseSchema.parse(result);
return NextResponse.json<ApiResponse<GetThingResponse>>(wrapResponse(response));
```

- Migration fallback (temporary): `ApiResponse<typeof result>` is acceptable while a shared response schema is being introduced.
- Keep framework adapters thin: derive wire types from shared contracts and call a controller factory, never a service/use-case factory.

Recommended CI gates:

```bash
rg -n "ApiResponse<unknown>|ApiResponse<any>" src/app/api --glob '**/route.ts'
rg -n "ApiResponse<\\{[^\\n}]*unknown" src/app/api --glob '**/route.ts'
```
