# Logging

> Runtime-agnostic operational logging contract, event ownership, and dependency-injection rules.

## Principles

- Structured JSON logging for machine parsing
- Human-readable output in development
- Request correlation via namespaced request ID plus OpenTelemetry trace context
- Sensitive data redaction
- Log at appropriate levels and layers
- Application code depends on `AppLogger`, not a concrete logging SDK
- Product analytics uses a separate `ProductAnalytics` interface

The Node.js reference adapter uses [Pino](../runtime/nodejs/libraries/pino/README.md), but Pino is not part of the core contract.

## Boundary

Server logs exist for debugging and operations. They are not a product analytics stream.

| Server log | Product analytics |
| --- | --- |
| `Database connection failed` | `checkout_completed` |
| `Request completed` | `feature_used` |
| Operational log backend | Mixpanel, Google Analytics, or another analytics destination |

Follow [Observability](./observability.md) for request/trace propagation and [Product Analytics](./product-analytics.md) for analytics events and vendor fan-out.

## Logger Port and Dependency Injection

Define a vendor-neutral port in the kernel:

```typescript
// shared/kernel/logger.ts

export type LogFields = Record<string, unknown>;

export interface AppLogger {
  debug(fields: LogFields, message: string): void;
  info(fields: LogFields, message: string): void;
  warn(fields: LogFields, message: string): void;
  error(fields: LogFields, message: string): void;
}
```

The infrastructure layer adapts its chosen backend to `AppLogger` and enriches records from the active observability scope. Factories inject `AppLogger` into controllers, services, and use cases that produce meaningful operational logs.

Rules:

- Do not import a concrete logging SDK inside a controller, service, or use case.
- Do not combine logger, analytics, and tracing methods in one service locator.
- Inject `AppLogger` and `ProductAnalytics` separately when both are needed.
- Inject a spy or no-op implementation in unit tests.

## Adapter Requirements

Every runtime logger adapter must:

- implement `AppLogger`;
- emit structured records;
- merge trusted request/trace correlation from the active observability scope after caller fields;
- serialize errors with stack/cause for server-side diagnostics;
- redact secrets and sensitive fields before export;
- expose stable resource identity such as service and deployment environment;
- never let logging failure change business behavior.

Concrete configuration belongs to the runtime/library layer. See the [Node.js Pino Adapter](../runtime/nodejs/libraries/pino/README.md).

## Request Context Enrichment

Establish request context once at the transport boundary. The logger adapter reads it for every record and maps runtime names to the canonical serialized names.

```typescript
await withRequestObservability(request, async () => {
  appLogger.info(
    {
      "otel.event.name": "http.request.started",
      "http.request.method": "POST",
      "http.route": "/api/users",
    },
    "Request started",
  );
});
```

The resulting JSON uses `trace_id`, `span_id`, `trace_flags`, and `com.example.api.request.id`. Do not create per-request concrete logger children with `{ requestId, traceId, spanId }` in application code.

## Log Levels

| Level   | When to Use                               | Examples                                |
| ------- | ----------------------------------------- | --------------------------------------- |
| `error` | Unexpected failures, unhandled exceptions | Unknown errors, system failures         |
| `warn`  | Expected errors, recoverable issues       | Known application errors, deprecations  |
| `info`  | Request lifecycle, operational events     | Request start/end, user created         |
| `debug` | Development details, verbose data         | Input/output bodies, intermediate state |

```typescript
log.error({ err }, "Unexpected database failure");
log.warn({ "error.type": "USER_NOT_FOUND", "user.id": userId }, "User not found");
log.info({ "otel.event.name": "user.created", "user.id": user.id }, "User created");
log.debug({ input }, "Request input");
```

## What to Log by Layer

| Layer             | Log                                  | Level   |
| ----------------- | ------------------------------------ | ------- |
| Router/Middleware | Request start, end, duration, status | `info`  |
| Router/Middleware | Request input (in development)       | `debug` |
| Controller        | Nothing routinely; meaningful capability-boundary events only | — / `info` |
| Error Handler     | Known application errors             | `warn`  |
| Error Handler     | Unknown/unexpected errors            | `error` |
| Services          | Significant business events          | `info`  |
| Repositories      | Nothing                              | —       |

