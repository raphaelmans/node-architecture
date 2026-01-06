# Endpoint Patterns Reference

## Common CRUD Endpoints

### Get by ID

```typescript
// Router
getById: protectedProcedure
  .input(z.object({ id: z.string().uuid() }))
  .query(async ({ input }) => {
    const entity = await makeEntityService().findById(input.id);
    if (!entity) {
      throw new EntityNotFoundError(input.id);
    }
    return wrapResponse(entity);
  }),

// Service
async findById(id: string, ctx?: RequestContext): Promise<Entity | null> {
  return this.entityRepository.findById(id, ctx);
}
```

### List with Pagination

```typescript
// Router
list: protectedProcedure
  .input(ListEntitiesInputSchema)
  .query(async ({ input }) => {
    return makeEntityService().list(input);
  }),

// Service
async list(input: ListEntitiesInput): Promise<PaginatedResponse<Entity>> {
  const { data, total } = await this.entityRepository.findMany(input);
  return buildPaginatedResponse(data, total, input);
}
```

### Create

```typescript
// Router
create: protectedProcedure
  .input(CreateEntitySchema)
  .mutation(async ({ input }) => {
    const entity = await makeEntityService().create(input);
    return wrapResponse(entity);
  }),

// Service (owns transaction)
async create(data: EntityInsert, ctx?: RequestContext): Promise<Entity> {
  if (ctx?.tx) {
    return this.createInternal(data, ctx);
  }
  return this.transactionManager.run((tx) => this.createInternal(data, { tx }));
}

private async createInternal(data: EntityInsert, ctx: RequestContext): Promise<Entity> {
  // Business validation
  const entity = await this.entityRepository.create(data, ctx);
  
  logger.info(
    { event: 'entity.created', entityId: entity.id },
    'Entity created',
  );
  
  return entity;
}
```

### Update

```typescript
// Router
update: protectedProcedure
  .input(UpdateEntitySchema)
  .mutation(async ({ input }) => {
    const { id, ...data } = input;
    const entity = await makeEntityService().update(id, data);
    return wrapResponse(entity);
  }),

// Service
async update(id: string, data: Partial<EntityInsert>, ctx?: RequestContext): Promise<Entity> {
  const exec = async (ctx: RequestContext): Promise<Entity> => {
    const existing = await this.entityRepository.findById(id, ctx);
    if (!existing) {
      throw new EntityNotFoundError(id);
    }
    
    // Business validation for unique fields, etc.
    
    return this.entityRepository.update(id, data, ctx);
  };

  if (ctx?.tx) return exec(ctx);
  return this.transactionManager.run((tx) => exec({ tx }));
}
```

### Delete

```typescript
// Router
delete: protectedProcedure
  .input(z.object({ id: z.string().uuid() }))
  .mutation(async ({ input }) => {
    await makeEntityService().delete(input.id);
    return { success: true };
  }),

// Service
async delete(id: string, ctx?: RequestContext): Promise<void> {
  const exec = async (ctx: RequestContext): Promise<void> => {
    const existing = await this.entityRepository.findById(id, ctx);
    if (!existing) {
      throw new EntityNotFoundError(id);
    }
    
    // Business rule checks
    
    await this.entityRepository.delete(id, ctx);
    
    logger.info(
      { event: 'entity.deleted', entityId: id },
      'Entity deleted',
    );
  };

  if (ctx?.tx) return exec(ctx);
  return this.transactionManager.run((tx) => exec({ tx }));
}
```

## Specialized Endpoints

### Bulk Operations

```typescript
// DTO
export const BulkDeleteSchema = z.object({
  ids: z.array(z.string().uuid()).min(1).max(100),
});

// Router
bulkDelete: protectedProcedure
  .input(BulkDeleteSchema)
  .mutation(async ({ input }) => {
    const result = await makeEntityService().bulkDelete(input.ids);
    return { deleted: result.count };
  }),

// Service
async bulkDelete(ids: string[], ctx?: RequestContext): Promise<{ count: number }> {
  return this.transactionManager.run(async (tx) => {
    let count = 0;
    for (const id of ids) {
      const existing = await this.entityRepository.findById(id, { tx });
      if (existing) {
        await this.entityRepository.delete(id, { tx });
        count++;
      }
    }
    
    logger.info(
      { event: 'entity.bulk_deleted', count, ids },
      'Entities bulk deleted',
    );
    
    return { count };
  });
}
```

### Status Transitions

```typescript
// DTO
export const TransitionStatusSchema = z.object({
  id: z.string().uuid(),
  status: z.enum(['draft', 'published', 'archived']),
});

// Router
updateStatus: protectedProcedure
  .input(TransitionStatusSchema)
  .mutation(async ({ input }) => {
    const entity = await makeEntityService().updateStatus(input.id, input.status);
    return wrapResponse(entity);
  }),

// Service with state machine validation
async updateStatus(id: string, newStatus: EntityStatus, ctx?: RequestContext): Promise<Entity> {
  const exec = async (ctx: RequestContext): Promise<Entity> => {
    const entity = await this.entityRepository.findById(id, ctx);
    if (!entity) {
      throw new EntityNotFoundError(id);
    }

    // Validate transition
    const validTransitions: Record<EntityStatus, EntityStatus[]> = {
      draft: ['published'],
      published: ['archived'],
      archived: [],
    };

    if (!validTransitions[entity.status].includes(newStatus)) {
      throw new InvalidStatusTransitionError(entity.status, newStatus);
    }

    const updated = await this.entityRepository.update(id, { status: newStatus }, ctx);

    logger.info(
      { event: 'entity.status_changed', entityId: id, from: entity.status, to: newStatus },
      'Entity status changed',
    );

    return updated;
  };

  if (ctx?.tx) return exec(ctx);
  return this.transactionManager.run((tx) => exec({ tx }));
}
```

