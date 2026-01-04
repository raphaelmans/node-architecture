# Logging Architecture

> **Purpose**: This document defines the logging conventions, configuration, and patterns across the application.

---

## 1. Overview

**Principles:**

- Structured JSON logging for machine parsing
- Human-readable output in development
- Request correlation via `requestId`
- Sensitive data redaction
- Log at appropriate levels and layers

**Library:** pino

---

## 2. Logger Configuration

```typescript
// shared/infra/logger/index.ts

import pino from 'pino';

const isProduction = process.env.NODE_ENV === 'production';

export const logger = pino({
  level: process.env.LOG_LEVEL ?? (isProduction ? 'info' : 'debug'),

  // Pretty print in development
  transport: isProduction
    ? undefined
    : {
        target: 'pino-pretty',
        options: {
          colorize: true,
          translateTime: 'SYS:standard',
          ignore: 'pid,hostname',
        },
      },

  // Redact sensitive fields
  redact: {
    paths: [
      'password',
      'passwordHash',
      'token',
      'accessToken',
      'refreshToken',
      'authorization',
      'cookie',
      'creditCard',
      'cardNumber',
      'cvv',
      'ssn',
      '*.password',
      '*.passwordHash',
      '*.token',
      '*.accessToken',
      '*.refreshToken',
      '*.authorization',
      '*.creditCard',
      '*.cardNumber',
      '*.cvv',
      '*.ssn',
    ],
    censor: '[REDACTED]',
  },

  // Base context for all logs
  base: {
    env: process.env.NODE_ENV,
    service: process.env.SERVICE_NAME ?? 'api',
  },
});

export type Logger = typeof logger;
```

---

## 3. Request Logger (Child Logger)

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
  method: 'POST',
  path: '/api/users',
});

log.info('Processing request');
// Output: { "requestId": "abc-123", "userId": "usr-456", "method": "POST", "path": "/api/users", "msg": "Processing request" }
```

---

## 4. Log Levels

| Level | When to Use | Examples |
|-------|-------------|----------|
| `error` | Unexpected failures, unhandled exceptions | Unknown errors, system failures |
| `warn` | Expected errors, recoverable issues | Known application errors, deprecations |
| `info` | Request lifecycle, business events | Request start/end, user created |
| `debug` | Development details, verbose data | Input/output bodies, intermediate state |

```typescript
log.error({ err }, 'Unexpected database failure');
log.warn({ code: 'USER_NOT_FOUND', userId }, 'User not found');
log.info({ userId: user.id }, 'User created');
log.debug({ input }, 'Request input');
```

---

## 5. What to Log by Layer

| Layer | Log | Level |
|-------|-----|-------|
| Router/Middleware | Request start, end, duration, status | `info` |
| Router/Middleware | Request input (in development) | `debug` |
| Error Handler | Known application errors | `warn` |
| Error Handler | Unknown/unexpected errors | `error` |
| Services | Significant business events | `info` |
| Repositories | Nothing | — |

---

## 6. Request Lifecycle Logging

### tRPC Middleware

```typescript
// shared/infra/trpc/middleware/logger.middleware.ts

import { middleware } from '../trpc';
import { createRequestLogger } from '@/shared/infra/logger';

export const loggerMiddleware = middleware(async ({ ctx, next, path, type }) => {
  const start = Date.now();

  const log = createRequestLogger({
    requestId: ctx.requestId,
    userId: ctx.userId,
    method: type,
    path,
  });

  log.info('Request started');

  // Log input at debug level only
  if (ctx.input) {
    log.debug({ input: ctx.input }, 'Request input');
  }

  try {
    const result = await next({ ctx: { ...ctx, log } });
    const duration = Date.now() - start;

    log.info({ duration, status: 'success' }, 'Request completed');

    return result;
  } catch (error) {
    const duration = Date.now() - start;

    log.info({ duration, status: 'error' }, 'Request failed');

    throw error;
  }
});
```

### Apply to Procedures

```typescript
// shared/infra/trpc/trpc.ts

const t = initTRPC.context<Context>().create({ /* ... */ });

const loggedProcedure = t.procedure.use(loggerMiddleware);

export const publicProcedure = loggedProcedure;
export const protectedProcedure = loggedProcedure.use(authMiddleware);
```

---

## 7. Service-Level Business Events

Log significant business events in services.

```typescript
// modules/user/services/user.service.ts

import { logger } from '@/shared/infra/logger';