## Request Lifecycle Logging

### Reference Transport Lifecycle

Every transport must implement this start/completion/failure lifecycle once. The tRPC-shaped excerpt below illustrates the core contract; the canonical implementation details live in [tRPC Integration](../runtime/nodejs/libraries/trpc/integration.md).

```typescript
// shared/infra/trpc/trpc.ts

import { initTRPC, TRPCError } from "@trpc/server";
import {
  AppError,
  AuthenticationError,
  type AppErrorKind,
} from "@/shared/kernel/errors";
import { APP_ATTRIBUTES } from "@/shared/infra/observability/attributes";
import type { Context, AuthenticatedContext } from "./context";

const t = initTRPC.context<Context>().create({
  errorFormatter({ error, shape, ctx }) {
    // ... error formatting
  },
});

export const router = t.router;
export const middleware = t.middleware;

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

/**
 * Logger middleware - request lifecycle tracing.
 * Defined inline to avoid circular dependency with middleware exports.
 */
const loggerMiddleware = t.middleware(async ({ ctx, next, path, type }) => {
  const start = Date.now();

  ctx.log.info(
    {
      "otel.event.name": "rpc.request.started",
      "rpc.system": "trpc",
      "rpc.method": path,
      [APP_ATTRIBUTES.operationType]: type,
    },
    "Request started",
  );

  // Log input at debug level only in development
  if (process.env.NODE_ENV !== "production") {
    ctx.log.debug({}, "Request processing");
  }

  try {
    const result = await next({ ctx });
    const duration = Date.now() - start;

    ctx.log.info(
      {
        "otel.event.name": "rpc.request.completed",
        "rpc.system": "trpc",
        "rpc.method": path,
        [APP_ATTRIBUTES.operationType]: type,
        [APP_ATTRIBUTES.durationMs]: duration,
        [APP_ATTRIBUTES.operationOutcome]: "success",
      },
      "Request completed",
    );

    return result;
  } catch (error) {
    const duration = Date.now() - start;

    ctx.log.info(
      {
        "otel.event.name": "rpc.request.failed",
        "rpc.system": "trpc",
        "rpc.method": path,
        [APP_ATTRIBUTES.operationType]: type,
        [APP_ATTRIBUTES.durationMs]: duration,
        [APP_ATTRIBUTES.operationOutcome]: "error",
      },
      "Request failed",
    );

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
 * Base procedure with central error mapping and logging.
 */
const baseProcedure = t.procedure
  .use(appErrorMiddleware)
  .use(loggerMiddleware);

/**
 * Public procedure - no authentication required
 */
export const publicProcedure = baseProcedure;

/**
 * Protected procedure - authentication required
 */
export const protectedProcedure = baseProcedure.use(authMiddleware);
```

## Service-Level Operational Events

Log significant business events in services.

```typescript
// modules/user/services/user.service.ts

export class UserService implements IUserService {
  constructor(
    private readonly repository: IUserRepository,
    private readonly logger: AppLogger,
  ) {}

  async create(data: UserInsert, options?: TransactionOptions): Promise<User> {
    const user = await this.createInternal(data, options);

    this.logger.info(
      {
        "otel.event.name": "user.created",
        "code.function.name": "UserService.create",
        "user.id": user.id,
      },
      "User created",
    );

    return user;
  }

  async delete(id: string, options?: TransactionOptions): Promise<void> {
    await this.deleteInternal(id, options);

    this.logger.info(
      {
        "otel.event.name": "user.deleted",
        "code.function.name": "UserService.delete",
        "user.id": id,
      },
      "User deleted",
    );
  }
}
```

## Log Format Convention

### Field Names

Use constants for custom fields and literal names only for registered OpenTelemetry or backend transport fields:

```typescript
import { APP_ATTRIBUTES } from "@/shared/infra/observability/attributes";

appLogger.info(
  {
    "otel.event.name": "user.logged_in",
    "code.function.name": "AuthService.completeLogin",
    "user.id": user.id,
    [APP_ATTRIBUTES.codeLayer]: "service",
    [APP_ATTRIBUTES.operationName]: "user.login",
  },
  "User logged in",
);
```

