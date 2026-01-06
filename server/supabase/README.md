# Supabase Integration

> Vendor-specific documentation for integrating Supabase with the layered backend architecture.

## Overview

This folder contains patterns for integrating Supabase services while maintaining the core architecture principles.

## Documentation

| Document                        | Description                          |
| ------------------------------- | ------------------------------------ |
| [Integration](./integration.md) | Auth, Storage, and Database patterns |

## Quick Reference

### Service Mapping

| Supabase Service | Architecture Layer   | Pattern                   |
| ---------------- | -------------------- | ------------------------- |
| Auth             | Repository → Service | Direct Supabase client    |
| Storage          | Adapter → Service    | Interface abstraction     |
| Database         | Repository (Drizzle) | Not using Supabase client |

### Key Files

```
shared/infra/
├── supabase/
│   ├── create-client.ts       # Supabase client factory
│   ├── object-storage.ts      # Storage adapter
│   └── database.types.ts      # Generated types
├── db/
│   └── drizzle.ts             # Drizzle client (uses Supabase Postgres)
└── services/
    └── storage-client.ts      # Path-scoped storage operations

modules/auth/
├── repositories/
│   └── auth.repository.ts     # Supabase Auth wrapper
└── services/
    └── auth.service.ts        # Auth business logic
```

### Usage

```typescript
// In tRPC context or route handler
const services = new ServiceProvider(cookies);

// Auth
const user = await services.AuthService().getCurrentUser();

// Storage
await services.ObjectStorage().ProfileImages().uploadFile(blob, "avatar.jpg");

// Database (via Drizzle, not Supabase client)
const profile = await services.ProfileService().findByUserId(user.id);
```

## Core Principles Applied

1. **Auth Repository** - Wraps Supabase Auth, no business logic
2. **Storage Adapter** - Implements `ObjectStorage` interface, vendor-replaceable
3. **Database via Drizzle** - Uses Supabase Postgres, but through Drizzle ORM
4. **Service Provider** - Manages Supabase client lifecycle with cookies
