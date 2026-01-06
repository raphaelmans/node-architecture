---
name: backend-logging
description: Implement structured logging with Pino, request tracing, business event logging, and consistent log formatting in Next.js + tRPC projects
---

# Backend Logging

Use this skill when implementing logging, request tracing, or business event logging.

## Architecture

| Component | Location | Responsibility |
|-----------|----------|----------------|
| Logger setup | `shared/infra/logger.ts` | Pino configuration |
| Request logger | `shared/infra/logger.ts` | Child logger factory |
| Logger middleware | `shared/infra/trpc/middleware/logger.middleware.ts` | Request lifecycle |
| Business events | Service layer | Domain event logging |

## Logger Setup

```typescript
// shared/infra/logger.ts
import pino from "pino";
import { env } from "@/lib/env";

const isDev = env.NODE_ENV === "development";

export const logger = pino({
  level: env.LOG_LEVEL ?? (isDev ? "debug" : "info"),
  base: { env: env.NODE_ENV, service: "api" },
  redact: ["password", "token", "secret", "authorization"],
  ...(isDev && {
    transport: {
      target: "pino-pretty",
      options: { colorize: true },
    },
  }),
});

export type Logger = typeof logger;

/**
 * Creates a child logger with request context.
 */
export function createRequestLogger(ctx: {
  requestId: string;
  userId?: string | null;
  method: string;
  path: string;
}) {
  return logger.child({
    requestId: ctx.requestId,
    userId: ctx.userId,
    method: ctx.method,
    path: ctx.path,
  });
}
```

## Request Tracing

### Logger Middleware

```typescript
// shared/infra/trpc/middleware/logger.middleware.ts
import { middleware } from "../trpc";

export const loggerMiddleware = middleware(async ({ ctx, next, type }) => {
  const start = Date.now();

  ctx.log.info({ type }, "Request started");

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
```

### Use in Procedures

```typescript
// shared/infra/trpc/trpc.ts
const loggedProcedure = t.procedure.use(loggerMiddleware);

export const publicProcedure = loggedProcedure;
export const protectedProcedure = loggedProcedure.use(authMiddleware);
```

## Business Event Logging

Log significant business events in the **Service layer**:

```typescript
// modules/auth/services/auth.service.ts
import { logger } from "@/shared/infra/logger";

export class AuthService {
  async signIn(email: string, password: string) {
    const result = await this.authRepository.signInWithPassword(email, password);

    // Business event
    logger.info(
      { event: "user.logged_in", userId: result.user.id, email },
      "User logged in"
    );

    return result;
  }

  async signOut() {
    await this.authRepository.signOut();

    logger.info({ event: "user.logged_out" }, "User logged out");
  }
}
```

## Log Format Convention

### Field Ordering

```typescript
// 1. Event type identifier
// 2. Entity identifiers (userId, workspaceId)
// 3. Action-specific data
// 4. Metadata (duration, status)

logger.info(
  {
    event: "user.logged_in",  // 1. Event type
    userId: user.id,          // 2. Primary entity
    email: user.email,        // 3. Action-specific
  },
  "User logged in"            // Human-readable message
);
```

### Required Fields by Log Type

| Log Type | Required Fields | Optional |
|----------|-----------------|----------|
| Request start | `type` | — |
| Request end | `duration`, `status`, `type` | `error` |
| Business event | `event`, entity ID | Related IDs |
| Known error | `err`, `code`, `requestId` | `details` |
| Unknown error | `err`, `requestId` | — |

### Message Format

- **Request lifecycle**: Short verb phrase ("Request started", "Request completed")
- **Business events**: Past tense ("User logged in", "Order created")
- **Errors**: The error message itself

```typescript
// Good
log.info({ type }, "Request started");
log.info({ duration, status, type }, "Request completed");
logger.info({ event: "user.registered", userId }, "User registered");

// Bad - avoid
log.info("Starting request processing...");  // Too verbose
log.info("Done");                            // Too vague
```

## Event Naming Convention

Format: `<entity>.<action>` (past tense, dot-separated)

### Standard Events

| Event | When |
|-------|------|
| `user.created` | New user registered |
| `user.logged_in` | Successful login |
| `user.logged_out` | User logged out |
| `user.updated` | Profile updated |
| `user.deleted` | Account deleted |
| `user.magic_link_requested` | Magic link sent |
| `user.password_changed` | Password updated |
| `workspace.created` | New workspace |
| `workspace.member.added` | Member added |
| `workspace.member.removed` | Member removed |
| `payment.processed` | Payment completed |
| `payment.failed` | Payment failed |

## Error Logging

Handle in error formatter, not manually:

```typescript
// shared/infra/trpc/trpc.ts
const t = initTRPC.context<Context>().create({
  errorFormatter({ error, shape, ctx }) {
    const cause = error.cause;
    const requestId = ctx?.requestId ?? "unknown";

    if (cause instanceof AppError) {
      // Known error - warn level
      ctx?.log.warn(
        { err: cause, code: cause.code, details: cause.details, requestId },
        cause.message
      );
      return { ...shape, data: { code: cause.code, requestId } };
    }

    // Unknown error - error level
    ctx?.log.error({ err: error, requestId }, "Unexpected error");
    return { ...shape, data: { code: "INTERNAL_ERROR", requestId } };
  },
});
```

## Layer Rules

| Layer | Logging |
|-------|---------|
| Router | None (middleware handles) |
| Service | Business events |
| Repository | None |
| Use Case | None (services log) |

## Checklist

### Configuration
- [ ] Pino configured with appropriate log level
- [ ] Pretty printing in development
- [ ] Sensitive fields redacted
- [ ] Base context includes `env` and `service`

### Request Tracing
- [ ] Request ID generated (UUID)
- [ ] Child logger with `requestId`, `userId`, `method`, `path`
- [ ] Logger middleware logs start/end with duration
- [ ] All procedures use `loggedProcedure` as base

### Business Events
- [ ] Services log at `info` level
- [ ] Events use `event` field with `<entity>.<action>` format
- [ ] Events include primary entity ID
- [ ] Message is past tense, concise

### Error Logging
- [ ] Known errors at `warn` with `code`, `details`
- [ ] Unknown errors at `error` with full stack
- [ ] Error message used as log message
