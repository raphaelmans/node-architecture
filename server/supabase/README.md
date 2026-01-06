# Supabase Integration

> Vendor-specific documentation for integrating Supabase with the layered backend architecture.

## Overview

This folder contains patterns for integrating Supabase services while maintaining the core architecture principles.

## Documentation

| Document | Description |
|----------|-------------|
| [Authentication](./auth.md) | Complete auth implementation with tRPC, user roles, middleware |
| [Integration](./integration.md) | Auth, Storage, and Database patterns (overview) |

## Quick Reference

### Service Mapping

| Supabase Service | Architecture Layer | Pattern |
|------------------|-------------------|---------|
| Auth | Repository → Service → Use Case | Request-scoped factories |
| Storage | Adapter → Service | Interface abstraction |
| Database | Repository (Drizzle) | Not using Supabase client |

### Key Files

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
│   ├── repositories/
│   │   └── auth.repository.ts # Supabase Auth wrapper
│   ├── services/
│   │   └── auth.service.ts    # Auth business logic
│   ├── use-cases/
│   │   └── register-user.use-case.ts # Multi-service orchestration
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
    .input(LoginSchema)
    .mutation(async ({ input, ctx }) => {
      // Request-scoped factory with cookies
      const authService = makeAuthService(ctx.cookies);
      return authService.signIn(input.email, input.password);
    }),

  me: protectedProcedure
    .query(async ({ ctx }) => {
      // Session already extracted in context
      return {
        id: ctx.session.userId,
        email: ctx.session.email,
        role: ctx.session.role,
      };
    }),
});
```

## Core Principles Applied

1. **Auth Repository** - Wraps Supabase Auth, maps errors to domain errors
2. **Request-Scoped Factories** - Auth factories accept cookies for SSR
3. **User Roles in DB** - Application roles separate from Supabase auth
4. **Session in Context** - tRPC context extracts and enriches session
5. **Storage Adapter** - Implements `ObjectStorage` interface, vendor-replaceable
6. **Database via Drizzle** - Uses Supabase Postgres through Drizzle ORM

## Environment Variables

```bash
# Public (safe to expose)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx

# Server-only (NEVER expose)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=sb_secret_xxx

# Database
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```
