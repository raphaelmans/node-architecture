# Error Handling

> Error handling conventions, custom error classes, and error flow across layers.

## Principles

- Errors are explicit and typed
- Kernel errors express semantic kinds; transport adapters map them to protocol codes
- Client receives structured, safe responses
- Internal details are logged, never exposed
- Domain-specific errors for clear API contracts

## Public Error Message Policy

Use a hybrid policy so clients get actionable messages for expected failures, while internal details stay private:

- 5xx errors **MUST** return `GENERIC_PUBLIC_ERROR_MESSAGE` — never the original message
- 4xx errors **MAY** return the domain error message (e.g., "User not found")
- Internal `details` are server-only; only explicitly allowlisted `publicDetails` may serialize on eligible 4xx responses
- `details` **MUST** be absent from 5xx responses (no stack traces, SQL, constraint names)
- Never serialize raw SQL/provider/stack messages in response bodies
- Always log full error context server-side; contextual `AppLogger` adds the namespaced request ID and active trace fields

### `public-error.ts` — Kernel Utility

Both the HTTP error handler and the tRPC error formatter share the same public-message policy via `shared/kernel/public-error.ts`. This file is a **required** kernel utility — do not inline the logic in individual handlers.

```typescript
// shared/kernel/public-error.ts

import { AppError } from "./errors";

export const GENERIC_PUBLIC_ERROR_MESSAGE = "An unexpected error occurred";

const INTERNAL_KINDS = new Set<AppError["kind"]>([
  "internal",
  "bad_gateway",
  "unavailable",
  "timeout",
]);

export function isInternalAppError(error: AppError): boolean {
  return INTERNAL_KINDS.has(error.kind);
}

export function getPublicErrorMessage(error: AppError): string {
  if (isInternalAppError(error)) {
    return GENERIC_PUBLIC_ERROR_MESSAGE;
  }
  return error.message;
}

export function canExposeErrorDetails(error: AppError): boolean {
  return !isInternalAppError(error) && error.publicDetails !== undefined;
}
```

## Base Error Class

```typescript
// shared/kernel/errors.ts

export abstract class AppError extends Error {
  abstract readonly code: string;
  abstract readonly kind: AppErrorKind;
  readonly details?: Record<string, unknown>;
  readonly publicDetails?: Record<string, unknown>;

  constructor(
    message: string,
    details?: Record<string, unknown>,
    publicDetails?: Record<string, unknown>,
  ) {
    super(message);
    this.name = this.constructor.name;
    this.details = details;
    this.publicDetails = publicDetails;
  }
}

export type AppErrorKind =
  | "validation"
  | "authentication"
  | "authorization"
  | "not_found"
  | "conflict"
  | "business_rule"
  | "rate_limit"
  | "internal"
  | "bad_gateway"
  | "unavailable"
  | "timeout";
```

## Core Error Classes

```typescript
// shared/kernel/errors.ts

export class ValidationError extends AppError {
  readonly code = "VALIDATION_ERROR";
  readonly kind = "validation" as const;
}

export class AuthenticationError extends AppError {
  readonly code = "AUTHENTICATION_ERROR";
  readonly kind = "authentication" as const;
}

export class AuthorizationError extends AppError {
  readonly code = "AUTHORIZATION_ERROR";
  readonly kind = "authorization" as const;
}

export class NotFoundError extends AppError {
  readonly code = "NOT_FOUND";
  readonly kind = "not_found" as const;
}

export class ConflictError extends AppError {
  readonly code = "CONFLICT";
  readonly kind = "conflict" as const;
}

export class BusinessRuleError extends AppError {
  readonly code = "BUSINESS_RULE_VIOLATION";
  readonly kind = "business_rule" as const;
}

export class RateLimitError extends AppError {
  readonly code = "RATE_LIMIT_EXCEEDED";
  readonly kind = "rate_limit" as const;
}

export class InternalError extends AppError {
  readonly code = "INTERNAL_ERROR";
  readonly kind = "internal" as const;
}

export class BadGatewayError extends AppError {
  readonly code = "BAD_GATEWAY";
  readonly kind = "bad_gateway" as const;
}

export class ServiceUnavailableError extends AppError {
  readonly code = "SERVICE_UNAVAILABLE";
  readonly kind = "unavailable" as const;
}

export class GatewayTimeoutError extends AppError {
  readonly code = "GATEWAY_TIMEOUT";
  readonly kind = "timeout" as const;
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

import type { ZodError, ZodSchema } from "zod";
import { ValidationError } from "@/shared/kernel/errors";

export function toValidationError(
  error: ZodError,
  message = "Invalid request",
): ValidationError {
  const publicDetails = {
    issues: error.issues.map((issue) => ({
      path: issue.path.join("."),
      message: issue.message,
    })),
  };

  return new ValidationError(
    message,
    { issueCount: error.issues.length },
    publicDetails,
  );
}

export function validate<T>(schema: ZodSchema<T>, data: unknown): T {
  const result = schema.safeParse(data);

  if (!result.success) {
    throw toValidationError(result.error, "Validation failed");
  }

  return result.data;
}
```

