# Logging

> Logging conventions, Pino configuration, and patterns across the application.

## Principles

- Structured JSON logging for machine parsing
- Human-readable output in development
- Request correlation via `requestId`
- Sensitive data redaction
- Log at appropriate levels and layers

**Library:** Pino

## Logger Configuration

```typescript
// shared/infra/logger/index.ts

import pino from "pino";

const isProduction = process.env.NODE_ENV === "production";

export const logger = pino({
  level: process.env.LOG_LEVEL ?? (isProduction ? "info" : "debug"),

  // Pretty print in development
  transport: isProduction
    ? undefined
    : {
        target: "pino-pretty",
        options: {
          colorize: true,
          translateTime: "SYS:standard",
          ignore: "pid,hostname",
        },
      },

  // Redact sensitive fields
  redact: {
    paths: [
      "password",
      "passwordHash",
      "token",
      "accessToken",
      "refreshToken",
      "authorization",
      "cookie",
      "creditCard",
      "cardNumber",
      "cvv",
      "ssn",
      "*.password",
      "*.passwordHash",
      "*.token",
      "*.accessToken",
      "*.refreshToken",
      "*.authorization",
      "*.creditCard",
      "*.cardNumber",
      "*.cvv",
      "*.ssn",
    ],
    censor: "[REDACTED]",
  },

  // Base context for all logs
  base: {
    env: process.env.NODE_ENV,
    service: process.env.SERVICE_NAME ?? "api",
  },
});

export type Logger = typeof logger;
```

## Request Logger (Child Logger)

Create a child logger with request context for correlation.

```typescript
// shared/infra/logger/index.ts

export interface RequestLogContext {
  requestId: string;
  userId?: string;
  method?: string;
  path?: string;
}

export function createRequestLogger(ctx: RequestLogContext) {
  return logger.child(ctx);
}
```

**Usage:**

```typescript
const log = createRequestLogger({
  requestId: ctx.requestId,
  userId: ctx.userId,
  method: "POST",
  path: "/api/users",
});

log.info("Processing request");
// Output: { "requestId": "abc-123", "userId": "usr-456", "method": "POST", "path": "/api/users", "msg": "Processing request" }
```

## Log Levels

| Level   | When to Use                               | Examples                                |
| ------- | ----------------------------------------- | --------------------------------------- |
| `error` | Unexpected failures, unhandled exceptions | Unknown errors, system failures         |
| `warn`  | Expected errors, recoverable issues       | Known application errors, deprecations  |
| `info`  | Request lifecycle, business events        | Request start/end, user created         |
| `debug` | Development details, verbose data         | Input/output bodies, intermediate state |

```typescript
log.error({ err }, "Unexpected database failure");
log.warn({ code: "USER_NOT_FOUND", userId }, "User not found");
log.info({ userId: user.id }, "User created");
log.debug({ input }, "Request input");
```

## What to Log by Layer

| Layer             | Log                                  | Level   |
| ----------------- | ------------------------------------ | ------- |
| Router/Middleware | Request start, end, duration, status | `info`  |
| Router/Middleware | Request input (in development)       | `debug` |
| Error Handler     | Known application errors             | `warn`  |
| Error Handler     | Unknown/unexpected errors            | `error` |
| Services          | Significant business events          | `info`  |
| Repositories      | Nothing                              | —       |

## Request Lifecycle Logging

### tRPC Middleware

**Important:** Define middleware inline in `trpc.ts` to avoid circular dependencies. Do NOT create separate middleware files that import from `trpc.ts`.

```typescript
// shared/infra/trpc/trpc.ts

import { initTRPC, TRPCError } from "@trpc/server";
import { AppError, AuthenticationError } from "@/shared/kernel/errors";
import type { Context, AuthenticatedContext } from "./context";

const t = initTRPC.context<Context>().create({
  errorFormatter({ error, shape, ctx }) {
    // ... error formatting
  },
});

export const router = t.router;
export const middleware = t.middleware;

/**
 * Logger middleware - request lifecycle tracing.
 * Defined inline to avoid circular dependency with middleware exports.
 */
const loggerMiddleware = t.middleware(async ({ ctx, next, type }) => {
  const start = Date.now();

  ctx.log.info({ type }, "Request started");

  // Log input at debug level only in development
  if (process.env.NODE_ENV !== "production") {
    ctx.log.debug("Request processing");
  }

  try {
    const result = await next({ ctx });
    const duration = Date.now() - start;

    ctx.log.info({ duration, status: "success", type }, "Request completed");

    return result;
  } catch (error) {
    const duration = Date.now() - start;

    ctx.log.info({ duration, status: "error", type }, "Request failed");

    throw error;
  }
});

/**
 * Auth middleware - requires valid session.
 * Defined inline to avoid circular dependency.
 */
const authMiddleware = t.middleware(async ({ ctx, next }) => {
  if (!ctx.session || !ctx.userId) {
    throw new TRPCError({
      code: "UNAUTHORIZED",
      message: "Authentication required",
      cause: new AuthenticationError("Authentication required"),
    });
  }

  return next({
    ctx: ctx as AuthenticatedContext,
  });
});

/**
 * Base procedure with logging - all procedures use this
 */
const loggedProcedure = t.procedure.use(loggerMiddleware);

/**
 * Public procedure - no authentication required
 */
export const publicProcedure = loggedProcedure;

/**
 * Protected procedure - authentication required
 */
export const protectedProcedure = loggedProcedure.use(authMiddleware);
```

