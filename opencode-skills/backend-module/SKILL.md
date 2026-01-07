---
name: backend-module
description: Create new backend modules with layered architecture (repository, service, factory, router, DTOs, errors) for Next.js + tRPC + Drizzle projects
---

# Creating a New Backend Module

Use this skill when adding a new domain entity/resource to the system. This creates a complete module with all architectural layers.

## Architecture

```
src/modules/<module>/
├── <module>.router.ts      # tRPC router (HTTP concerns)
├── dtos/                   # Input/output schemas (Zod)
├── errors/                 # Domain-specific errors
├── factories/              # Dependency creation
├── services/               # Business logic
└── repositories/           # Data access
```

## Step-by-Step

### 1. Database Schema

Add to `shared/infra/db/schema.ts`:

```typescript
import { pgTable, uuid, text, timestamp } from 'drizzle-orm/pg-core'
import { createSelectSchema, createInsertSchema } from 'drizzle-zod'

export const entities = pgTable('entities', {
  id: uuid('id').primaryKey().defaultRandom(),
  name: text('name').notNull(),
  // ... fields
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

export const EntitySchema = createSelectSchema(entities)
export type Entity = z.infer<typeof EntitySchema>

export const EntityInsertSchema = createInsertSchema(entities).omit({ id: true })
export type EntityInsert = z.infer<typeof EntityInsertSchema>
```

### 2. Domain Errors

```typescript
// modules/<module>/errors/<module>.errors.ts
import { NotFoundError, ConflictError, BusinessRuleError } from '@/shared/kernel/errors'

export class EntityNotFoundError extends NotFoundError {
  readonly code = 'ENTITY_NOT_FOUND'
  constructor(entityId: string) {
    super('Entity not found', { entityId })
  }
}
```

### 3. Repository

```typescript
// modules/<module>/repositories/<module>.repository.ts
import { eq } from 'drizzle-orm'
import { entities, Entity, EntityInsert } from '@/shared/infra/db/schema'
import type { RequestContext } from '@/shared/kernel/context'
import type { DbClient, DrizzleTransaction } from '@/shared/infra/db/types'

export interface IEntityRepository {
  findById(id: string, ctx?: RequestContext): Promise<Entity | null>
  create(data: EntityInsert, ctx?: RequestContext): Promise<Entity>
}

export class EntityRepository implements IEntityRepository {
  constructor(private db: DbClient) {}

  private getClient(ctx?: RequestContext): DbClient | DrizzleTransaction {
    return (ctx?.tx as DrizzleTransaction) ?? this.db
  }

  async findById(id: string, ctx?: RequestContext): Promise<Entity | null> {
    const client = this.getClient(ctx)
    const result = await client
      .select()
      .from(entities)
      .where(eq(entities.id, id))
      .limit(1)
    return result[0] ?? null
  }

  async create(data: EntityInsert, ctx?: RequestContext): Promise<Entity> {
    const client = this.getClient(ctx)
    const result = await client.insert(entities).values(data).returning()
    return result[0]
  }
}
```

### 4. Service

```typescript
// modules/<module>/services/<module>.service.ts
import type { TransactionManager } from '@/shared/kernel/transaction'
import type { RequestContext } from '@/shared/kernel/context'
import type { IEntityRepository } from '../repositories/<module>.repository'
import { Entity, EntityInsert } from '@/shared/infra/db/schema'

export interface IEntityService {
  findById(id: string, ctx?: RequestContext): Promise<Entity | null>
  create(data: EntityInsert, ctx?: RequestContext): Promise<Entity>
}

export class EntityService implements IEntityService {
  constructor(
    private entityRepository: IEntityRepository,
    private transactionManager: TransactionManager
  ) {}

  async findById(id: string, ctx?: RequestContext): Promise<Entity | null> {
    return this.entityRepository.findById(id, ctx)
  }

  async create(data: EntityInsert, ctx?: RequestContext): Promise<Entity> {
    if (ctx?.tx) {
      return this.createInternal(data, ctx)
    }
    return this.transactionManager.run((tx) => this.createInternal(data, { tx }))
  }

  private async createInternal(
    data: EntityInsert,
    ctx: RequestContext
  ): Promise<Entity> {
    return this.entityRepository.create(data, ctx)
  }
}
```

### 5. Factory

```typescript
// modules/<module>/factories/<module>.factory.ts
import { getContainer } from '@/shared/infra/container'
import { EntityRepository } from '../repositories/<module>.repository'
import { EntityService } from '../services/<module>.service'

let entityRepository: EntityRepository | null = null
let entityService: EntityService | null = null

export function makeEntityRepository() {
  if (!entityRepository) {
    entityRepository = new EntityRepository(getContainer().db)
  }
  return entityRepository
}

export function makeEntityService() {
  if (!entityService) {
    entityService = new EntityService(
      makeEntityRepository(),
      getContainer().transactionManager
    )
  }
  return entityService
}
```

### 6. DTOs

```typescript
// modules/<module>/dtos/create-entity.dto.ts
import { z } from 'zod'

export const CreateEntitySchema = z.object({
  name: z.string().min(1).max(255),
  // Define input fields (exclude id, timestamps)
})

export type CreateEntityDTO = z.infer<typeof CreateEntitySchema>
```

### 7. Router

```typescript
// modules/<module>/<module>.router.ts
import { router, protectedProcedure } from '@/shared/infra/trpc'
import { z } from 'zod'
import { makeEntityService } from './factories/<module>.factory'
import { wrapResponse } from '@/shared/utils/response'
import { EntityNotFoundError } from './errors/<module>.errors'
import { CreateEntitySchema } from './dtos/create-entity.dto'

export const entityRouter = router({
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input }) => {
      const entity = await makeEntityService().findById(input.id)
      if (!entity) {
        throw new EntityNotFoundError(input.id)
      }
      return wrapResponse(entity)
    }),

  create: protectedProcedure.input(CreateEntitySchema).mutation(async ({ input }) => {
    const entity = await makeEntityService().create(input)
    return wrapResponse(entity)
  }),
})
```

### 8. Register Router

Add to `shared/infra/trpc/root.ts`:

```typescript
import { entityRouter } from '@/modules/<module>/<module>.router'

export const appRouter = router({
  // ... existing routers
  entity: entityRouter,
})
```

## Key Rules

| Layer | Responsibility |
|-------|---------------|
| Router | HTTP concerns, throws NotFoundError for null |
| Service | Business logic, owns transactions for single-service writes |
| Repository | Data access only, never creates transactions |
| Factory | Lazy singleton creation |
| DTO | API contracts (Zod schemas) |
| Entity | Internal domain type |

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