**Usage:**

```typescript
import { validate } from "@/shared/utils/validation";
import { CreateUserInputSchema } from "@/modules/user/shared/contracts";

const input = validate(CreateUserInputSchema, req.body);
```

Runtime HTTP adapters must also translate malformed request encoding/JSON into `ValidationError`. Keep that parser in transport infrastructure; do not make the kernel depend on `Request` or framework types. Response-schema failures remain internal errors because they indicate server contract drift, not invalid client input.

Use one transport helper for Zod input parsing so Express, Hono, Next.js, and
OpenAPI adapters produce the same error contract:

```typescript
// shared/infra/http/validation.ts

import { z } from "zod";
import { toValidationError } from "@/shared/utils/validation";

export function parseRequestInput<T extends z.ZodTypeAny>(
  schema: T,
  value: unknown,
): z.infer<T> {
  const result = schema.safeParse(value);
  if (!result.success) {
    throw toValidationError(result.error);
  }
  return result.data;
}
```

`details` remains internal logging context. Only the sanitized path/message
projection in `publicDetails` is serialized in the 400 response; never expose
the raw Zod issue objects.

Framework validator middleware such as Hono's `zValidator` must use a custom
hook that throws this shared `ValidationError`; otherwise it may return a
framework-specific response before central error mapping runs.

## Error Response Structure

### Client Response

The standardized HTTP error response type is `ApiErrorResponse` (defined in `shared/kernel/response.ts`):

```typescript
// shared/kernel/response.ts
export interface ApiErrorResponse {
  code: string; // Error code (e.g., "USER_NOT_FOUND")
  message: string; // Public-safe user-facing message
  requestId: string; // For support/debugging
  details?: Record<string, unknown>; // Explicitly allowlisted public context only
}
```

**Example responses:**

```json
// 404 - Not Found
{
  "code": "USER_NOT_FOUND",
  "message": "User not found",
  "requestId": "req-abc-123"
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

HTTP status is transport mapping, not a property of the kernel error:

```typescript
// shared/infra/http/error-mapping.ts

import type { AppErrorKind } from "@/shared/kernel/errors";

const HTTP_STATUS_BY_KIND: Record<AppErrorKind, number> = {
  validation: 400,
  authentication: 401,
  authorization: 403,
  not_found: 404,
  conflict: 409,
  business_rule: 422,
  rate_limit: 429,
  internal: 500,
  bad_gateway: 502,
  unavailable: 503,
  timeout: 504,
};

export function toHttpStatus(kind: AppErrorKind): number {
  return HTTP_STATUS_BY_KIND[kind];
}
```

```typescript
// shared/infra/http/error-handler.ts

import { AppError } from "@/shared/kernel/errors";
import {
  getPublicErrorMessage,
  canExposeErrorDetails,
  GENERIC_PUBLIC_ERROR_MESSAGE,
} from "@/shared/kernel/public-error";
import { appLogger } from "@/shared/infra/logger";
import { APP_ATTRIBUTES } from "@/shared/infra/observability/attributes";
import { toHttpStatus } from "./error-mapping";
import type { ApiErrorResponse } from "@/shared/kernel/response";