## Service-Level Business Events

Log significant business events in services.

```typescript
// modules/user/services/user.service.ts

import { logger } from "@/shared/infra/logger";

export class UserService implements IUserService {
  async create(data: UserInsert, ctx?: RequestContext): Promise<User> {
    const user = await this.createInternal(data, ctx);

    // Business event: user created
    logger.info(
      {
        event: "user.created",
        userId: user.id,
        email: user.email,
      },
      "User created",
    );

    return user;
  }

  async delete(id: string, ctx?: RequestContext): Promise<void> {
    await this.deleteInternal(id, ctx);

    // Business event: user deleted
    logger.info(
      {
        event: "user.deleted",
        userId: id,
      },
      "User deleted",
    );
  }
}
```

## Log Format Convention

### Field Ordering

Always order log fields consistently for readability:

```typescript
// 1. Event type identifier (if business event)
// 2. Entity identifiers (userId, workspaceId, etc.)
// 3. Action-specific data
// 4. Metadata (duration, status, etc.)

logger.info(
  {
    event: "user.logged_in",     // 1. Event type
    userId: user.id,             // 2. Primary entity
    email: user.email,           // 3. Action-specific
  },
  "User logged in",              // Human-readable message
);
```

### Required Fields by Log Type

| Log Type | Required Fields | Optional Fields |
|----------|-----------------|-----------------|
| Request start | `type` | — |
| Request end | `duration`, `status`, `type` | `error` |
| Business event | `event`, primary entity ID | Related entity IDs |
| Known error | `err`, `code`, `requestId` | `details` |
| Unknown error | `err`, `requestId` | — |

### Message Format

- **Request lifecycle**: Short verb phrase ("Request started", "Request completed")
- **Business events**: Past tense describing what happened ("User logged in", "Order created")
- **Errors**: The error message itself

```typescript
// Good messages
log.info({ type }, "Request started");
log.info({ duration, status, type }, "Request completed");
logger.info({ event: "user.registered", userId }, "User registered");
logger.warn({ err, code, requestId }, err.message);

// Bad messages (avoid)
log.info("Starting request processing...");  // Too verbose
log.info("Done");                            // Too vague
logger.info({ event: "user.registered" }, "A new user has been registered in the system");  // Too wordy
```

### Business Event Naming Convention

Use past tense, dot-separated format:

```
<entity>.<action>
```

**Examples:**

| Event                      | Description                   |
| -------------------------- | ----------------------------- |
| `user.created`             | New user registered           |
| `user.logged_in`           | User logged in                |
| `user.logged_out`          | User logged out               |
| `user.updated`             | User profile updated          |
| `user.deleted`             | User account deleted          |
| `user.magic_link_requested`| Magic link email sent         |
| `workspace.created`        | New workspace created         |
| `workspace.member.added`   | Member added to workspace     |
| `workspace.member.removed` | Member removed from workspace |
| `payment.processed`        | Payment completed             |
| `payment.failed`           | Payment failed                |

### Auth Events

Standard auth-related events:

| Event | When | Fields |
|-------|------|--------|
| `user.registered` | New user created | `userId`, `email` |
| `user.logged_in` | Successful login | `userId`, `email` |
| `user.logged_out` | User logged out | — |
| `user.magic_link_requested` | Magic link sent | `email` |
| `user.session_exchanged` | OAuth/magic link callback | `userId` |
| `user.password_reset_requested` | Password reset email sent | `email` |
| `user.password_changed` | Password updated | `userId` |

## Error Logging

Errors are logged by the error handler (see [Error Handling](./error-handling.md)).