`level`, `time`, and `msg` in the examples are backend transport fields. `trace_id`, `span_id`, and the namespaced request-ID attribute are added by the adapter. See [Observability](./observability.md#canonical-correlated-json-record) for the authoritative mapping.

### Required Fields by Log Type

| Log Type | Required Fields | Optional Fields |
|----------|-----------------|-----------------|
| Request start | `otel.event.name`, transport semantic attributes | operation type/name |
| Request end | `otel.event.name`, transport semantic attributes, namespaced duration/outcome | `error.type` |
| Operational event | `otel.event.name`, primary entity semantic attribute | `code.function.name`, related entity IDs |
| Known error | `err`, `error.type` | safe details |
| Unknown error | `err` | `error.type` |

Correlation fields are required on every request-scoped record, but the adapter supplies them; callers do not repeat them.

### Message Format

- **Request lifecycle**: Short verb phrase ("Request started", "Request completed")
- **Business events**: Past tense describing what happened ("User logged in", "Order created")
- **Errors**: The error message itself

```typescript
// Good messages
log.info({ "otel.event.name": "rpc.request.started", "rpc.method": path }, "Request started");
log.info({ "otel.event.name": "rpc.request.completed", "rpc.method": path }, "Request completed");
appLogger.info({ "otel.event.name": "user.registered", "user.id": userId }, "User registered");
appLogger.warn({ err, "error.type": error.code }, error.message);

// Bad messages (avoid)
log.info("Starting request processing...");  // Too verbose
log.info("Done");                            // Too vague
appLogger.info({ "otel.event.name": "user.registered" }, "A new user has been registered in the system"); // Too wordy
```

### Operational Event Naming Convention

Use past tense, dot-separated format:

```
<entity>.<action>
```

Place this value in `otel.event.name` so a compatible non-OTLP JSON record can map to OpenTelemetry `EventName`. These records are operational breadcrumbs for debugging. If product reporting also needs the action, emit a separate typed `ProductEvent`; do not route the log record to analytics vendors.

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
| `user.registered` | New user created | `user.id` |
| `user.logged_in` | Successful login | `user.id` |
| `user.logged_out` | User logged out | — |
| `user.magic_link_requested` | Magic link sent | Avoid email address in logs |
| `user.session_exchanged` | OAuth/magic link callback | `user.id` |
| `user.password_reset_requested` | Password reset email sent | Avoid email address in logs |
| `user.password_changed` | Password updated | `user.id` |

## Error Logging

Errors are logged by the error handler (see [Error Handling](./error-handling.md)).

```typescript
import { APP_ATTRIBUTES } from "@/shared/infra/observability/attributes";

// Known application error - warn level
logger.warn(
  {
    err: error,
    "error.type": error.code,
    [APP_ATTRIBUTES.errorDetails]: error.details,
  },
  error.message,
);

// Unknown error - error level with full stack
logger.error(
  {
    err: error,
    "error.type": error.constructor.name,
  },
  "Unexpected error",
);
```

The contextual `AppLogger` adds the namespaced request ID and active trace fields. Do not pass correlation identifiers manually.

## Request Correlation Integration

### Request ID Generation

Generate or accept the application `requestId` at the transport boundary. OpenTelemetry owns `traceId` and `spanId`; application services do not pass them manually.

```typescript
// shared/infra/trpc/context.ts

import { randomUUID } from "crypto";
import { getTrustedRequestId } from "@/shared/infra/observability/request-id";

export async function createContext({ req }: { req: Request }) {
  const requestId = getTrustedRequestId(req.headers) ?? randomUUID();

  return {
    requestId,
    userId: undefined, // Set by auth middleware
  };
}

export type Context = Awaited<ReturnType<typeof createContext>>;
```

The tRPC context may expose the contextual `AppLogger` for transport middleware. Application services still receive the `AppLogger` port from their factories. Next.js, Express, and Hono establish the equivalent request scope in framework middleware or wrappers before invoking a controller. See [Next.js](../runtime/nodejs/metaframeworks/nextjs/route-handlers.md), [Express](../runtime/nodejs/metaframeworks/express/README.md), and [Hono](../runtime/nodejs/metaframeworks/hono/README.md).

## Sensitive Data Handling

### Automatic Redaction

The concrete logger adapter must redact common sensitive fields automatically. The Node.js Pino implementation is documented in [Pino Logger Adapter](../runtime/nodejs/libraries/pino/README.md).

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
import { APP_ATTRIBUTES } from "@/shared/infra/observability/attributes";

log.debug(
  { [APP_ATTRIBUTES.debugData]: sanitize(requestBody) },
  "Processing data",
);
```

## Log Output Examples

### Development (Human-Readable Adapter Output)

```
[2026-08-15 10:30:45] INFO: Request started
    otel.event.name: "http.request.started"
    http.request.method: "POST"
    http.route: "/api/users"
    trace_id: "4bf92f3577b34da6a3ce929d0e0e4736"
    span_id: "00f067aa0ba902b7"
    com.example.api.request.id: "req-abc-123"

[2026-08-15 10:30:46] INFO: User created
    otel.event.name: "user.created"
    code.function.name: "CreateUserUseCase.execute"
    user.id: "usr-789"
    trace_id: "4bf92f3577b34da6a3ce929d0e0e4736"
    span_id: "00f067aa0ba902b7"
    com.example.api.request.id: "req-abc-123"
```

### Production (JSON)

```json
{"level":30,"time":1786761045000,"msg":"Request started","otel.event.name":"http.request.started","http.request.method":"POST","http.route":"/api/users","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"00f067aa0ba902b7","trace_flags":"01","com.example.api.request.id":"req-abc-123"}
{"level":30,"time":1786761046000,"msg":"User created","otel.event.name":"user.created","code.function.name":"CreateUserUseCase.execute","user.id":"usr-789","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"00f067aa0ba902b7","trace_flags":"01","com.example.api.request.id":"req-abc-123"}
```

## Observability Integration

Request-scoped JSON logs include the configured namespaced request ID and, when tracing is enabled, `trace_id`, `span_id`, and `trace_flags`. Their runtime values come from async observability context and remain separate from `TransactionOptions`. See [Observability](./observability.md).

## Checklist

### Configuration
- [ ] Concrete adapter configured with an appropriate log level
- [ ] Pretty printing enabled in development
- [ ] Sensitive fields redacted by the concrete adapter/exporter
- [ ] Resource identity uses `deployment.environment.name` and `service.name`
- [ ] `AppLogger` port defined independently from the logging backend
- [ ] Controllers/services/use cases receive `AppLogger` through factories only when they emit meaningful operational events

### Request Tracing
- [ ] Request ID generated at context creation (UUID)
- [ ] Transport establishes async observability context once per request
- [ ] Adapter maps runtime `requestId` to the configured namespaced log attribute
- [ ] JSON trace correlation uses `trace_id`, `span_id`, and `trace_flags`
- [ ] Logger middleware logs request start/end with duration
- [ ] All procedures inherit central error mapping and logger middleware from `baseProcedure`
- [ ] Request input logged at `debug` level only (not in production)

### Operational Events
- [ ] Services log significant business events at `info` level
- [ ] Operational events use `otel.event.name` with a stable dot-separated value
- [ ] Entity identifiers use registered semantic attributes when available (for example, `user.id`)
- [ ] Auth events follow standard naming (`user.logged_in`, `user.registered`, etc.)
- [ ] Message is past tense, concise ("User logged in", not "A user has logged in")

### Error Logging
- [ ] Error handler logs known errors at `warn` with `error.type` and safe details
- [ ] Correlation fields come from `AppLogger`; callers do not pass them manually
- [ ] Error handler logs unknown errors at `error` with full stack
- [ ] Error message used as log message (not generic text)

### Layer Rules
- [ ] Routers: No logging (handled by middleware)
- [ ] Services: Log business events
- [ ] Repositories: No logging
- [ ] Use cases: Log orchestration outcomes when they own the business action
- [ ] No service/use case imports the concrete logger
- [ ] Product analytics is emitted through `ProductAnalytics`, never through `AppLogger`

## Standards References

- [OpenTelemetry Logs Data Model](https://opentelemetry.io/docs/specs/otel/logs/data-model/)
- [Trace Context in non-OTLP Log Formats](https://opentelemetry.io/docs/specs/otel/compatibility/logging_trace_context/)
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [OpenTelemetry Attribute Naming](https://opentelemetry.io/docs/specs/semconv/general/naming/)