export function handleError(
  error: unknown,
  requestId: string,
  logFields: Record<string, unknown> = {},
): { status: number; body: ApiErrorResponse } {
  // Known application error
  if (error instanceof AppError) {
    appLogger.warn(
      {
        ...logFields,
        err: error,
        "error.type": error.code,
        [APP_ATTRIBUTES.errorDetails]: error.details,
      },
      error.message,
    );

    return {
      status: toHttpStatus(error.kind),
      body: {
        code: error.code,
        message: getPublicErrorMessage(error),
        requestId,
        ...(canExposeErrorDetails(error) &&
          error.publicDetails && { details: error.publicDetails }),
      },
    };
  }

  // Unknown error - log full details, return generic response
  appLogger.error(
    {
      ...logFields,
      err: error,
      "error.type":
        error instanceof Error ? error.constructor.name : "UnknownError",
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

The optional `logFields` argument is for allowlisted transport context such as
the webhook provider/event ID and operational event name. Never pass raw
request bodies, headers, cookies, or provider response objects. The logger
adapter still overwrites trusted correlation fields from the active context.

## tRPC Error Formatter

For tRPC integration, see [tRPC Integration](../runtime/nodejs/libraries/trpc/integration.md).

The formatter has two critical security responsibilities:

1. **Override `shape.message`** with `getPublicErrorMessage()` — the raw message may contain SQL, stack traces, or constraint names
2. **Strip `shape.data`** with `pickPublicTrpcShapeData()` — tRPC's default shape data includes `stack` in development and other internal fields

```typescript
// shared/infra/trpc/trpc.ts

import { initTRPC, TRPCError } from "@trpc/server";
import { AppError, type AppErrorKind } from "@/shared/kernel/errors";
import {
  getPublicErrorMessage,
  canExposeErrorDetails,
  GENERIC_PUBLIC_ERROR_MESSAGE,
} from "@/shared/kernel/public-error";
import { appLogger } from "@/shared/infra/logger";
import { APP_ATTRIBUTES } from "@/shared/infra/observability/attributes";
import { getObservabilityContext } from "@/shared/infra/observability";
import type { Context } from "./context";

/**
 * Keep only `path` and `zodError` from tRPC shape data.
 * Keeps only explicitly public fields and strips all other transport/internal metadata.
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
    const requestId =
      ctx?.requestId ?? getObservabilityContext()?.requestId ?? "unknown";

    // Known application error
    if (cause instanceof AppError) {
      appLogger.warn(
        {
          err: cause,
          "error.type": cause.code,
          [APP_ATTRIBUTES.errorDetails]: cause.details,
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
            cause.publicDetails && { details: cause.publicDetails }),
        },
      };
    }

    // Input validation error — preserve tRPC's BAD_REQUEST shape (Zod messages)
    if (error.code === "BAD_REQUEST") {
      ctx?.log.warn(
        { err: error, "error.type": "BAD_REQUEST" },
        "Input validation failed",
      );

      return {
        ...shape,
        data: {
          ...pickPublicTrpcShapeData(shape.data),
          requestId,
        },
      };
    }

    // Unknown error — never expose internals
    appLogger.error(
      { err: error, "error.type": error.constructor.name },
      "Unexpected error",
    );

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

const TRPC_CODE_BY_KIND = {
  validation: "BAD_REQUEST",
  authentication: "UNAUTHORIZED",
  authorization: "FORBIDDEN",
  not_found: "NOT_FOUND",
  conflict: "CONFLICT",
  business_rule: "UNPROCESSABLE_CONTENT",
  rate_limit: "TOO_MANY_REQUESTS",
  internal: "INTERNAL_SERVER_ERROR",
  bad_gateway: "BAD_GATEWAY",
  unavailable: "SERVICE_UNAVAILABLE",
  timeout: "GATEWAY_TIMEOUT",
} as const satisfies Record<AppErrorKind, string>;

const appErrorMiddleware = t.middleware(async ({ ctx, next }) => {
  try {
    return await next({ ctx });
  } catch (error) {
    if (error instanceof AppError) {
      throw new TRPCError({
        code: TRPC_CODE_BY_KIND[error.kind],
        message: error.message,
        cause: error,
      });
    }
    throw error;
  }
});

// Every procedure starts from this base before auth/rate-limit middleware.
const baseProcedure = t.procedure.use(appErrorMiddleware);
```

The transport-level tRPC code remains on the error envelope itself (`error.code`) and is derived centrally from `AppError.kind`. Put the application-specific error code in `shape.data.appCode`. Routers do not repeat error-kind mapping.

## Error Flow by Layer

| Layer             | Throws                                                   | Catches                                                |
| ----------------- | -------------------------------------------------------- | ------------------------------------------------------ |
| Repository        | Domain errors (from caught DB constraints)               | Known Postgres constraint violations (e.g., `23505`)   |
| Service           | Domain-specific errors, `BusinessRuleError`              | Nothing (let bubble)                                   |
| Use Case          | Domain-specific errors                                   | Nothing (let bubble)                                   |
| Controller        | Capability-level `NotFoundError` for null results       | Nothing; let shared transport mapping handle it        |
| Framework Adapter | Transport parsing errors                                 | Nothing per route; shared transport mapping handles it |

**Example flow:**

```typescript
// Repository - returns null, doesn't throw
async findById(id: string, options?: TransactionOptions): Promise<User | null> {
  const client = this.getClient(options);
  const result = await client
    .select()
    .from(users)
    .where(eq(users.id, id))
    .limit(1);

  return result[0] ?? null;
}

// Service - business logic errors
async delete(id: string, options?: TransactionOptions): Promise<void> {
  const exec = async (transactionOptions: TransactionOptions) => {
    const user = await this.userRepository.findById(id, transactionOptions);
    if (!user) {
      throw new UserNotFoundError(id);
    }

    if (user.role === 'owner') {
      throw new UserCannotDeleteOwnerError(id);
    }

    await this.userRepository.delete(id, transactionOptions);
  };

  if (options?.tx) {
    return exec(options);
  }
  return this.transactionManager.run((tx) => exec({ tx }));
}

// Framework-neutral controller - handles capability-level null
class GetUserController {
  constructor(private readonly users: IUserService) {}

  async execute(input: GetUserInput): Promise<GetUserResponse> {
    const user = await this.users.findById(input.id);
    if (!user) {
      throw new UserNotFoundError(input.id);
    }
    return toUserResponse(user);
  }
}

// Framework adapter - errors from the controller bubble to shared mapping
delete: protectedProcedure
  .input(z.object({ id: z.string() }))
  .mutation(async ({ input }) => {
    const result = await makeDeleteUserController().execute(input);
    return DeleteUserResponseSchema.parse(result);
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
    options?: TransactionOptions,
  ): Promise<Organization> {
    const client = this.getClient(options);

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
| **Transport error middleware** | Map `AppError.kind` once and preserve the error as `cause` | `not_found` -> tRPC `NOT_FOUND` or HTTP `404` |
| **Formatter** | Always call `getPublicErrorMessage()` and expose only explicit `publicDetails` | 5xx → generic message; 4xx → domain message |

**Safety invariant:** At no point in this chain should a raw library or database error message appear in a client response.

### What happens to unknown errors

If an error is NOT an `AppError` (e.g., a raw Postgres error that wasn't caught in the repository), the formatter treats it as an unknown error:

- Logs the full error at `error` level (including SQL, params, stack trace)
- Returns `GENERIC_PUBLIC_ERROR_MESSAGE` to the client
- Returns `appCode: "INTERNAL_ERROR"` with no details

This is the **last line of defense**. Catching DB errors in the repository is the first.

## HTTP Status Mapping Reference

These are adapter mappings. The kernel classes expose `kind`, not an HTTP status.

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
- [ ] Core error classes expose semantic `kind` values with no HTTP/tRPC dependency
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
- [ ] Inherits the correct transport-neutral `kind` from its base class
- [ ] Code format: `<MODULE>_<ERROR_TYPE>` in SCREAMING_SNAKE_CASE
- [ ] Constructor passes relevant IDs to `details` object
- [ ] Client-visible metadata is separately allowlisted in `publicDetails`; internal `details` never serialize implicitly
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
- [ ] Request-scoped error logs include the namespaced request ID through contextual `AppLogger`
- [ ] Known errors (`AppError`) logged at `warn` level with `error.type` and safe details
- [ ] Unknown errors logged at `error` level with full stack and `error.type`
- [ ] Client response includes `code`, `message`, `requestId`, optional `details`
- [ ] Client never receives stack traces or internal details
- [ ] Formatter calls `getPublicErrorMessage()` — never passes raw `shape.message` through
- [ ] Formatter uses `pickPublicTrpcShapeData()` — never spreads raw `shape.data`
- [ ] 5xx responses have no `details` field (only `appCode` and `requestId`)
- [ ] Application error codes use `appCode` field (not `code`, which is tRPC's)

```typescript
import { APP_ATTRIBUTES } from "@/shared/infra/observability/attributes";

// CORRECT - correlation is supplied by contextual AppLogger
ctx?.log.warn(
  {
    err: cause,
    "error.type": cause.code,
    [APP_ATTRIBUTES.errorDetails]: cause.details,
  },
  cause.message,
);

// WRONG - caller manually serializes correlation fields
ctx?.log.warn(
  { err: cause, requestId, traceId, spanId },
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
- [ ] Let domain errors bubble to the shared transport mapping
- [ ] Unknown errors re-thrown to the global formatter
