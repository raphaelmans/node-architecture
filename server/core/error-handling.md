# Error Handling

> Error handling conventions, custom error classes, and error flow across layers.

## Principles

- Errors are explicit and typed
- HTTP status codes follow REST semantics
- Client receives structured, safe responses
- Internal details are logged, never exposed
- Domain-specific errors for clear API contracts

## Public Error Message Policy

Use a hybrid policy so clients get actionable messages for expected failures, while internal details stay private:

- 5xx errors **MUST** return `GENERIC_PUBLIC_ERROR_MESSAGE` — never the original message
- 4xx errors **MAY** return the domain error message (e.g., "User not found")
- `details` **MUST** be stripped from 5xx responses (no stack traces, SQL, constraint names)
- Never serialize raw SQL/provider/stack messages in response bodies
- Always log full error context server-side with `requestId`

### `public-error.ts` — Kernel Utility

Both the HTTP error handler and the tRPC error formatter share the same public-message policy via `shared/kernel/public-error.ts`. This file is a **required** kernel utility — do not inline the logic in individual handlers.

```typescript
// shared/kernel/public-error.ts

import { AppError } from "./errors";

export const GENERIC_PUBLIC_ERROR_MESSAGE = "An unexpected error occurred";

const INTERNAL_CODES = new Set([
  "INTERNAL_ERROR",
  "BAD_GATEWAY",
  "SERVICE_UNAVAILABLE",
  "GATEWAY_TIMEOUT",
]);

export function isInternalAppError(error: AppError): boolean {
  return error.httpStatus >= 500 || INTERNAL_CODES.has(error.code);
}

export function getPublicErrorMessage(error: AppError): string {
  if (isInternalAppError(error)) {
    return GENERIC_PUBLIC_ERROR_MESSAGE;
  }
  return error.message;
}

export function canExposeErrorDetails(error: AppError): boolean {
  return !isInternalAppError(error);
}
```

## Base Error Class

```typescript
// shared/kernel/errors.ts

export abstract class AppError extends Error {
  abstract readonly code: string;
  abstract readonly httpStatus: number;
  readonly details?: Record<string, unknown>;

  constructor(message: string, details?: Record<string, unknown>) {
    super(message);
    this.name = this.constructor.name;
    this.details = details;
    Error.captureStackTrace(this, this.constructor);
  }
}
```

## Core Error Classes

```typescript
// shared/kernel/errors.ts

// 400 - Bad Request
export class ValidationError extends AppError {
  readonly code = "VALIDATION_ERROR";
  readonly httpStatus = 400;
}

// 401 - Unauthorized
export class AuthenticationError extends AppError {
  readonly code = "AUTHENTICATION_ERROR";
  readonly httpStatus = 401;
}

// 403 - Forbidden
export class AuthorizationError extends AppError {
  readonly code = "AUTHORIZATION_ERROR";
  readonly httpStatus = 403;
}

// 404 - Not Found
export class NotFoundError extends AppError {
  readonly code = "NOT_FOUND";
  readonly httpStatus = 404;
}

// 409 - Conflict
export class ConflictError extends AppError {
  readonly code = "CONFLICT";
  readonly httpStatus = 409;
}

// 422 - Unprocessable Entity (business rule violations)
export class BusinessRuleError extends AppError {
  readonly code = "BUSINESS_RULE_VIOLATION";
  readonly httpStatus = 422;
}

// 429 - Too Many Requests
export class RateLimitError extends AppError {
  readonly code = "RATE_LIMIT_EXCEEDED";
  readonly httpStatus = 429;
}

// 500 - Internal Server Error
export class InternalError extends AppError {
  readonly code = "INTERNAL_ERROR";
  readonly httpStatus = 500;
}

// 502 - Bad Gateway
export class BadGatewayError extends AppError {
  readonly code = "BAD_GATEWAY";
  readonly httpStatus = 502;
}

// 503 - Service Unavailable
export class ServiceUnavailableError extends AppError {
  readonly code = "SERVICE_UNAVAILABLE";
  readonly httpStatus = 503;
}

// 504 - Gateway Timeout
export class GatewayTimeoutError extends AppError {
  readonly code = "GATEWAY_TIMEOUT";
  readonly httpStatus = 504;
}
```