```typescript
// Known application error - warn level
logger.warn(
  {
    err: error,
    code: error.code,
    details: error.details,
    requestId,
  },
  error.message,
);

// Unknown error - error level with full stack
logger.error(
  {
    err: error,
    requestId,
  },
  "Unexpected error",
);
```

## Request Context Integration

### Request ID Generation

Generate UUID at the tRPC context creation.

```typescript
// shared/infra/trpc/context.ts

import { randomUUID } from "crypto";

export async function createContext({ req }: { req: Request }) {
  const requestId = req.headers.get("x-request-id") ?? randomUUID();

  return {
    requestId,
    userId: undefined, // Set by auth middleware
  };
}

export type Context = Awaited<ReturnType<typeof createContext>>;
```

## Sensitive Data Handling

### Automatic Redaction

Pino's `redact` option handles common sensitive fields automatically.

### Manual Sanitization

For cases where you need to log objects that might contain sensitive data:

```typescript
// shared/utils/sanitize.ts

const SENSITIVE_KEYS = [
  "password",
  "token",
  "authorization",
  "creditcard",
  "cardnumber",
  "cvv",
  "ssn",
  "secret",
];

export function sanitize<T extends Record<string, unknown>>(obj: T): T {
  const result = { ...obj };

  for (const key of Object.keys(result)) {
    const lowerKey = key.toLowerCase();
    if (SENSITIVE_KEYS.some((sensitive) => lowerKey.includes(sensitive))) {
      (result as Record<string, unknown>)[key] = "[REDACTED]";
    }
  }

  return result;
}
```

**Usage:**

```typescript
log.debug({ data: sanitize(requestBody) }, "Processing data");
```

## Log Output Examples

### Development (pino-pretty)

```
[2024-01-15 10:30:45] INFO: Request started
    requestId: "req-abc-123"
    userId: "usr-456"
    method: "mutation"
    path: "user.create"

[2024-01-15 10:30:45] DEBUG: Request input
    requestId: "req-abc-123"
    input: { email: "john@example.com", name: "John" }

[2024-01-15 10:30:46] INFO: User created
    event: "user.created"
    userId: "usr-789"
    email: "john@example.com"

[2024-01-15 10:30:46] INFO: Request completed
    requestId: "req-abc-123"
    duration: 145
    status: "success"
```

### Production (JSON)

```json
{"level":30,"time":1705312245000,"requestId":"req-abc-123","userId":"usr-456","method":"mutation","path":"user.create","msg":"Request started"}
{"level":30,"time":1705312246000,"event":"user.created","userId":"usr-789","email":"john@example.com","msg":"User created"}
{"level":30,"time":1705312246000,"requestId":"req-abc-123","duration":145,"status":"success","msg":"Request completed"}
```

## Future: Observability

When ready for full observability, extend with:

### OpenTelemetry Integration

```typescript
// Future: Add tracing context
export interface RequestContext {
  requestId: string;
  traceId: string; // W3C Trace Context
  spanId: string;
  tx?: TransactionContext;
}

// Future: Export to observability platform
// - Traces → Jaeger, Tempo, Datadog
// - Metrics → Prometheus, Datadog
// - Logs → Loki, CloudWatch, Datadog
```

## Checklist

### Configuration
- [ ] Pino configured with appropriate log level
- [ ] Pretty printing enabled in development
- [ ] Sensitive fields redacted via pino config
- [ ] Base context includes `env` and `service`

### Request Tracing
- [ ] Request ID generated at context creation (UUID)
- [ ] Request logger creates child logger with `requestId`, `userId`, `method`, `path`
- [ ] Logger middleware logs request start/end with duration
- [ ] All procedures use `loggedProcedure` as base
- [ ] Request input logged at `debug` level only (not in production)

### Business Events
- [ ] Services log significant business events at `info` level
- [ ] Business events use `event` field with `<entity>.<action>` format
- [ ] Business events include primary entity ID (e.g., `userId`)
- [ ] Auth events follow standard naming (`user.logged_in`, `user.registered`, etc.)
- [ ] Message is past tense, concise ("User logged in", not "A user has logged in")

### Error Logging
- [ ] Error handler logs known errors at `warn` with `code`, `details`, `requestId`
- [ ] Error handler logs unknown errors at `error` with full stack
- [ ] Error message used as log message (not generic text)

### Layer Rules
- [ ] Routers: No logging (handled by middleware)
- [ ] Services: Log business events
- [ ] Repositories: No logging
- [ ] Use cases: No logging (services log the events)
