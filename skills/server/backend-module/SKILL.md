---
name: backend-module
description: Creates new backend modules with repository, service, factory, router, DTOs, and errors. Use when adding a new domain entity/resource to the system, creating a new module, or when the user mentions "new module", "add entity", "create resource", or "scaffold module".
---

# Creating a New Backend Module

## Overview

A module encapsulates a domain entity with all its layers. Follow this architecture:

```
src/modules/<module>/
├── <module>.router.ts      # tRPC router (HTTP concerns)
├── dtos/                   # Input/output schemas (Zod)
├── errors/                 # Domain-specific errors
├── factories/              # Dependency creation
├── services/               # Business logic
└── repositories/           # Data access
```

## Step-by-Step Process

### 1. Define Database Schema

Add table definition to `shared/infra/db/schema.ts`:

```typescript
import { pgTable, uuid, text, timestamp } from 'drizzle-orm/pg-core';
import { createSelectSchema, createInsertSchema } from 'drizzle-zod';

export const <entities> = pgTable('<entities>', {
  id: uuid('id').primaryKey().defaultRandom(),
  // ... fields
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

export const <Entity>Schema = createSelectSchema(<entities>);
export type <Entity> = z.infer<typeof <Entity>Schema>;

export const <Entity>InsertSchema = createInsertSchema(<entities>).omit({ id: true });
export type <Entity>Insert = z.infer<typeof <Entity>InsertSchema>;
```

### 2. Create Domain Errors

```typescript
// modules/<module>/errors/<module>.errors.ts
import { NotFoundError, ConflictError, BusinessRuleError } from '@/shared/kernel/errors';

export class <Entity>NotFoundError extends NotFoundError {
  readonly code = '<ENTITY>_NOT_FOUND';
  constructor(<entity>Id: string) {
    super('<Entity> not found', { <entity>Id });
  }
}
```

### 3. Create Repository

```typescript
// modules/<module>/repositories/<module>.repository.ts
import { eq } from 'drizzle-orm';
import { <entities>, <Entity>, <Entity>Insert } from '@/shared/infra/db/schema';
import type { RequestContext } from '@/shared/kernel/context';
import type { DbClient, DrizzleTransaction } from '@/shared/infra/db/types';

export interface I<Entity>Repository {
  findById(id: string, ctx?: RequestContext): Promise<<Entity> | null>;
  create(data: <Entity>Insert, ctx?: RequestContext): Promise<<Entity>>;
}

export class <Entity>Repository implements I<Entity>Repository {
  constructor(private db: DbClient) {}

  private getClient(ctx?: RequestContext): DbClient | DrizzleTransaction {
    return (ctx?.tx as DrizzleTransaction) ?? this.db;
  }

  async findById(id: string, ctx?: RequestContext): Promise<<Entity> | null> {
    const client = this.getClient(ctx);
    const result = await client
      .select()
      .from(<entities>)
      .where(eq(<entities>.id, id))
      .limit(1);
    return result[0] ?? null;
  }

  async create(data: <Entity>Insert, ctx?: RequestContext): Promise<<Entity>> {
    const client = this.getClient(ctx);
    const result = await client
      .insert(<entities>)
      .values(data)
      .returning();
    return result[0];
  }
}
```

### 4. Create Service

```typescript
// modules/<module>/services/<module>.service.ts
import type { TransactionManager } from '@/shared/kernel/transaction';
import type { RequestContext } from '@/shared/kernel/context';
import type { I<Entity>Repository } from '../repositories/<module>.repository';
import { <Entity>, <Entity>Insert } from '@/shared/infra/db/schema';

export interface I<Entity>Service {
  findById(id: string, ctx?: RequestContext): Promise<<Entity> | null>;
  create(data: <Entity>Insert, ctx?: RequestContext): Promise<<Entity>>;
}

export class <Entity>Service implements I<Entity>Service {
  constructor(
    private <entity>Repository: I<Entity>Repository,
    private transactionManager: TransactionManager,
  ) {}

  async findById(id: string, ctx?: RequestContext): Promise<<Entity> | null> {
    return this.<entity>Repository.findById(id, ctx);
  }

  async create(data: <Entity>Insert, ctx?: RequestContext): Promise<<Entity>> {
    if (ctx?.tx) {
      return this.createInternal(data, ctx);
    }
    return this.transactionManager.run((tx) => this.createInternal(data, { tx }));
  }

  private async createInternal(data: <Entity>Insert, ctx: RequestContext): Promise<<Entity>> {
    // Add business validation here
    return this.<entity>Repository.create(data, ctx);
  }
}
```

### 5. Create Factory

```typescript
// modules/<module>/factories/<module>.factory.ts
import { getContainer } from '@/shared/infra/container';
import { <Entity>Repository } from '../repositories/<module>.repository';
import { <Entity>Service } from '../services/<module>.service';

let <entity>Repository: <Entity>Repository | null = null;
let <entity>Service: <Entity>Service | null = null;

export function make<Entity>Repository() {
  if (!<entity>Repository) {
    <entity>Repository = new <Entity>Repository(getContainer().db);
  }
  return <entity>Repository;
}

export function make<Entity>Service() {
  if (!<entity>Service) {
    <entity>Service = new <Entity>Service(
      make<Entity>Repository(),
      getContainer().transactionManager,
    );
  }
  return <entity>Service;
}
```

### 6. Create DTOs

