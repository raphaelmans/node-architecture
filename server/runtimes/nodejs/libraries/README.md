# Node.js Library Documentation

Library-level documentation for Node.js runtime integrations.

Libraries are adapters. They may depend on Node.js and vendor SDKs, but controllers, domain services, and use cases depend only on their ports. A library integration must preserve the shared contracts, central error policy, observability scope, controller boundary, and transaction boundary defined in `server/core/`.

Application-owned capabilities use that flow. Provider-native authentication/plugin endpoints follow the core [native-handler boundary](../../../core/controllers.md#provider-managed-endpoints) and preserve their protocol rather than adopting the business envelope.

- [OpenAPI Integration](./openapi/README.md)
- [OpenAPI Parity Testing](./openapi/parity-testing.md)
- [Pino Logger Adapter](./pino/README.md)
- [tRPC Integration](./trpc/integration.md)
- [tRPC Rate Limiting](./trpc/rate-limiting.md)
- [tRPC Authentication](./trpc/authentication.md)
- [Supabase](./supabase/README.md)
- [Supabase Data Access](./supabase/data-access.md)
- [Drizzle Repository Convention](./drizzle/README.md)
- [Better Auth Integration Convention](./better-auth/README.md)

Better Auth, Drizzle, and Supabase are independent choices. Load only the selected integrations; Better Auth + Drizzle needs no Supabase layer. Database hosting, authentication, and business-data access need not use the same adapter.
