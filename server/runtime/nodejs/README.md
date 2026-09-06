# Node.js Runtime Documentation

For Express, Hono, or other Node.js HTTP server startup, use [Node.js Local Development](../../../development/runtimes/nodejs/README.md). It coordinates assigned listener configuration, optional self-origins, and same-checkout frontend/API targets while preserving server architecture ownership.

Node.js runtime-specific documentation layered on top of `server/core/`.

Node.js supplies the concrete execution environment for async observability context, database clients, logger adapters, and transport libraries. It inherits the layer boundaries, contracts, error kinds, transaction rules, and DI rules from [Core](../../core/README.md).

```text
Next.js / Express / Hono / tRPC / OpenAPI adapter
          ↓
module-owned framework-neutral controller
          ↓
use case OR service

kernel/application ports
          ↑ implemented by
Node.js infrastructure and vendor adapters
```

No Node.js adapter may be imported by client code or by browser-safe shared contracts.

## Scaffolding

- [Node.js Scaffolding](./scaffolding.md) implements the runtime-agnostic core contract for existing Node.js repositories.
- Its Next.js, Express, and Hono adapter guides are known specializations, not an allowlist.

## Libraries

- [Libraries Index](./libraries/README.md)
- [tRPC Integration](./libraries/trpc/integration.md)
- [OpenAPI Integration](./libraries/openapi/README.md)
- [OpenAPI Parity Testing](./libraries/openapi/parity-testing.md)
- [Pino Logger Adapter](./libraries/pino/README.md)
- [tRPC Rate Limiting](./libraries/trpc/rate-limiting.md)
- [tRPC Authentication](./libraries/trpc/authentication.md)
- [Supabase](./libraries/supabase/README.md)

## Framework Adapters

- [Framework Adapter Index](./metaframeworks/README.md)
- [Next.js](./metaframeworks/nextjs/README.md)
- [Express](./metaframeworks/express/README.md)
- [Hono](./metaframeworks/hono/README.md)
- [NestJS](./metaframeworks/nestjs/README.md)

## Runtime Checklist

- Concrete adapters implement kernel/application ports.
- Public framework adapters resolve and call one framework-neutral controller.
- Request observability scope is established before application code.
- `TransactionContext` remains database-only.
- Transport errors are derived centrally from `AppError.kind`.
- Composition roots/factories are the only cross-layer construction points.
