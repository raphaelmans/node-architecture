---
name: backend-feature
description: Adds new features to existing backend modules including endpoints, service methods, and database changes. Use when adding a new endpoint, new API method, extending an entity, adding a field, or when the user mentions "add endpoint", "new route", "add field", "extend module".
---

# Adding Features to Existing Modules

## Feature Types

| Type | What Changes |
|------|--------------|
| New endpoint | Router + Service method + DTO |
| New field | Schema + Migration + DTOs |
| New service method | Service + Repository (if needed) |
| New use case | Use case class + Factory |

## Adding a New Endpoint

### 1. Determine Layer Requirements

```
Is it a read operation?
├── Yes → Add to Service + Router
└── No (write)
    └── Multiple services or side effects?
        ├── No → Add to Service + Router
        └── Yes → Create Use Case + Add to Router
```

### 2. Create DTO (if needed)

```typescript
// modules/<module>/dtos/<action>-<entity>.dto.ts
import { z } from 'zod';

export const <Action><Entity>Schema = z.object({
  // Define input fields
});

export type <Action><Entity>DTO = z.infer<typeof <Action><Entity>Schema>;
```

### 3. Add Repository Method (if new data access pattern)

```typescript
// In repository file
async findByStatus(status: string, ctx?: RequestContext): Promise<Entity[]> {
  const client = this.getClient(ctx);
  return client
    .select()
    .from(entities)
    .where(eq(entities.status, status));
}
```

Update interface:
```typescript
export interface IEntityRepository {
  // ... existing methods
  findByStatus(status: string, ctx?: RequestContext): Promise<Entity[]>;
}
```

### 4. Add Service Method

```typescript
// In service file
async findByStatus(status: string, ctx?: RequestContext): Promise<Entity[]> {
  return this.entityRepository.findByStatus(status, ctx);
}

// For write operations with business logic:
async archive(id: string, ctx?: RequestContext): Promise<Entity> {
  const exec = async (ctx: RequestContext): Promise<Entity> => {
    const entity = await this.entityRepository.findById(id, ctx);
    if (!entity) {
      throw new EntityNotFoundError(id);
    }
    if (entity.status === 'archived') {
      throw new EntityAlreadyArchivedError(id);
    }
    
    const updated = await this.entityRepository.update(id, { status: 'archived' }, ctx);
    
    logger.info(
      { event: 'entity.archived', entityId: id },
      'Entity archived',
    );
    
    return updated;
  };

  if (ctx?.tx) return exec(ctx);
  return this.transactionManager.run((tx) => exec({ tx }));
}
```

Update interface:
```typescript
export interface IEntityService {
  // ... existing methods
  findByStatus(status: string, ctx?: RequestContext): Promise<Entity[]>;
  archive(id: string, ctx?: RequestContext): Promise<Entity>;
}
```

### 5. Add Router Procedure

```typescript
// In router file
export const entityRouter = router({
  // ... existing procedures
  
  getByStatus: protectedProcedure
    .input(z.object({ status: z.enum(['active', 'archived']) }))
    .query(async ({ input }) => {
      const entities = await makeEntityService().findByStatus(input.status);
      return wrapResponse(entities);
    }),

  archive: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .mutation(async ({ input }) => {
      const entity = await makeEntityService().archive(input.id);
      return wrapResponse(entity);
    }),
});
```

## Adding a New Field

### 1. Update Database Schema

```typescript
// shared/infra/db/schema.ts
export const entities = pgTable('entities', {
  // ... existing fields
  newField: text('new_field'),  // Add new field
});
```

### 2. Generate and Run Migration

```bash
npx drizzle-kit generate
npx drizzle-kit migrate
```

### 3. Update DTOs

```typescript
// Create DTO - add if user can set on create
export const CreateEntitySchema = z.object({
  // ... existing fields
  newField: z.string().optional(),
});

// Update DTO - add if user can update
export const UpdateEntitySchema = z.object({
  // ... existing fields
  newField: z.string().optional(),
});
```

### 4. Update Service (if business logic needed)

```typescript
private async createInternal(data: EntityInsert, ctx: RequestContext): Promise<Entity> {
  // Add validation for new field if needed
  if (data.newField) {
    // Validate newField
  }
  
  return this.entityRepository.create(data, ctx);
}
```

## Adding a New Use Case

Use cases are for multi-service orchestration or complex workflows with side effects.

### 1. Create Use Case Class