### Search Endpoint

```typescript
// DTO
export const SearchEntitiesSchema = PaginationInputSchema.extend({
  query: z.string().min(1).max(100),
  filters: z.object({
    category: z.string().optional(),
    dateFrom: z.string().datetime().optional(),
    dateTo: z.string().datetime().optional(),
  }).optional(),
});

// Router
search: protectedProcedure
  .input(SearchEntitiesSchema)
  .query(async ({ input }) => {
    return makeEntityService().search(input);
  }),

// Service
async search(input: SearchEntitiesInput): Promise<PaginatedResponse<Entity>> {
  const { data, total } = await this.entityRepository.search(input);
  return buildPaginatedResponse(data, total, input);
}

// Repository
async search(input: SearchEntitiesInput, ctx?: RequestContext): Promise<{ data: Entity[]; total: number }> {
  const client = this.getClient(ctx);
  const { query, filters, limit = 20, cursor, sort = 'desc' } = input;
  const offset = cursor ?? 0;

  const conditions = [
    or(
      ilike(entities.name, `%${query}%`),
      ilike(entities.description, `%${query}%`),
    ),
  ];

  if (filters?.category) {
    conditions.push(eq(entities.category, filters.category));
  }
  if (filters?.dateFrom) {
    conditions.push(gte(entities.createdAt, new Date(filters.dateFrom)));
  }
  if (filters?.dateTo) {
    conditions.push(lte(entities.createdAt, new Date(filters.dateTo)));
  }

  const whereClause = and(...conditions);

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

### Aggregate/Stats Endpoint

```typescript
// Router
getStats: protectedProcedure
  .input(z.object({
    workspaceId: z.string().uuid(),
    period: z.enum(['day', 'week', 'month']),
  }))
  .query(async ({ input }) => {
    const stats = await makeEntityService().getStats(input.workspaceId, input.period);
    return wrapResponse(stats);
  }),

// Service
async getStats(workspaceId: string, period: Period): Promise<EntityStats> {
  return this.entityRepository.getStats(workspaceId, period);
}

// Repository
async getStats(workspaceId: string, period: Period, ctx?: RequestContext): Promise<EntityStats> {
  const client = this.getClient(ctx);
  
  const periodStart = getPeriodStart(period);
  
  const result = await client
    .select({
      total: count(),
      active: count(sql`CASE WHEN ${entities.status} = 'active' THEN 1 END`),
      archived: count(sql`CASE WHEN ${entities.status} = 'archived' THEN 1 END`),
      createdInPeriod: count(sql`CASE WHEN ${entities.createdAt} >= ${periodStart} THEN 1 END`),
    })
    .from(entities)
    .where(eq(entities.workspaceId, workspaceId));

  return result[0];
}
```

## Endpoints with Authorization

### Resource-Level Authorization

```typescript
// Router
getById: protectedProcedure
  .input(z.object({ id: z.string().uuid() }))
  .query(async ({ input, ctx }) => {
    // Service handles authorization
    const entity = await makeEntityService().getById(input.id, ctx.userId);
    return wrapResponse(entity);
  }),

// Service
async getById(id: string, userId: string): Promise<Entity> {
  const entity = await this.entityRepository.findById(id);
  if (!entity) {
    throw new EntityNotFoundError(id);
  }
  
  // Check access
  const hasAccess = await this.checkAccess(entity, userId);
  if (!hasAccess) {
    throw new EntityAccessDeniedError(id, userId);
  }
  
  return entity;
}

private async checkAccess(entity: Entity, userId: string): Promise<boolean> {
  // Owner always has access
  if (entity.ownerId === userId) return true;
  
  // Check workspace membership
  const member = await this.workspaceMemberRepository.findByUserAndWorkspace(
    userId,
    entity.workspaceId,
  );
  
  return member !== null;
}
```

### Role-Based Authorization

```typescript
// Router with permission middleware
import { requirePermission } from '@/shared/infra/trpc/middleware/authorize.middleware';

delete: protectedProcedure
  .use(requirePermission('manage_entities'))
  .input(z.object({ id: z.string().uuid() }))
  .mutation(async ({ input }) => {
    await makeEntityService().delete(input.id);
    return { success: true };
  }),
```

## Response Patterns

### Single Resource Response

```typescript
// Use wrapResponse for single resources
return wrapResponse(entity);

// Output: { data: entity }
```

### Paginated Response

```typescript
// Use buildPaginatedResponse for lists
return buildPaginatedResponse(data, total, input);

// Output: { data: [...], meta: { total, limit, cursor, nextCursor, sort } }
```

### Action Response

```typescript
// Simple success
return { success: true };

// With count
return { deleted: count };

// With ID
return { id: entity.id };
```

### Omitting Sensitive Fields

```typescript
// For user data, always omit sensitive fields
function omitSensitive(user: User): UserPublic {
  const { passwordHash, ...publicFields } = user;
  return publicFields;
}

// In router
return wrapResponse(omitSensitive(user));
```