export class UserService implements IUserService {
  constructor(
    private userRepository: IUserRepository,
    private transactionManager: TransactionManager,
  ) {}

  async create(data: UserInsert): Promise<User> {
    const user = await this.transactionManager.run(async (tx) => {
      const existing = await this.userRepository.findByEmail(data.email, { tx });
      if (existing) {
        throw new UserEmailConflictError(data.email);
      }

      return this.userRepository.create(data, { tx });
    });

    // Business event: user created
    logger.info(
      { 
        event: 'user.created', 
        userId: user.id, 
        email: user.email,
      },
      'User created',
    );

    return user;
  }

  async delete(id: string): Promise<void> {
    await this.transactionManager.run(async (tx) => {
      await this.userRepository.findByIdOrThrow(id, { tx });
      await this.userRepository.delete(id, { tx });
    });

    // Business event: user deleted
    logger.info(
      { 
        event: 'user.deleted', 
        userId: id,
      },
      'User deleted',
    );
  }
}
```

### Business Event Naming Convention

Use past tense, dot-separated format:

```
<entity>.<action>
```

**Examples:**

| Event | Description |
|-------|-------------|
| `user.created` | New user registered |
| `user.updated` | User profile updated |
| `user.deleted` | User account deleted |
| `workspace.created` | New workspace created |
| `workspace.member.added` | Member added to workspace |
| `workspace.member.removed` | Member removed from workspace |
| `payment.processed` | Payment completed |
| `payment.failed` | Payment failed |

---

## 8. Error Logging

Errors are logged by the error handler (see Error Handling Architecture).

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
  'Unexpected error',
);
```

---

## 9. Request Context Integration

### Request ID Generation

Generate UUID at the tRPC context creation.

```typescript
// shared/infra/trpc/context.ts

import { randomUUID } from 'crypto';

export async function createContext({ req }: { req: Request }) {
  const requestId = req.headers.get('x-request-id') ?? randomUUID();

  return {
    requestId,
    userId: undefined, // Set by auth middleware
  };
}

export type Context = Awaited<ReturnType<typeof createContext>>;
```

### RequestContext Type

```typescript
// shared/kernel/context.ts

import { TransactionContext } from './transaction';

export interface RequestContext {
  requestId: string;
  traceId?: string;   // Future: OpenTelemetry
  spanId?: string;    // Future: OpenTelemetry
  tx?: TransactionContext;
}
```

---

## 10. Sensitive Data Handling

### Automatic Redaction

Pino's `redact` option handles common sensitive fields automatically.

### Manual Sanitization

For cases where you need to log objects that might contain sensitive data:

```typescript
// shared/utils/sanitize.ts

const SENSITIVE_KEYS = [
  'password',
  'token',
  'authorization',
  'creditcard',
  'cardnumber',
  'cvv',
  'ssn',
  'secret',
];

export function sanitize<T extends Record<string, unknown>>(obj: T): T {
  const result = { ...obj };

  for (const key of Object.keys(result)) {
    const lowerKey = key.toLowerCase();
    if (SENSITIVE_KEYS.some((sensitive) => lowerKey.includes(sensitive))) {
      (result as Record<string, unknown>)[key] = '[REDACTED]';
    }
  }

  return result;
}
```

**Usage:**

```typescript
log.debug({ data: sanitize(requestBody) }, 'Processing data');
```

---

## 11. Log Output Examples

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

---

## 12. Future: Observability

When ready for full observability, extend with:

### OpenTelemetry Integration

```typescript
// Future: Add tracing context
export interface RequestContext {
  requestId: string;
  traceId: string;    // W3C Trace Context
  spanId: string;
  tx?: TransactionContext;
}

// Future: Export to observability platform
// - Traces → Jaeger, Tempo, Datadog
// - Metrics → Prometheus, Datadog
// - Logs → Loki, CloudWatch, Datadog
```

---

## 13. Checklist

- [ ] Pino configured with appropriate log level
- [ ] Pretty printing enabled in development
- [ ] Sensitive fields redacted via pino config
- [ ] Request logger creates child logger with `requestId`
- [ ] Request ID generated at context creation
- [ ] Logger middleware logs request lifecycle
- [ ] Request input logged at `debug` level only
- [ ] Services log significant business events at `info` level
- [ ] Business events use `<entity>.<action>` naming convention
- [ ] Error handler logs known errors at `warn`, unknown at `error`
- [ ] Repositories do not log
