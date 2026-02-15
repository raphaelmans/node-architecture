# Layer Patterns Reference

## Repository Patterns

### Standard CRUD Repository

```typescript
export class EntityRepository implements IEntityRepository {
  constructor(private db: DbClient) {}

  private getClient(ctx?: RequestContext): DbClient | DrizzleTransaction {
    return (ctx?.tx as DrizzleTransaction) ?? this.db;
  }

  // Read - no transaction needed
  async findById(id: string, ctx?: RequestContext): Promise<Entity | null> {
    const client = this.getClient(ctx);
    const result = await client
      .select()
      .from(entities)
      .where(eq(entities.id, id))
      .limit(1);
    return result[0] ?? null;
  }

  // Read with relations
  async findByIdWithRelations(id: string, ctx?: RequestContext): Promise<EntityWithRelations | null> {
    const client = this.getClient(ctx);
    const result = await client.query.entities.findFirst({
      where: eq(entities.id, id),
      with: {
        relatedEntity: true,
      },
    });
    return result ?? null;
  }

  // List with filters
  async findMany(
    filters: EntityFilters,
    ctx?: RequestContext,
  ): Promise<{ data: Entity[]; total: number }> {
    const client = this.getClient(ctx);
    const { limit = 20, cursor, sort = 'desc', search } = filters;
    const offset = cursor ?? 0;

    const conditions = [];
    if (search) {
      conditions.push(ilike(entities.name, `%${search}%`));
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

  // Create
  async create(data: EntityInsert, ctx?: RequestContext): Promise<Entity> {
    const client = this.getClient(ctx);
    const result = await client
      .insert(entities)
      .values(data)
      .returning();
    return result[0];
  }

  // Update
  async update(id: string, data: Partial<EntityInsert>, ctx?: RequestContext): Promise<Entity> {
    const client = this.getClient(ctx);
    const result = await client
      .update(entities)
      .set({ ...data, updatedAt: new Date() })
      .where(eq(entities.id, id))
      .returning();
    return result[0];
  }

  // Delete
  async delete(id: string, ctx?: RequestContext): Promise<void> {
    const client = this.getClient(ctx);
    await client.delete(entities).where(eq(entities.id, id));
  }

  // Lookup by unique field
  async findByEmail(email: string, ctx?: RequestContext): Promise<Entity | null> {
    const client = this.getClient(ctx);
    const result = await client
      .select()
      .from(entities)
      .where(eq(entities.email, email))
      .limit(1);
    return result[0] ?? null;
  }
}
```

## Service Patterns

### Standard Service with Transaction Handling

```typescript
export class EntityService implements IEntityService {
  constructor(
    private entityRepository: IEntityRepository,
    private transactionManager: TransactionManager,
  ) {}

  // Read - pass through
  async findById(id: string, ctx?: RequestContext): Promise<Entity | null> {
    return this.entityRepository.findById(id, ctx);
  }

  // List with pagination
  async list(input: ListInput): Promise<PaginatedResponse<Entity>> {
    const { data, total } = await this.entityRepository.findMany(input);
    return buildPaginatedResponse(data, total, input);
  }

  // Write - owns or participates in transaction
  async create(data: EntityInsert, ctx?: RequestContext): Promise<Entity> {
    if (ctx?.tx) {
      return this.createInternal(data, ctx);
    }
    return this.transactionManager.run((tx) => this.createInternal(data, { tx }));
  }

  private async createInternal(data: EntityInsert, ctx: RequestContext): Promise<Entity> {
    // Business validation
    if (data.email) {
      const existing = await this.entityRepository.findByEmail(data.email, ctx);
      if (existing) {
        throw new EntityEmailConflictError(data.email);
      }
    }

    const entity = await this.entityRepository.create(data, ctx);

    // Log business event
    logger.info(
      { event: 'entity.created', entityId: entity.id },
      'Entity created',
    );

    return entity;
  }

  // Update with validation
  async update(id: string, data: Partial<EntityInsert>, ctx?: RequestContext): Promise<Entity> {
    const exec = async (ctx: RequestContext): Promise<Entity> => {
      const existing = await this.entityRepository.findById(id, ctx);
      if (!existing) {
        throw new EntityNotFoundError(id);
      }

      // Business validation for unique fields
      if (data.email && data.email !== existing.email) {
        const conflict = await this.entityRepository.findByEmail(data.email, ctx);
        if (conflict) {
          throw new EntityEmailConflictError(data.email);
        }
      }

      return this.entityRepository.update(id, data, ctx);
    };

    if (ctx?.tx) {
      return exec(ctx);
    }
    return this.transactionManager.run((tx) => exec({ tx }));
  }

  // Delete with business rules
  async delete(id: string, ctx?: RequestContext): Promise<void> {
    const exec = async (ctx: RequestContext): Promise<void> => {
      const existing = await this.entityRepository.findById(id, ctx);
      if (!existing) {
        throw new EntityNotFoundError(id);
      }

      // Business rule checks
      if (existing.role === 'owner') {
        throw new CannotDeleteOwnerError(id);
      }

      await this.entityRepository.delete(id, ctx);

      logger.info(
        { event: 'entity.deleted', entityId: id },
        'Entity deleted',
      );
    };

    if (ctx?.tx) {
      return exec(ctx);
    }
    return this.transactionManager.run((tx) => exec({ tx }));
  }
}
```