```typescript
// modules/<module>/use-cases/<action>.use-case.ts
import type { TransactionManager } from '@/shared/kernel/transaction';
import type { IEntityService } from '../services/entity.service';
import type { IOtherService } from '@/modules/other/services/other.service';
import type { IEmailService } from '@/shared/infra/email/email.service';

export interface I<Action>UseCase {
  execute(input: <Action>DTO): Promise<Result>;
}

export class <Action>UseCase implements I<Action>UseCase {
  constructor(
    private entityService: IEntityService,
    private otherService: IOtherService,
    private emailService: IEmailService,
    private transactionManager: TransactionManager,
  ) {}

  async execute(input: <Action>DTO): Promise<Result> {
    // Transaction for database operations
    const result = await this.transactionManager.run(async (tx) => {
      const entity = await this.entityService.doSomething(input.entityId, { tx });
      await this.otherService.relatedAction(entity.id, { tx });
      return entity;
    });

    // Side effects after transaction
    await this.emailService.sendNotification(result.email);

    return result;
  }
}
```

### 2. Add Factory Function

```typescript
// modules/<module>/factories/<module>.factory.ts

// Use cases: new instance per invocation
export function make<Action>UseCase() {
  return new <Action>UseCase(
    makeEntityService(),
    makeOtherService(),
    makeEmailService(),
    getContainer().transactionManager,
  );
}
```

### 3. Add Router Procedure

```typescript
// In router
<action>: protectedProcedure
  .input(<Action>Schema)
  .mutation(async ({ input }) => {
    return make<Action>UseCase().execute(input);
  }),
```

## Adding Pagination to an Endpoint

### 1. Create List DTO

```typescript
// modules/<module>/dtos/list-<entities>.dto.ts
import { z } from 'zod';
import { PaginationInputSchema } from '@/shared/kernel/pagination';

export const ListEntitiesInputSchema = PaginationInputSchema.extend({
  // Module-specific filters
  status: z.enum(['active', 'archived']).optional(),
  ownerId: z.string().uuid().optional(),
});

export type ListEntitiesInput = z.infer<typeof ListEntitiesInputSchema>;
```

### 2. Add Repository Method

```typescript
async findMany(
  input: ListEntitiesInput,
  ctx?: RequestContext,
): Promise<{ data: Entity[]; total: number }> {
  const client = this.getClient(ctx);
  const { limit = 20, cursor, sort = 'desc', search, status, ownerId } = input;
  const offset = cursor ?? 0;

  const conditions = [];
  
  if (search) {
    conditions.push(
      or(
        ilike(entities.name, `%${search}%`),
        ilike(entities.description, `%${search}%`),
      ),
    );
  }
  if (status) {
    conditions.push(eq(entities.status, status));
  }
  if (ownerId) {
    conditions.push(eq(entities.ownerId, ownerId));
  }

  const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

  const [data, [{ total }]] = await Promise.all([
    client
      .select()
      .from(entities)
      .where(whereClause)
      .orderBy(sort === 'desc' ? desc(entities.createdAt) : asc(entities.createdAt))
      .limit(limit)
      .offset(offset),
    client
      .select({ total: count() })
      .from(entities)
      .where(whereClause),
  ]);

  return { data, total };
}
```

### 3. Add Service Method

```typescript
async list(input: ListEntitiesInput): Promise<PaginatedResponse<Entity>> {
  const { data, total } = await this.entityRepository.findMany(input);
  return buildPaginatedResponse(data, total, input);
}
```

### 4. Add Router Procedure

```typescript
list: protectedProcedure
  .input(ListEntitiesInputSchema)
  .query(async ({ input }) => {
    return makeEntityService().list(input);
  }),
```

## Adding Domain Errors

```typescript
// modules/<module>/errors/<module>.errors.ts

// Add new error classes as needed
export class EntityAlreadyArchivedError extends BusinessRuleError {
  readonly code = 'ENTITY_ALREADY_ARCHIVED';

  constructor(entityId: string) {
    super('Entity is already archived', { entityId });
  }
}

export class EntityAccessDeniedError extends AuthorizationError {
  readonly code = 'ENTITY_ACCESS_DENIED';

  constructor(entityId: string, userId: string) {
    super('Access to entity denied', { entityId, userId });
  }
}
```

## Checklist for New Features

- [ ] DTO created with Zod schema
- [ ] Repository method added (if new data access)
- [ ] Repository interface updated
- [ ] Service method added
- [ ] Service interface updated
- [ ] Business events logged in service
- [ ] Domain errors created (if new error cases)
- [ ] Router procedure added
- [ ] Input validation in `.input()` uses Zod schema
- [ ] Router handles null from service (throws NotFoundError)

See [references/endpoint-patterns.md](references/endpoint-patterns.md) for more examples.