## Domain-Specific Errors

Each module defines its own error subclasses for specific error codes.

```typescript
// modules/user/errors/user.errors.ts

import {
  NotFoundError,
  ConflictError,
  BusinessRuleError,
} from "@/shared/kernel/errors";

export class UserNotFoundError extends NotFoundError {
  readonly code = "USER_NOT_FOUND";

  constructor(userId: string) {
    super("User not found", { userId });
  }
}

export class UserEmailConflictError extends ConflictError {
  readonly code = "USER_EMAIL_CONFLICT";

  constructor(email: string) {
    super("Email already in use", { email });
  }
}

export class UserCannotDeleteSelfError extends BusinessRuleError {
  readonly code = "USER_CANNOT_DELETE_SELF";

  constructor(userId: string) {
    super("Cannot delete your own account", { userId });
  }
}
```

```typescript
// modules/workspace/errors/workspace.errors.ts

import {
  NotFoundError,
  AuthorizationError,
  BusinessRuleError,
} from "@/shared/kernel/errors";

export class WorkspaceNotFoundError extends NotFoundError {
  readonly code = "WORKSPACE_NOT_FOUND";

  constructor(workspaceId: string) {
    super("Workspace not found", { workspaceId });
  }
}

export class WorkspaceAccessDeniedError extends AuthorizationError {
  readonly code = "WORKSPACE_ACCESS_DENIED";

  constructor(workspaceId: string, userId: string) {
    super("Access to workspace denied", { workspaceId, userId });
  }
}

export class WorkspaceHasActiveProjectsError extends BusinessRuleError {
  readonly code = "WORKSPACE_HAS_ACTIVE_PROJECTS";

  constructor(workspaceId: string, projectCount: number) {
    super("Cannot delete workspace with active projects", {
      workspaceId,
      projectCount,
    });
  }
}
```

### Folder Structure

```
lib/modules/
├─ user/
│  ├─ errors/
│  │  └─ user.errors.ts
│  └─ ...
├─ workspace/
│  ├─ errors/
│  │  └─ workspace.errors.ts
│  └─ ...
```

## Validation Error Handling

Use a generic handler that transforms Zod errors into `ValidationError`:

```typescript
// shared/utils/validation.ts

import { ZodError, ZodSchema } from "zod";
import { ValidationError } from "@/shared/kernel/errors";

export function validate<T>(schema: ZodSchema<T>, data: unknown): T {
  const result = schema.safeParse(data);

  if (!result.success) {
    throw new ValidationError("Validation failed", {
      issues: result.error.issues.map((issue) => ({
        path: issue.path.join("."),
        message: issue.message,
      })),
    });
  }

  return result.data;
}
```

**Usage:**

```typescript
import { validate } from "@/shared/utils/validation";
import { CreateUserSchema } from "./dtos/create-user.dto";

const input = validate(CreateUserSchema, req.body);
```

## Error Response Structure

### Client Response

The standardized HTTP error response type is `ApiErrorResponse` (defined in `shared/kernel/response.ts`):

```typescript
// shared/kernel/response.ts
export interface ApiErrorResponse {
  code: string; // Error code (e.g., "USER_NOT_FOUND")
  message: string; // Public-safe user-facing message
  requestId: string; // For support/debugging
  details?: Record<string, unknown>; // Optional additional context
}
```

**Example responses:**

```json
// 404 - Not Found
{
  "code": "USER_NOT_FOUND",
  "message": "User not found",
  "requestId": "req-abc-123",
  "details": {
    "userId": "usr-456"
  }
}

// 400 - Validation Error
{
  "code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "requestId": "req-abc-123",
  "details": {
    "issues": [
      { "path": "email", "message": "Invalid email" },
      { "path": "name", "message": "Required" }
    ]
  }
}

// 500 - Internal Error (generic, safe)
{
  "code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred",
  "requestId": "req-abc-123"
}
```