## Use Case Patterns

### Multi-Service Orchestration

```typescript
export class RegisterUserUseCase {
  constructor(
    private userService: IUserService,
    private workspaceService: IWorkspaceService,
    private emailService: IEmailService,
    private transactionManager: TransactionManager,
  ) {}

  async execute(input: RegisterUserDTO): Promise<UserPublic> {
    // Transaction: all database operations
    const user = await this.transactionManager.run(async (tx) => {
      const passwordHash = await hashPassword(input.password);

      const user = await this.userService.create(
        {
          email: input.email,
          name: input.name,
          passwordHash,
        },
        { tx },
      );

      if (input.workspaceId) {
        await this.workspaceService.addMember(input.workspaceId, user.id, { tx });
      }

      return user;
    });

    // Side effects: after transaction commits
    await this.emailService.sendWelcomeEmail(user.email, user.name);

    return omitSensitive(user);
  }
}
```

### Use Case with Conditional Logic

```typescript
export class TransferFundsUseCase {
  constructor(
    private accountService: IAccountService,
    private auditService: IAuditService,
    private notificationService: INotificationService,
    private transactionManager: TransactionManager,
  ) {}

  async execute(input: TransferFundsDTO): Promise<TransferResult> {
    const result = await this.transactionManager.run(async (tx) => {
      // Validate accounts exist
      const fromAccount = await this.accountService.findById(input.fromAccountId, { tx });
      const toAccount = await this.accountService.findById(input.toAccountId, { tx });

      if (!fromAccount) throw new AccountNotFoundError(input.fromAccountId);
      if (!toAccount) throw new AccountNotFoundError(input.toAccountId);

      // Business rule validation
      if (fromAccount.balance < input.amount) {
        throw new InsufficientFundsError(input.fromAccountId, input.amount);
      }

      // Execute transfer
      await this.accountService.debit(input.fromAccountId, input.amount, { tx });
      await this.accountService.credit(input.toAccountId, input.amount, { tx });

      // Audit within transaction
      const transfer = await this.auditService.logTransfer(
        {
          fromAccountId: input.fromAccountId,
          toAccountId: input.toAccountId,
          amount: input.amount,
        },
        { tx },
      );

      return transfer;
    });

    // Notifications after commit
    await this.notificationService.sendTransferNotification(result);

    return result;
  }
}
```

## Factory Patterns

### Module Factory with Multiple Dependencies

```typescript
// factories/module.factory.ts
import { getContainer } from '@/shared/infra/container';
import { EntityRepository } from '../repositories/entity.repository';
import { EntityService } from '../services/entity.service';
import { ComplexUseCase } from '../use-cases/complex.use-case';
import { makeOtherService } from '@/modules/other/factories';
import { makeEmailService } from '@/shared/infra/email/factory';

// Lazy singletons for stateless components
let entityRepository: EntityRepository | null = null;
let entityService: EntityService | null = null;

export function makeEntityRepository() {
  if (!entityRepository) {
    entityRepository = new EntityRepository(getContainer().db);
  }
  return entityRepository;
}

export function makeEntityService() {
  if (!entityService) {
    entityService = new EntityService(
      makeEntityRepository(),
      getContainer().transactionManager,
    );
  }
  return entityService;
}

// New instance per invocation for use cases
export function makeComplexUseCase() {
  return new ComplexUseCase(
    makeEntityService(),
    makeOtherService(),
    makeEmailService(),
    getContainer().transactionManager,
  );
}

// For testing
export function resetFactories() {
  entityRepository = null;
  entityService = null;
}
```

## Router Decision Flow

```
Is it a read operation?
├── Yes → Call Service.findById() or Service.list()
└── No (write operation)
    └── Does it involve multiple services or side effects?
        ├── No → Call Service directly (service owns transaction)
        └── Yes → Call Use Case (use case owns transaction)
```

### Router Examples

```typescript
export const entityRouter = router({
  // Read: Service directly
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input }) => {
      const entity = await makeEntityService().findById(input.id);
      if (!entity) {
        throw new EntityNotFoundError(input.id);
      }
      return wrapResponse(entity);
    }),

  // List: Service directly
  list: protectedProcedure
    .input(ListEntitiesInputSchema)
    .query(async ({ input }) => {
      return makeEntityService().list(input);
    }),

  // Simple write: Service (owns transaction)
  create: protectedProcedure
    .input(CreateEntitySchema)
    .mutation(async ({ input }) => {
      const entity = await makeEntityService().create(input);
      return wrapResponse(entity);
    }),

  // Multi-service: Use Case
  register: publicProcedure
    .input(RegisterSchema)
    .mutation(async ({ input }) => {
      return makeRegisterUseCase().execute(input);
    }),
});
```