```typescript
// modules/<module>/dtos/create-<entity>.dto.ts
import { z } from 'zod';

export const Create<Entity>Schema = z.object({
  // Define input fields (exclude id, timestamps)
});

export type Create<Entity>DTO = z.infer<typeof Create<Entity>Schema>;
```

### 7. Create Router

```typescript
// modules/<module>/<module>.router.ts
import { router, protectedProcedure } from '@/shared/infra/trpc';
import { z } from 'zod';
import { make<Entity>Service } from './factories/<module>.factory';
import { wrapResponse } from '@/shared/utils/response';
import { <Entity>NotFoundError } from './errors/<module>.errors';
import { Create<Entity>Schema } from './dtos/create-<entity>.dto';

export const <module>Router = router({
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input }) => {
      const <entity> = await make<Entity>Service().findById(input.id);
      if (!<entity>) {
        throw new <Entity>NotFoundError(input.id);
      }
      return wrapResponse(<entity>);
    }),

  create: protectedProcedure
    .input(Create<Entity>Schema)
    .mutation(async ({ input }) => {
      const <entity> = await make<Entity>Service().create(input);
      return wrapResponse(<entity>);
    }),
});
```

### 8. Register Router

Add to root router in `shared/infra/trpc/root.ts`:

```typescript
import { <module>Router } from '@/modules/<module>/<module>.router';

export const appRouter = router({
  // ... existing routers
  <module>: <module>Router,
});
```

## Key Rules

| Rule | Description |
|------|-------------|
| Router handles null | Service returns null, router throws NotFoundError |
| Service owns transactions | For single-service writes without external ctx |
| Repository never creates tx | Only receives ctx?.tx |
| Factories are lazy singletons | Reuse during serverless warm starts |
| DTOs for API contracts | Entities for internal use |

See [references/layer-patterns.md](references/layer-patterns.md) for detailed patterns.

---

## Module Checklist

Use this checklist for EVERY new module to ensure nothing is missed.

### Errors (`errors/<module>.errors.ts`)
- [ ] Each error class extends appropriate base (`NotFoundError`, `ConflictError`, etc.)
- [ ] Each error class has unique `readonly code = '<MODULE>_<ERROR_TYPE>'`
- [ ] Error code uses SCREAMING_SNAKE_CASE
- [ ] Constructor passes entity ID to details: `super('Message', { entityId })`
- [ ] Error messages are user-safe (no internal details)

```typescript
// CORRECT
export class EntityNotFoundError extends NotFoundError {
  readonly code = 'ENTITY_NOT_FOUND';  // REQUIRED: unique code
  constructor(entityId: string) {
    super('Entity not found', { entityId });
  }
}

// WRONG - missing code property
export class EntityNotFoundError extends NotFoundError {
  constructor(entityId: string) {
    super('Entity not found', { entityId });
  }
}
```

### Repository (`repositories/<module>.repository.ts`)
- [ ] Interface `I<Entity>Repository` defined with all method signatures
- [ ] Class implements the interface: `class <Entity>Repository implements I<Entity>Repository`
- [ ] Constructor accepts `DbClient`
- [ ] `getClient(ctx)` helper returns `ctx?.tx ?? this.db`
- [ ] All methods accept `ctx?: RequestContext`
- [ ] Returns `null` for not found (never throws NotFoundError)
- [ ] No logging in repository layer
- [ ] No business logic in repository

### Service (`services/<module>.service.ts`)
- [ ] Interface `I<Entity>Service` defined with all method signatures
- [ ] Class implements the interface: `class <Entity>Service implements I<Entity>Service`
- [ ] Constructor accepts interface types (not concrete): `I<Entity>Repository`
- [ ] Constructor accepts `TransactionManager`
- [ ] Read methods pass through `ctx` to repository
- [ ] Write methods check `ctx?.tx` - participate if exists, else create own transaction
- [ ] Business events logged with `logger.info({ event: '<entity>.<action>', ... }, 'Message')`
- [ ] Event names use `<entity>.<past_tense_action>` format
- [ ] Returns `null` for not found (router handles throwing)

### Factory (`factories/<module>.factory.ts`)
- [ ] Lazy singleton pattern for standard modules (DB-backed)
- [ ] Request-scoped pattern for modules needing request context (cookies, etc.)
- [ ] Returns interface type, not concrete class
- [ ] Uses `getContainer()` for shared dependencies

### DTOs (`dtos/`)
- [ ] Zod schemas for all inputs
- [ ] `export type <Name>DTO = z.infer<typeof <Name>Schema>`
- [ ] Index file exports all DTOs
- [ ] Validation rules match business requirements

### Router (`<module>.router.ts`)
- [ ] Uses `publicProcedure` or `protectedProcedure` (both include logging)
- [ ] Input validated with `.input(ZodSchema)`
- [ ] Calls factory to get service: `make<Entity>Service()`
- [ ] Handles null returns by throwing domain error: `if (!entity) throw new EntityNotFoundError(id)`
- [ ] No business logic in router (delegate to service/use-case)
- [ ] No direct logging (handled by middleware)

### Root Router Registration
- [ ] Router imported in `shared/infra/trpc/root.ts`
- [ ] Router added to `appRouter`

### Final Verification
- [ ] TypeScript compiles without errors
- [ ] All interfaces have implementations
- [ ] All error classes have unique codes
- [ ] Business events logged in service layer
- [ ] No logging in repository layer
