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
- [Supabase Data Access](./supabase/data-access.md)
- [Drizzle Repository Convention](./drizzle/README.md)

Drizzle and Supabase are independent choices. Use one or both only for the selected stack; database hosting, authentication, and business-data access need not use the same adapter.
