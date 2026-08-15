# Node.js Library Documentation

Library-level documentation for Node.js runtime integrations.

Libraries are adapters. They may depend on Node.js and vendor SDKs, but controllers, domain services, and use cases depend only on their ports. A library integration must preserve the shared contracts, central error policy, observability scope, controller boundary, and transaction boundary defined in `server/core/`.

- [OpenAPI Integration](./openapi/README.md)
- [OpenAPI Parity Testing](./openapi/parity-testing.md)
- [Pino Logger Adapter](./pino/README.md)
- [tRPC Integration](./trpc/integration.md)
- [tRPC Rate Limiting](./trpc/rate-limiting.md)
- [tRPC Authentication](./trpc/authentication.md)
- [Supabase](./supabase/README.md)
