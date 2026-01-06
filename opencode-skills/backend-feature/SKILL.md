---
name: backend-feature
description: Add endpoints, service methods, fields, and use cases to existing backend modules in Next.js + tRPC + Drizzle projects
---

# Adding Features to Existing Modules

Use this skill when extending existing modules with new endpoints, fields, or capabilities.

## Feature Types

| Type | Changes Required |
|------|------------------|
| New endpoint | Router + Service method + DTO |
| New field | Schema + Migration + DTOs |
| New service method | Service + Repository (if needed) |
| New use case | Use case class + Factory |

## Adding a New Endpoint

### 1. Determine Layer Requirements

```
Is it a read operation?
├── Yes → Service + Router only
└── No (write)
    └── Multiple services or side effects?
        ├── No → Service + Router
        └── Yes → Create Use Case
```

### 2. Create DTO

```typescript
// modules/<module>/dtos/<action>-entity.dto.ts
import { z } from 'zod'

export const ArchiveEntitySchema = z.object({
  id: z.string().uuid(),
})

export type ArchiveEntityDTO = z.infer<typeof ArchiveEntitySchema>
```

### 3. Add Repository Method (if new data access)

```typescript
// In repository file - add method
async findByStatus(status: string, ctx?: RequestContext): Promise<Entity[]> {
  const client = this.getClient(ctx)
  return client.select().from(entities).where(eq(entities.status, status))
}

// Update interface
export interface IEntityRepository {
  // ... existing
  findByStatus(status: string, ctx?: RequestContext): Promise<Entity[]>
}
```

### 4. Add Service Method

```typescript
// For writes with business logic
async archive(id: string, ctx?: RequestContext): Promise<Entity> {
  const exec = async (ctx: RequestContext): Promise<Entity> => {
    const entity = await this.entityRepository.findById(id, ctx)
    if (!entity) {
      throw new EntityNotFoundError(id)
    }
    if (entity.status === 'archived') {
      throw new EntityAlreadyArchivedError(id)
    }

    const updated = await this.entityRepository.update(
      id,
      { status: 'archived' },
      ctx
    )

    logger.info({ event: 'entity.archived', entityId: id }, 'Entity archived')

    return updated
  }

  if (ctx?.tx) return exec(ctx)
  return this.transactionManager.run((tx) => exec({ tx }))
}
```

### 5. Add Router Procedure

```typescript
archive: protectedProcedure
  .input(z.object({ id: z.string().uuid() }))
  .mutation(async ({ input }) => {
    const entity = await makeEntityService().archive(input.id)
    return wrapResponse(entity)
  }),
```

## Adding a New Field

### 1. Update Schema

```typescript
// shared/infra/db/schema.ts
export const entities = pgTable('entities', {
  // ... existing
  newField: text('new_field'),
})
```

### 2. Generate Migration

```bash
npx drizzle-kit generate
npx drizzle-kit migrate
```

### 3. Update DTOs

```typescript
// Add to create/update DTOs as needed
export const UpdateEntitySchema = z.object({
  // ... existing
  newField: z.string().optional(),
})
```

## Adding a Use Case

Use cases are for multi-service orchestration or complex workflows.

### 1. Create Use Case

```typescript
// modules/<module>/use-cases/<action>.use-case.ts
import type { TransactionManager } from '@/shared/kernel/transaction'
import type { IEntityService } from '../services/entity.service'
import type { IOtherService } from '@/modules/other/services/other.service'
import type { IEmailService } from '@/shared/infra/email/email.service'

export interface ICreateWithNotificationUseCase {
  execute(input: CreateEntityDTO): Promise<Entity>
}

export class CreateWithNotificationUseCase implements ICreateWithNotificationUseCase {
  constructor(
    private entityService: IEntityService,
    private otherService: IOtherService,
    private emailService: IEmailService,
    private transactionManager: TransactionManager
  ) {}

  async execute(input: CreateEntityDTO): Promise<Entity> {
    // Transaction for database operations
    const entity = await this.transactionManager.run(async (tx) => {
      const created = await this.entityService.create(input, { tx })
      await this.otherService.relatedAction(created.id, { tx })
      return created
    })

    // Side effects after transaction
    await this.emailService.sendNotification(entity.email)

    return entity
  }
}
```

### 2. Add Factory

```typescript
// Use cases: new instance per invocation
export function makeCreateWithNotificationUseCase() {
  return new CreateWithNotificationUseCase(
    makeEntityService(),
    makeOtherService(),
    makeEmailService(),
    getContainer().transactionManager
  )
}
```

### 3. Add Router Procedure

```typescript
createWithNotification: protectedProcedure
  .input(CreateEntitySchema)
  .mutation(async ({ input }) => {
    return makeCreateWithNotificationUseCase().execute(input)
  }),
```

## Adding Pagination

### 1. Create List DTO

```typescript
import { PaginationInputSchema } from '@/shared/kernel/pagination'

export const ListEntitiesInputSchema = PaginationInputSchema.extend({
  status: z.enum(['active', 'archived']).optional(),
  search: z.string().optional(),
})
```

### 2. Repository Method

```typescript
async findMany(
  input: ListEntitiesInput,
  ctx?: RequestContext
): Promise<{ data: Entity[]; total: number }> {
  const client = this.getClient(ctx)
  const { limit = 20, cursor, sort = 'desc', search, status } = input
  const offset = cursor ?? 0

  const conditions = []
  if (search) {
    conditions.push(ilike(entities.name, `%${search}%`))
  }
  if (status) {
    conditions.push(eq(entities.status, status))
  }

  const whereClause = conditions.length > 0 ? and(...conditions) : undefined

  const [data, [{ total }]] = await Promise.all([
    client
      .select()
      .from(entities)
      .where(whereClause)
      .orderBy(sort === 'desc' ? desc(entities.createdAt) : asc(entities.createdAt))
      .limit(limit)
      .offset(offset),
    client.select({ total: count() }).from(entities).where(whereClause),
  ])

  return { data, total }
}
```

### 3. Service + Router

```typescript
// Service
async list(input: ListEntitiesInput): Promise<PaginatedResponse<Entity>> {
  const { data, total } = await this.entityRepository.findMany(input)
  return buildPaginatedResponse(data, total, input)
}

// Router
list: protectedProcedure.input(ListEntitiesInputSchema).query(async ({ input }) => {
  return makeEntityService().list(input)
}),
```

## Checklist

- [ ] DTO created with Zod schema
- [ ] Repository method added (if new data access)
- [ ] Repository interface updated
- [ ] Service method added
- [ ] Service interface updated
- [ ] Business events logged in service
- [ ] Domain errors created (if new error cases)
- [ ] Router procedure added
- [ ] Router handles null from service (throws NotFoundError)