## Error Handler (Generic HTTP)

For Next.js `route.ts` handlers (non-tRPC), use this helper and return its `{ status, body }` as an `ApiErrorResponse`. See [`../runtime/nodejs/metaframeworks/nextjs/route-handlers.md`](../runtime/nodejs/metaframeworks/nextjs/route-handlers.md) for a complete `app/api/**/route.ts` example.

```typescript
// shared/infra/http/error-handler.ts

import { AppError } from "@/shared/kernel/errors";
import {
  getPublicErrorMessage,
  canExposeErrorDetails,
  GENERIC_PUBLIC_ERROR_MESSAGE,
} from "@/shared/kernel/public-error";
import { logger } from "@/shared/infra/logger";
import type { ApiErrorResponse } from "@/shared/kernel/response";

export function handleError(
  error: unknown,
  requestId: string,
): { status: number; body: ApiErrorResponse } {
  // Known application error
  if (error instanceof AppError) {
    logger.warn(
      {
        err: error,
        code: error.code,
        details: error.details,
        requestId,
      },
      error.message,
    );

    return {
      status: error.httpStatus,
      body: {
        code: error.code,
        message: getPublicErrorMessage(error),
        requestId,
        ...(canExposeErrorDetails(error) &&
          error.details && { details: error.details }),
      },
    };
  }

  // Unknown error - log full details, return generic response
  logger.error(
    {
      err: error,
      requestId,
    },
    "Unexpected error",
  );

  return {
    status: 500,
    body: {
      code: "INTERNAL_ERROR",
      message: GENERIC_PUBLIC_ERROR_MESSAGE,
      requestId,
    },
  };
}
```

## tRPC Error Formatter

For tRPC integration, see [tRPC Integration](../runtime/nodejs/libraries/trpc/integration.md).

The formatter has two critical security responsibilities:

1. **Override `shape.message`** with `getPublicErrorMessage()` — the raw message may contain SQL, stack traces, or constraint names
2. **Strip `shape.data`** with `pickPublicTrpcShapeData()` — tRPC's default shape data includes `stack` in development and other internal fields

```typescript
// shared/infra/trpc/trpc.ts

import { initTRPC } from "@trpc/server";
import { AppError } from "@/shared/kernel/errors";
import {
  getPublicErrorMessage,
  canExposeErrorDetails,
  GENERIC_PUBLIC_ERROR_MESSAGE,
} from "@/shared/kernel/public-error";
import { logger } from "@/shared/infra/logger";
import type { Context } from "./context";

/**
 * Keep only `path` and `zodError` from tRPC shape data.
 * Strips `stack`, `code`, `httpStatus`, and any other internal fields.
 */
function pickPublicTrpcShapeData(
  shapeData: Record<string, unknown>,
): Record<string, unknown> {
  const picked: Record<string, unknown> = {};
  if ("path" in shapeData) picked.path = shapeData.path;
  if ("zodError" in shapeData) picked.zodError = shapeData.zodError;
  return picked;
}

const t = initTRPC.context<Context>().create({
  errorFormatter({ error, shape, ctx }) {
    const cause = error.cause;
    const requestId = ctx?.requestId ?? "unknown";

    // Known application error
    if (cause instanceof AppError) {
      logger.warn(
        {
          err: cause,
          code: cause.code,
          details: cause.details,
          requestId,
        },
        cause.message,
      );

      return {
        ...shape,
        message: getPublicErrorMessage(cause),
        data: {
          ...pickPublicTrpcShapeData(shape.data),
          appCode: cause.code,
          requestId,
          ...(canExposeErrorDetails(cause) &&
            cause.details && { details: cause.details }),
        },
      };
    }

    // Unknown error — never expose internals
    logger.error({ err: error, requestId }, "Unexpected error");

    return {
      ...shape,
      message: GENERIC_PUBLIC_ERROR_MESSAGE,
      data: {
        ...pickPublicTrpcShapeData(shape.data),
        appCode: "INTERNAL_ERROR",
        requestId,
      },
    };
  },
});
```

