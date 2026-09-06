# Supabase Integration

> Vendor-specific documentation for integrating Supabase with the layered backend architecture.

## Overview

This folder contains patterns for integrating Supabase services while maintaining the core architecture principles.

## Documentation

| Document | Description |
|----------|-------------|
| [Authentication](./auth.md) | Complete auth implementation with tRPC, user roles, middleware |
| [Integration](./integration.md) | Auth, Storage, and Database patterns (overview) |
| [Data Access Convention](./data-access.md) | Direct repositories, atomic database functions, security, and coexistence with Drizzle |

The [data-access convention](./data-access.md) owns persistence selection. Older examples below and in the auth/integration guides demonstrate a Drizzle-backed application; they do not require Drizzle for Supabase-only repositories. Resolve exact installation, configuration, SDK, key, and migration details from current version-applicable [Supabase docs](https://supabase.com/docs).

## Quick Reference

### Service Mapping

| Supabase Service | Architecture Layer | Pattern |
|------------------|-------------------|---------|
| Auth | Controller → Service/Use Case → Repository | Request-scoped controller factories |
| Storage | Controller → Use Case → Provider adapter | Interface abstraction + compensating workflow |
| Database | Application-owned repository contract | Direct Supabase SDK/data API, or independently selected Drizzle |

### Key Files

This is the combined Drizzle + Supabase example. In a Supabase-only application, omit ORM infrastructure and use direct repositories plus database functions where atomicity requires them.

```
shared/infra/
├── supabase/
│   ├── create-client.ts       # Supabase client factory (SSR)
│   ├── object-storage.ts      # Storage adapter
│   └── types.ts               # SupabaseClient type export
├── db/
│   ├── drizzle.ts             # Drizzle client (uses Supabase Postgres)
│   └── schema/
│       └── user-roles.ts      # user_roles linked to auth.users
└── trpc/
    └── context.ts             # Session extraction from Supabase

modules/
├── auth/
│   ├── controllers/
│   │   └── <capability>.controller.ts # Framework-neutral public boundary
│   ├── repositories/
│   │   └── auth.repository.ts # Supabase Auth wrapper
│   ├── services/
│   │   └── auth.service.ts    # Auth business logic
│   ├── use-cases/
│   │   ├── complete-signup.use-case.ts # Verified, idempotent local provisioning
│   │   └── provision-managed-user.use-case.ts # Trusted flow with compensation
│   ├── factories/
│   │   └── auth.factory.ts    # Request-scoped factories
│   └── auth.router.ts         # tRPC endpoints
└── user-role/
    └── ...                    # Application-level roles in DB
```

### Usage

```typescript
// In tRPC router
const authRouter = router({
  login: publicProcedure
    .input(LoginInputSchema)
    .mutation(async ({ input, ctx }) => {
      // Request-scoped outer factory; controller owns public mapping.
      const result = await makeLoginController(ctx.cookies).execute(input);
      return wrapResponse(LoginResponseSchema.parse(result));
    }),

  me: protectedProcedure
    .query(async ({ ctx }) => {
      const result = await makeCurrentSessionController(ctx.cookies)
        .execute(toActor(ctx.session));
      const response = CurrentSessionResponseSchema.parse(result);
      return wrapResponse(response);
    }),
});
```

## Core Principles Applied

1. **Auth Repository** - Wraps Supabase Auth, maps errors to domain errors
2. **Request-Scoped Controller Factories** - Framework adapters resolve controllers whose inward graph contains cookie-bound Supabase adapters
3. **User Roles in DB** - Application roles separate from Supabase auth
4. **Session in Context** - tRPC context extracts and enriches session
5. **Storage Adapter** - Implements `ObjectStorage` interface, vendor-replaceable
6. **Independent Persistence Choice** - Use direct Supabase repositories or Drizzle; neither is a prerequisite for the other

## Environment Variables

For Next.js, define these values in the validated
[environment boundary](../../metaframeworks/nextjs/environment-variables.md)
and inject narrow configuration through runtime factories. This block documents
deployment names only; ordinary application code should not read `process.env`
directly.

```bash
# Public (safe to expose)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx

# Server-only (NEVER expose)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx
SUPABASE_SECRET_KEY=sb_secret_xxx

# Database connection only when a SQL adapter or migration tool needs it
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

Request-scoped user/session clients use `SUPABASE_PUBLISHABLE_KEY`. The secret
key is read only by a separately named privileged client used for narrowly
authorized admin/worker operations; it is never the default server client.
