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