The transport-level tRPC code remains on the error envelope itself (`error.code`). Do not mirror transport `code` or `httpStatus` into `shape.data`. Put application-specific error codes in `shape.data.appCode`.

## Error Flow by Layer

| Layer             | Throws                                                   | Catches                                                |
| ----------------- | -------------------------------------------------------- | ------------------------------------------------------ |
| Repository        | Domain errors (from caught DB constraints)               | Known Postgres constraint violations (e.g., `23505`)   |
| Service           | Domain-specific errors, `BusinessRuleError`              | Nothing (let bubble)                                   |
| Use Case          | Domain-specific errors                                   | Nothing (let bubble)                                   |
| Router/Controller | `NotFoundError` for null results                         | Optional module-specific mapping; otherwise let bubble |

**Example flow:**

```typescript
// Repository - returns null, doesn't throw
async findById(id: string, ctx?: RequestContext): Promise<User | null> {
  const client = this.getClient(ctx);
  const result = await client
    .select()
    .from(users)
    .where(eq(users.id, id))
    .limit(1);

  return result[0] ?? null;
}

// Service - business logic errors
async delete(id: string, ctx?: RequestContext): Promise<void> {
  const exec = async (ctx: RequestContext) => {
    const user = await this.userRepository.findById(id, ctx);
    if (!user) {
      throw new UserNotFoundError(id);
    }

    if (user.role === 'owner') {
      throw new UserCannotDeleteOwnerError(id);
    }

    await this.userRepository.delete(id, ctx);
  };

  if (ctx?.tx) {
    return exec(ctx);
  }
  return this.transactionManager.run((tx) => exec({ tx }));
}

// Router - handles null from findById
getById: protectedProcedure
  .input(z.object({ id: z.string() }))
  .query(async ({ input }) => {
    const user = await makeUserService().findById(input.id);
    if (!user) {
      throw new UserNotFoundError(input.id);
    }
    return wrapResponse(omitSensitive(user));
  }),

// Router - errors from service bubble up to formatter
delete: protectedProcedure
  .input(z.object({ id: z.string() }))
  .mutation(async ({ input }) => {
    await makeUserService().delete(input.id);
    return { success: true };
  }),
```

## Database Error Translation

Repositories **MUST** catch known database constraint violations and translate them to domain errors. Raw database error messages (SQL queries, parameter values, constraint names) **MUST NEVER** propagate to the error formatter.

### Postgres Error Type Guard

```typescript
// shared/infra/db/errors.ts

interface PostgresError {
  code: string;
  detail?: string;
  constraint?: string;
}

export function isPostgresError(error: unknown): error is PostgresError {
  return (
    error instanceof Error &&
    "code" in error &&
    typeof (error as any).code === "string" &&
    /^\d{5}$/.test((error as any).code)
  );
}
```

### Common Postgres Error Codes

| Code    | Name                       | Domain Translation                                       |
| ------- | -------------------------- | -------------------------------------------------------- |
| `23505` | Unique violation           | `ConflictError` — resource already exists                |
| `23503` | Foreign key violation      | `ValidationError` — referenced resource not found        |
| `23502` | Not null violation         | `ValidationError` — required field missing               |
| `23514` | Check constraint violation | `ValidationError` — value out of range                   |

### Repository Pattern

```typescript
// modules/organization/repositories/organization.repository.ts

import { isPostgresError } from "@/shared/infra/db/errors";
import { OrganizationSlugConflictError } from "../errors/organization.errors";

export class OrganizationRepository implements IOrganizationRepository {
  async create(
    data: OrganizationInsert,
    ctx?: RequestContext,
  ): Promise<Organization> {
    const client = this.getClient(ctx);

    try {
      const result = await client
        .insert(organizations)
        .values(data)
        .returning();

      return result[0];
    } catch (error) {
      if (isPostgresError(error) && error.code === "23505") {
        throw new OrganizationSlugConflictError(data.slug);
      }
      throw error; // Unknown DB error — let it bubble
    }
  }
}
```

