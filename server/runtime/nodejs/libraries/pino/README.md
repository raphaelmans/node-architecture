# Pino Logger Adapter (Node.js)

> Node.js implementation of the runtime-agnostic [`AppLogger`](../../../../core/logging.md) contract.

## Boundary

- Pino stays in `shared/infra/logger/`.
- Services and use cases depend on `AppLogger`, never Pino types.
- The adapter reads active observability context and adds correlation after caller fields.
- The composition root exports the `AppLogger` instance used by module factories.

## Configuration

```typescript
// shared/infra/logger/index.ts

import pino from "pino";
import type { AppLogger } from "@/shared/kernel/logger";
import { PinoAppLogger } from "./pino-app-logger";

const isProduction = process.env.NODE_ENV === "production";

const pinoLogger = pino({
  level: process.env.LOG_LEVEL ?? (isProduction ? "info" : "debug"),
  transport: isProduction
    ? undefined
    : {
        target: "pino-pretty",
        options: { colorize: true, translateTime: "SYS:standard" },
      },
  redact: {
    paths: [
      "password",
      "passwordHash",
      "token",
      "accessToken",
      "refreshToken",
      "apiKey",
      "secret",
      "authorization",
      "cookie",
      "req.headers.authorization",
      "req.headers.cookie",
      "request.headers.authorization",
      "request.headers.cookie",
      "res.headers.set-cookie",
      "response.headers.set-cookie",
      "*.password",
      "*.token",
      "*.accessToken",
      "*.refreshToken",
      "*.apiKey",
      "*.secret",
      "*.authorization",
      "*.cookie",
      "*.*.password",
      "*.*.token",
      "*.*.accessToken",
      "*.*.refreshToken",
      "*.*.authorization",
    ],
    censor: "[REDACTED]",
  },
  serializers: { err: pino.stdSerializers.err },
  base: {
    "deployment.environment.name": process.env.NODE_ENV,
    "service.name": process.env.SERVICE_NAME ?? "api",
  },
});

export const appLogger: AppLogger = new PinoAppLogger(pinoLogger);
```

## Adapter

```typescript
// shared/infra/logger/pino-app-logger.ts

export class PinoAppLogger implements AppLogger {
  constructor(private readonly logger: pino.Logger) {}

  info(fields: LogFields, message: string): void {
    const context = getObservabilityContext();

    try {
      this.logger.info(
        {
          ...fields,
          trace_id: context?.traceId,
          span_id: context?.spanId,
          trace_flags: context?.traceFlags,
          [APP_ATTRIBUTES.requestId]: context?.requestId,
        },
        message,
      );
    } catch {
      // Logging must not change application behavior.
    }
  }

  // debug, warn, and error use the same enrichment order.
}
```

Correlation is written after caller fields so application code cannot spoof trusted IDs. Configure equivalent enrichment and redaction for every method.

Redaction is defense in depth, not permission to log entire request, session, or
provider objects. Prefer allowlisted log fields. Add a redaction path whenever a
new credential shape is introduced, and keep regression fixtures for root,
header, one-level, and two-level nesting.

```typescript
it.each([
  { password: "secret" },
  { req: { headers: { authorization: "Bearer secret" } } },
  { session: { refreshToken: "secret" } },
  { provider: { credentials: { accessToken: "secret" } } },
])("redacts credential-shaped fields", (fields) => {
  appLogger.info(fields, "Redaction test");
  expect(testDestination.lastLine()).not.toContain("secret");
});
```

## Checklist

- [ ] Pino is imported only by infrastructure
- [ ] `appLogger` is typed as `AppLogger`
- [ ] Production output is structured JSON
- [ ] Development pretty printing is optional and disabled in production
- [ ] Secrets and nested sensitive fields are redacted
- [ ] Redaction tests cover nested headers and token objects
- [ ] Logs use allowlisted fields rather than full request/session objects
- [ ] Errors use the standard error serializer
- [ ] Resource identity is stable
- [ ] Active request/trace context is merged into every method
- [ ] Adapter failure cannot change business behavior

## Related Guides

- [Core Logging](../../../../core/logging.md)
- [Observability](../../../../core/observability.md)
- [tRPC Integration](../trpc/integration.md)
- [Next.js Route Handlers](../../metaframeworks/nextjs/route-handlers.md)
