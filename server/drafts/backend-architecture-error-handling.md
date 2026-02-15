# Error Handling Architecture

> **Purpose**: This document defines the error handling conventions, custom error classes, and error flow across layers.

---

## 1. Overview

**Principles:**

- Errors are explicit and typed
- HTTP status codes follow REST semantics
- Client receives structured, safe responses
- Internal details are logged, never exposed
- Domain-specific errors for clear API contracts

---

## 2. Base Error Class

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

---

## 3. Core Error Classes

```typescript
// shared/kernel/errors.ts

// 400 - Bad Request
export class ValidationError extends AppError {
  readonly code = 'VALIDATION_ERROR';
  readonly httpStatus = 400;
}

// 401 - Unauthorized
export class AuthenticationError extends AppError {
  readonly code = 'AUTHENTICATION_ERROR';
  readonly httpStatus = 401;
}

// 403 - Forbidden
export class AuthorizationError extends AppError {
  readonly code = 'AUTHORIZATION_ERROR';
  readonly httpStatus = 403;
}

// 404 - Not Found
export class NotFoundError extends AppError {
  readonly code = 'NOT_FOUND';
  readonly httpStatus = 404;
}

// 409 - Conflict
export class ConflictError extends AppError {
  readonly code = 'CONFLICT';
  readonly httpStatus = 409;
}

// 422 - Unprocessable Entity (business rule violations)
export class BusinessRuleError extends AppError {
  readonly code = 'BUSINESS_RULE_VIOLATION';
  readonly httpStatus = 422;
}

// 429 - Too Many Requests
export class RateLimitError extends AppError {
  readonly code = 'RATE_LIMIT_EXCEEDED';
  readonly httpStatus = 429;
}

// 500 - Internal Server Error
export class InternalError extends AppError {
  readonly code = 'INTERNAL_ERROR';
  readonly httpStatus = 500;
}

// 502 - Bad Gateway
export class BadGatewayError extends AppError {
  readonly code = 'BAD_GATEWAY';
  readonly httpStatus = 502;
}

// 503 - Service Unavailable
export class ServiceUnavailableError extends AppError {
  readonly code = 'SERVICE_UNAVAILABLE';
  readonly httpStatus = 503;
}

// 504 - Gateway Timeout
export class GatewayTimeoutError extends AppError {
  readonly code = 'GATEWAY_TIMEOUT';
  readonly httpStatus = 504;
}
```

---

## 4. Domain-Specific Errors

Each module defines its own error subclasses for specific error codes.

```typescript
// modules/user/errors/user.errors.ts

import { NotFoundError, ConflictError, BusinessRuleError } from '@/shared/kernel/errors';

export class UserNotFoundError extends NotFoundError {
  readonly code = 'USER_NOT_FOUND';

  constructor(userId: string) {
    super('User not found', { userId });
  }
}

export class UserEmailConflictError extends ConflictError {
  readonly code = 'USER_EMAIL_CONFLICT';

  constructor(email: string) {
    super('Email already in use', { email });
  }
}

export class UserCannotDeleteSelfError extends BusinessRuleError {
  readonly code = 'USER_CANNOT_DELETE_SELF';

  constructor(userId: string) {
    super('Cannot delete your own account', { userId });
  }
}
```

```typescript
// modules/workspace/errors/workspace.errors.ts

import { NotFoundError, AuthorizationError, BusinessRuleError } from '@/shared/kernel/errors';

export class WorkspaceNotFoundError extends NotFoundError {
  readonly code = 'WORKSPACE_NOT_FOUND';

  constructor(workspaceId: string) {
    super('Workspace not found', { workspaceId });
  }
}

export class WorkspaceAccessDeniedError extends AuthorizationError {
  readonly code = 'WORKSPACE_ACCESS_DENIED';

  constructor(workspaceId: string, userId: string) {
    super('Access to workspace denied', { workspaceId, userId });
  }
}

export class WorkspaceHasActiveProjectsError extends BusinessRuleError {
  readonly code = 'WORKSPACE_HAS_ACTIVE_PROJECTS';

  constructor(workspaceId: string, projectCount: number) {
    super('Cannot delete workspace with active projects', { workspaceId, projectCount });
  }
}
```

### Folder Structure

```
modules/
├─ user/
│  ├─ errors/
│  │  └─ user.errors.ts
│  └─ ...
├─ workspace/
│  ├─ errors/
│  │  └─ workspace.errors.ts
│  └─ ...
```

---

## 5. Validation Error Handling

Use a generic handler that transforms Zod errors into `ValidationError`:

```typescript
// shared/utils/validation.ts

import { ZodError, ZodSchema } from 'zod';
import { ValidationError } from '@/shared/kernel/errors';

export function validate<T>(schema: ZodSchema<T>, data: unknown): T {
  const result = schema.safeParse(data);

  if (!result.success) {
    throw new ValidationError('Validation failed', {
      issues: result.error.issues.map((issue) => ({
        path: issue.path.join('.'),
        message: issue.message,
      })),
    });
  }

  return result.data;
}
```

**Usage:**