**Rules:**

- Only catch constraint codes you can translate to a meaningful domain error
- Always re-throw unknown database errors — the formatter will sanitize them
- Prefer application-level checks (query-then-insert) for common cases; use database-level catches as a safety net for race conditions
- Domain error messages MUST be user-safe: `"Organization slug already exists"`, NOT `"duplicate key value violates unique constraint \"organizations_slug_key\""`

## Error Propagation Safety Rules

Every error passes through a chain of layers before reaching the client. Each layer has specific responsibilities:

| Layer | Responsibility | Example |
|-------|---------------|---------|
| **Repository** | Catch known DB constraints → throw domain error; re-throw unknown | `23505` → `OrganizationSlugConflictError` |
| **Service** | Throw domain errors only; never catch-and-wrap unknown errors | `throw new UserNotFoundError(id)` |
| **Router error handler** | Re-throw as `TRPCError({ cause: appError })` so formatter controls exposure | `throw new TRPCError({ code: "NOT_FOUND", cause: error })` |
| **Formatter** | Always call `getPublicErrorMessage()` and `canExposeErrorDetails()` | 5xx → generic message; 4xx → domain message |

**Safety invariant:** At no point in this chain should a raw library or database error message appear in a client response.

### What happens to unknown errors

If an error is NOT an `AppError` (e.g., a raw Postgres error that wasn't caught in the repository), the formatter treats it as an unknown error:

- Logs the full error at `error` level (including SQL, params, stack trace)
- Returns `GENERIC_PUBLIC_ERROR_MESSAGE` to the client
- Returns `appCode: "INTERNAL_ERROR"` with no details

This is the **last line of defense**. Catching DB errors in the repository is the first.

## HTTP Status Code Reference

| Status | Class                     | When to Use                                     |
| ------ | ------------------------- | ----------------------------------------------- |
| 400    | `ValidationError`         | Malformed request, invalid input, or operation-specific precondition failures |
| 401    | `AuthenticationError`     | Missing or invalid credentials                  |
| 403    | `AuthorizationError`      | Valid credentials, insufficient permissions     |
| 404    | `NotFoundError`           | Resource does not exist                         |
| 409    | `ConflictError`           | Resource conflict (duplicate, version mismatch) |
| 422    | `BusinessRuleError`       | Valid request, but violates a structural business invariant |
| 429    | `RateLimitError`          | Too many requests                               |
| 500    | `InternalError`           | Unexpected server error                         |
| 502    | `BadGatewayError`         | Upstream service error                          |
| 503    | `ServiceUnavailableError` | Service temporarily unavailable                 |
| 504    | `GatewayTimeoutError`     | Upstream service timeout                        |

### ValidationError (400) vs BusinessRuleError (422) — Disambiguation

Both represent "the request cannot be fulfilled," but they convey different semantics to the client:

| Use `ValidationError` (400) when | Use `BusinessRuleError` (422) when |
| --- | --- |
| The operation's **specific preconditions** are not met | A **structural business invariant** is violated |
| The client could fix the issue by changing the request timing or input | The client understands the rule but the system state prevents it |
| Examples: slot not available, reservation expired, booking window exceeded, terms not accepted, ping limit exceeded | Examples: cannot delete own account, workspace has active projects, cannot downgrade plan with active features |

Rule of thumb: if the error describes a **transient or operation-specific** condition the user can act on, use `ValidationError`. If it describes a **permanent structural rule** of the domain, use `BusinessRuleError`.

### Retryable Status Codes

Clients can determine retry behavior from status code:

| Status | Retryable | Notes                                            |
| ------ | --------- | ------------------------------------------------ |
| 4xx    | No        | Client error, won't change without client action |
| 429    | Yes       | Rate limited, retry after backoff                |
| 500    | Maybe     | Depends on cause                                 |
| 502    | Yes       | Bad gateway, transient                           |
| 503    | Yes       | Unavailable, retry after backoff                 |
| 504    | Yes       | Timeout, retry                                   |

## Checklist

### Base Infrastructure
- [ ] Base `AppError` class in `shared/kernel/errors.ts`
- [ ] Core error classes for common HTTP statuses (400, 401, 403, 404, 409, 422, 429, 500, 502, 503, 504)
- [ ] `public-error.ts` in kernel with `getPublicErrorMessage`, `canExposeErrorDetails`, `isInternalAppError`
- [ ] `GENERIC_PUBLIC_ERROR_MESSAGE` constant used (never hardcoded strings)
- [ ] Validation helper wraps Zod errors into `ValidationError`

### Domain Error Classes (CRITICAL)

Every domain error class MUST have:

```typescript
export class <Entity><ErrorType>Error extends <BaseError> {
  readonly code = '<MODULE>_<ERROR_TYPE>';  // REQUIRED - unique code
  
  constructor(<params>) {
    super('<message>', { <details> });
  }
}
```

**Checklist for each domain error:**
- [ ] Extends appropriate base class (`NotFoundError`, `ConflictError`, `AuthenticationError`, etc.)
- [ ] Has `readonly code` property with unique value
- [ ] Code format: `<MODULE>_<ERROR_TYPE>` in SCREAMING_SNAKE_CASE
- [ ] Constructor passes relevant IDs to `details` object
- [ ] Message is user-safe (no internal details)

**Common error codes by module:**
| Module | Error | Code |
|--------|-------|------|
| Auth | Invalid credentials | `AUTH_INVALID_CREDENTIALS` |
| Auth | Email not verified | `AUTH_EMAIL_NOT_VERIFIED` |
| Auth | User already exists | `AUTH_USER_ALREADY_EXISTS` |
| Auth | Session expired | `AUTH_SESSION_EXPIRED` |
| User | User not found | `USER_NOT_FOUND` |
| User | Email conflict | `USER_EMAIL_CONFLICT` |
| Workspace | Not found | `WORKSPACE_NOT_FOUND` |
| Workspace | Access denied | `WORKSPACE_ACCESS_DENIED` |

### Error Handler / tRPC Error Formatter
- [ ] Error handler attaches `requestId` to all responses
- [ ] Error logs include `requestId` field
- [ ] Known errors (`AppError`) logged at `warn` level with `code`, `details`, `requestId`
- [ ] Unknown errors logged at `error` level with full stack and `requestId`
- [ ] Client response includes `code`, `message`, `requestId`, optional `details`
- [ ] Client never receives stack traces or internal details
- [ ] Formatter calls `getPublicErrorMessage()` — never passes raw `shape.message` through
- [ ] Formatter uses `pickPublicTrpcShapeData()` — never spreads raw `shape.data`
- [ ] 5xx responses have no `details` field (only `appCode` and `requestId`)
- [ ] Application error codes use `appCode` field (not `code`, which is tRPC's)

```typescript
// CORRECT - requestId included in logs
ctx?.log.warn(
  { err: cause, code: cause.code, details: cause.details, requestId },
  cause.message,
);

// WRONG - missing requestId
ctx?.log.warn(
  { err: cause, code: cause.code, details: cause.details },
  cause.message,
);
```

### Use Cases
- [ ] Throw domain errors (NOT generic `Error`)
- [ ] Use specific error types for each failure case

```typescript
// CORRECT
if (!result.user) {
  throw new AuthRegistrationFailedError(input.email);
}

// WRONG
if (!result.user) {
  throw new Error('Failed to create user');
}
```

### Router Layer
- [ ] Router handles null returns from service
- [ ] Router throws appropriate domain error for null
- [ ] Add per-router error handler only when module-specific tRPC code mapping is needed (see `server/core/conventions.md`)
- [ ] Unknown errors re-thrown to the global formatter
