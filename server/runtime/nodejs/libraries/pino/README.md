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
      "authorization",
      "cookie",
      "*.password",
      "*.token",
      "*.authorization",
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

## Checklist

- [ ] Pino is imported only by infrastructure
- [ ] `appLogger` is typed as `AppLogger`
- [ ] Production output is structured JSON
- [ ] Development pretty printing is optional and disabled in production
- [ ] Secrets and nested sensitive fields are redacted
- [ ] Errors use the standard error serializer
- [ ] Resource identity is stable
- [ ] Active request/trace context is merged into every method
- [ ] Adapter failure cannot change business behavior

## Related Guides

- [Core Logging](../../../../core/logging.md)
- [Observability](../../../../core/observability.md)
- [tRPC Integration](../trpc/integration.md)
- [Next.js Route Handlers](../../metaframeworks/nextjs/route-handlers.md)