```typescript
import { validate } from '@/shared/utils/validation';
import { CreateUserSchema } from './dtos/create-user.dto';

const input = validate(CreateUserSchema, req.body);
```

---

## 6. Error Response Structure

### Client Response

```typescript
interface ErrorResponse {
  code: string;              // Error code (e.g., 'USER_NOT_FOUND')
  message: string;           // Human-readable message
  requestId: string;         // For support/debugging
  details?: {                // Optional additional context
    [key: string]: unknown;
  };
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

---

## 7. Error Handler

### Generic Handler

```typescript
// shared/infra/http/error-handler.ts

import { AppError } from '@/shared/kernel/errors';
import { logger } from '@/shared/infra/logger';

interface ErrorResponseBody {
  code: string;
  message: string;
  requestId: string;
  details?: Record<string, unknown>;
}

export function handleError(
  error: unknown,
  requestId: string,
): { status: number; body: ErrorResponseBody } {
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
        message: error.message,
        requestId,
        ...(error.details && { details: error.details }),
      },
    };
  }

  // Unknown error - log full details, return generic response
  logger.error(
    { 
      err: error,
      requestId,
    },
    'Unexpected error',
  );

  return {
    status: 500,
    body: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
      requestId,
    },
  };
}
```

### tRPC Error Formatter

```typescript
// shared/infra/trpc/trpc.ts

import { initTRPC, TRPCError } from '@trpc/server';
import { AppError } from '@/shared/kernel/errors';
import { logger } from '@/shared/infra/logger';
import type { Context } from './context';

const t = initTRPC.context<Context>().create({
  errorFormatter({ error, shape, ctx }) {
    const cause = error.cause;
    const requestId = ctx?.requestId ?? 'unknown';

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
        data: {
          ...shape.data,
          code: cause.code,
          requestId,
          details: cause.details,
        },
      };
    }

    // Unknown error
    logger.error(
      {
        err: error,
        requestId,
      },
      'Unexpected error',
    );

    return {
      ...shape,
      data: {
        ...shape.data,
        code: 'INTERNAL_ERROR',
        requestId,
      },
    };
  },
});
```

---

## 8. Error Flow by Layer

| Layer | Throws | Catches |
|-------|--------|---------|
| Repository | `NotFoundError`, `ConflictError` | Nothing |
| Service | Domain-specific errors, `BusinessRuleError` | Nothing (let bubble) |
| Use Case | Domain-specific errors | Nothing (let bubble) |
| Router/Controller | Nothing | All (via error handler) |

**Example flow:**

```typescript
// Repository
async findByIdOrThrow(id: string, ctx?: RequestContext): Promise<User> {
  const user = await this.findById(id, ctx);
  if (!user) {
    throw new UserNotFoundError(id);
  }
  return user;
}

// Service
async delete(id: string): Promise<void> {
  return this.transactionManager.run(async (tx) => {
    const user = await this.userRepository.findByIdOrThrow(id, { tx });
    
    if (user.role === 'owner') {
      throw new UserCannotDeleteOwnerError(id);
    }
    
    await this.userRepository.delete(id, { tx });
  });
}

// Router - errors bubble up and are caught by error formatter
deleteUser: protectedProcedure
  .input(z.object({ id: z.string() }))
  .mutation(async ({ input }) => {
    await makeUserService().delete(input.id);
    return { success: true };
  }),
```

---

## 9. HTTP Status Code Reference

| Status | Class | When to Use |
|--------|-------|-------------|
| 400 | `ValidationError` | Malformed request, invalid input |
| 401 | `AuthenticationError` | Missing or invalid credentials |
| 403 | `AuthorizationError` | Valid credentials, insufficient permissions |
| 404 | `NotFoundError` | Resource does not exist |
| 409 | `ConflictError` | Resource conflict (duplicate, version mismatch) |
| 422 | `BusinessRuleError` | Valid request, but violates business rules |
| 429 | `RateLimitError` | Too many requests |
| 500 | `InternalError` | Unexpected server error |
| 502 | `BadGatewayError` | Upstream service error |
| 503 | `ServiceUnavailableError` | Service temporarily unavailable |
| 504 | `GatewayTimeoutError` | Upstream service timeout |

### Retryable Status Codes

Clients can determine retry behavior from status code:

| Status | Retryable | Notes |
|--------|-----------|-------|
| 4xx | ❌ | Client error, won't change without client action |
| 429 | ✅ | Rate limited, retry after backoff |
| 500 | ⚠️ | Maybe, depends on cause |
| 502 | ✅ | Bad gateway, transient |
| 503 | ✅ | Unavailable, retry after backoff |
| 504 | ✅ | Timeout, retry |

---

## 10. Checklist

- [ ] Base `AppError` class in `shared/kernel/errors.ts`
- [ ] Core error classes for common HTTP statuses
- [ ] Domain-specific errors in each module's `errors/` folder
- [ ] Validation helper wraps Zod errors into `ValidationError`
- [ ] Error handler attaches `requestId` to all responses
- [ ] Known errors logged at `warn` level
- [ ] Unknown errors logged at `error` level with full stack
- [ ] Client never receives stack traces or internal details
