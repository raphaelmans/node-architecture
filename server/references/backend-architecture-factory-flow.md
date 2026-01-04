# Factory to Repository Flow

> **Purpose**: This document defines the complete dependency flow from factory to repository, including interfaces, context passing, and return types.

---

## 1. Flow Overview

```
Factory
  → creates Repository (injects db)
  → creates Service (injects Repository)
  → creates Use Case (injects Service + TransactionManager)
```

**Key principles:**

- Factories are the only place dependencies are instantiated
- Each layer has explicit interfaces
- Context object is passed for extensibility (transactions, tracing, etc.)
- Repositories and Services return Entities
- Use Cases and Controllers return DTOs or Entities

---

## 2. Entity Definition (drizzle-zod)

Entities are generated from Drizzle table definitions using drizzle-zod.

```typescript
// shared/infra/db/schema.ts

import { pgTable, text, timestamp } from 'drizzle-orm/pg-core';
import { createSelectSchema, createInsertSchema } from 'drizzle-zod';
import { z } from 'zod';

// Table definition
export const users = pgTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  passwordHash: text('password_hash').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

// Entity schemas (generated)
export const UserSchema = createSelectSchema(users);
export const UserInsertSchema = createInsertSchema(users);

// Entity types
export type User = z.infer<typeof UserSchema>;
export type UserInsert = z.infer<typeof UserInsertSchema>;

// Safe entity variant (excludes sensitive fields)
export const UserPublicSchema = UserSchema.omit({ passwordHash: true });
export type UserPublic = z.infer<typeof UserPublicSchema>;
```

---

## 3. Context Object

A shared context object for extensibility. Currently holds transaction context, but can be extended for tracing, user context, etc.

```typescript
// shared/kernel/context.ts

import { TransactionContext } from './transaction';

export interface RequestContext {
  tx?: TransactionContext;
  // Future extensions:
  // traceId?: string;
  // userId?: string;
}
```

---

## 4. Repository Layer

### 4.1 Repository Interface

```typescript
// modules/user/repositories/user.repository.interface.ts

import { User, UserInsert } from '@/shared/infra/db/schema';
import { RequestContext } from '@/shared/kernel/context';

export interface IUserRepository {
  findById(id: string, ctx?: RequestContext): Promise<User | null>;
  findByEmail(email: string, ctx?: RequestContext): Promise<User | null>;
  create(data: UserInsert, ctx?: RequestContext): Promise<User>;
  update(id: string, data: Partial<UserInsert>, ctx?: RequestContext): Promise<User>;
  delete(id: string, ctx?: RequestContext): Promise<void>;
}
```

### 4.2 Repository Implementation

```typescript
// modules/user/repositories/user.repository.ts

import { eq } from 'drizzle-orm';
import { users, User, UserInsert } from '@/shared/infra/db/schema';
import { RequestContext } from '@/shared/kernel/context';
import { NotFoundError } from '@/shared/kernel/errors';
import { IUserRepository } from './user.repository.interface';

export class UserRepository implements IUserRepository {
  constructor(private db: DbClient) {}

  async findById(id: string, ctx?: RequestContext): Promise<User | null> {
    const client = ctx?.tx ?? this.db;
    const result = await client
      .select()
      .from(users)
      .where(eq(users.id, id))
      .limit(1);
    
    return result[0] ?? null;
  }

  async findByEmail(email: string, ctx?: RequestContext): Promise<User | null> {
    const client = ctx?.tx ?? this.db;
    const result = await client
      .select()
      .from(users)
      .where(eq(users.email, email))
      .limit(1);
    
    return result[0] ?? null;
  }

  async create(data: UserInsert, ctx?: RequestContext): Promise<User> {
    const client = ctx?.tx ?? this.db;
    const result = await client
      .insert(users)
      .values(data)
      .returning();
    
    return result[0];
  }

  async update(id: string, data: Partial<UserInsert>, ctx?: RequestContext): Promise<User> {
    const client = ctx?.tx ?? this.db;
    const result = await client
      .update(users)
      .set({ ...data, updatedAt: new Date() })
      .where(eq(users.id, id))
      .returning();
    
    if (!result[0]) {
      throw new NotFoundError('User not found', { id });
    }
    
    return result[0];
  }

  async delete(id: string, ctx?: RequestContext): Promise<void> {
    const client = ctx?.tx ?? this.db;
    const result = await client
      .delete(users)
      .where(eq(users.id, id))
      .returning({ id: users.id });
    
    if (!result[0]) {
      throw new NotFoundError('User not found', { id });
    }
  }
}
```

---

## 5. Service Layer

### 5.1 Service Interface

```typescript
// modules/user/services/user.service.interface.ts

import { User, UserInsert } from '@/shared/infra/db/schema';
import { RequestContext } from '@/shared/kernel/context';

export interface IUserService {
  findById(id: string, ctx?: RequestContext): Promise<User | null>;
  findByEmail(email: string, ctx?: RequestContext): Promise<User | null>;
  create(data: UserInsert): Promise<User>;
  update(id: string, data: Partial<UserInsert>): Promise<User>;
  delete(id: string): Promise<void>;
}
```

### 5.2 Service Implementation

Services own transactions for single-service writes.

```typescript
// modules/user/services/user.service.ts

import { User, UserInsert } from '@/shared/infra/db/schema';
import { RequestContext } from '@/shared/kernel/context';
import { TransactionManager } from '@/shared/kernel/transaction';
import { ConflictError } from '@/shared/kernel/errors';
import { IUserRepository } from '../repositories/user.repository.interface';
import { IUserService } from './user.service.interface';

export class UserService implements IUserService {
  constructor(
    private userRepository: IUserRepository,
    private transactionManager: TransactionManager,
  ) {}

  async findById(id: string, ctx?: RequestContext): Promise<User | null> {
    return this.userRepository.findById(id, ctx);
  }

  async findByEmail(email: string, ctx?: RequestContext): Promise<User | null> {
    return this.userRepository.findByEmail(email, ctx);
  }

  async create(data: UserInsert): Promise<User> {
    return this.transactionManager.run(async (tx) => {
      // Business rule: email must be unique
      const existing = await this.userRepository.findByEmail(data.email, { tx });
      if (existing) {
        throw new ConflictError('Email already in use', { email: data.email });
      }

      return this.userRepository.create(data, { tx });
    });
  }

  async update(id: string, data: Partial<UserInsert>): Promise<User> {
    return this.transactionManager.run(async (tx) => {
      // Business rule: if updating email, check uniqueness
      if (data.email) {
        const existing = await this.userRepository.findByEmail(data.email, { tx });
        if (existing && existing.id !== id) {
          throw new ConflictError('Email already in use', { email: data.email });
        }
      }

      return this.userRepository.update(id, data, { tx });
    });
  }

  async delete(id: string): Promise<void> {
    return this.transactionManager.run(async (tx) => {
      return this.userRepository.delete(id, { tx });
    });
  }
}
```

---

## 6. Use Case Layer

Use cases are for **multi-service orchestration** and **side effects**, not for single-service writes.

### 6.1 When to Use a Use Case

* Coordinating multiple services
* Triggering side effects (email, audit, events)
* Complex workflows

### 6.2 Use Case Interface

```typescript
// modules/user/use-cases/register-user.use-case.interface.ts

import { UserPublic } from '@/shared/infra/db/schema';
import { RegisterUserDTO } from '../dtos/register-user.dto';

export interface IRegisterUserUseCase {
  execute(input: RegisterUserDTO): Promise<UserPublic>;
}
```

### 6.3 DTO Definition

```typescript
// modules/user/dtos/register-user.dto.ts

import { z } from 'zod';

export const RegisterUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  password: z.string().min(8).max(100),
  workspaceId: z.string().optional(),
});

export type RegisterUserDTO = z.infer<typeof RegisterUserSchema>;
```

### 6.4 Use Case Implementation (Multi-Service Example)

```typescript
// modules/user/use-cases/register-user.use-case.ts

import { UserPublic } from '@/shared/infra/db/schema';
import { TransactionManager } from '@/shared/kernel/transaction';
import { IUserService } from '../services/user.service.interface';
import { IWorkspaceService } from '@/modules/workspace/services/workspace.service.interface';
import { IEmailService } from '@/shared/infra/email/email.service.interface';
import { RegisterUserDTO } from '../dtos/register-user.dto';
import { IRegisterUserUseCase } from './register-user.use-case.interface';
import { hashPassword } from '@/shared/utils/password';

export class RegisterUserUseCase implements IRegisterUserUseCase {
  constructor(
    private userService: IUserService,
    private workspaceService: IWorkspaceService,
    private emailService: IEmailService,
    private transactionManager: TransactionManager,
  ) {}

  async execute(input: RegisterUserDTO): Promise<UserPublic> {
    // Multi-service orchestration requires use case
    const user = await this.transactionManager.run(async (tx) => {
      const passwordHash = await hashPassword(input.password);

      const user = await this.userService.createWithContext(
        {
          id: generateId(),
          email: input.email,
          name: input.name,
          passwordHash,
        },
        { tx },
      );

      // Add user to workspace if provided
      if (input.workspaceId) {
        await this.workspaceService.addMember(
          input.workspaceId,
          user.id,
          { tx },
        );
      }

      return user;
    });

    // Side effect: send welcome email (outside transaction)
    await this.emailService.sendWelcomeEmail(user.email, user.name);

    // Omit sensitive fields
    const { passwordHash: _, ...userPublic } = user;
    return userPublic;
  }
}
```

---

## 7. Factory Layer

```typescript
// modules/user/factories/user.factory.ts

import { getContainer } from '@/shared/infra/container';
import { UserRepository } from '../repositories/user.repository';
import { UserService } from '../services/user.service';
import { RegisterUserUseCase } from '../use-cases/register-user.use-case';
import { IUserRepository } from '../repositories/user.repository.interface';
import { IUserService } from '../services/user.service.interface';
import { IRegisterUserUseCase } from '../use-cases/register-user.use-case.interface';

let userRepository: IUserRepository | null = null;
let userService: IUserService | null = null;

export function makeUserRepository(): IUserRepository {
  if (!userRepository) {
    userRepository = new UserRepository(getContainer().db);
  }
  return userRepository;
}

export function makeUserService(): IUserService {
  if (!userService) {
    userService = new UserService(
      makeUserRepository(),
      getContainer().transactionManager,
    );
  }
  return userService;
}

// Use case: only for multi-service orchestration
export function makeRegisterUserUseCase(): IRegisterUserUseCase {
  return new RegisterUserUseCase(
    makeUserService(),
    makeWorkspaceService(), // from workspace module
    makeEmailService(),     // from shared infra
    getContainer().transactionManager,
  );
}
```

---

## 8. Router/Controller Layer (tRPC Example)

```typescript
// modules/user/user.router.ts

import { router, publicProcedure, protectedProcedure } from '@/shared/infra/trpc';
import { z } from 'zod';
import { CreateUserSchema } from './dtos/create-user.dto';
import { RegisterUserSchema } from './dtos/register-user.dto';
import { makeUserService, makeRegisterUserUseCase } from './factories/user.factory';
import { NotFoundError } from '@/shared/kernel/errors';

export const userRouter = router({
  // Simple write → Service (owns its own transaction)
  create: protectedProcedure
    .input(CreateUserSchema)
    .mutation(async ({ input }) => {
      const user = await makeUserService().create(input);
      const { passwordHash: _, ...userPublic } = user;
      return userPublic;
    }),

  // Multi-service orchestration → Use Case
  register: publicProcedure
    .input(RegisterUserSchema)
    .mutation(async ({ input }) => {
      return makeRegisterUserUseCase().execute(input);
    }),

  // Read → Service
  getById: protectedProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      const user = await makeUserService().findById(input.id);
      if (!user) {
        throw new NotFoundError('User not found', { id: input.id });
      }
      const { passwordHash: _, ...userPublic } = user;
      return userPublic;
    }),
});
```

---

## 9. Complete Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                           Factory                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ makeUserRepository() ──► UserRepository(db)             │   │
│  │         │                                               │   │
│  │         ▼                                               │   │
│  │ makeUserService() ──► UserService(                      │   │
│  │         │               userRepository,                 │   │
│  │         │               transactionManager)             │   │
│  │         │                                               │   │
│  │         ▼                                               │   │
│  │ makeRegisterUserUseCase() ──► RegisterUserUseCase(      │   │
│  │                                userService,             │   │
│  │                                workspaceService,        │   │
│  │                                emailService,            │   │
│  │                                transactionManager)      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Router/Controller                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │ Simple write (single service):                          │   │
│  │   userRouter.create ──► UserService.create()            │   │
│  │                              │                          │   │
│  │                              ▼                          │   │
│  │                     UserRepository.create()             │   │
│  │                                                         │   │
│  │ Multi-service orchestration:                            │   │
│  │   userRouter.register ──► RegisterUserUseCase.execute() │   │
│  │                              │                          │   │
│  │                    ┌─────────┴─────────┐                │   │
│  │                    ▼                   ▼                │   │
│  │           UserService        WorkspaceService           │   │
│  │                    │                   │                │   │
│  │                    ▼                   ▼                │   │
│  │           UserRepository     WorkspaceRepository        │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Return Type Summary

| Layer | Returns | Type Source |
|-------|---------|-------------|
| Repository | Entity | drizzle-zod `createSelectSchema` |
| Service | Entity | Same as Repository |
| Use Case | Entity or DTO | DTO when transforming/omitting |
| Router/Controller | Entity or DTO | What API consumers see |

**Rule**: Return entities by default. Introduce DTOs when you need to transform, omit sensitive fields, or combine data.

---

## 11. Checklist

- [ ] Entity schemas generated via drizzle-zod
- [ ] Repository interface defined with `ctx?: RequestContext`
- [ ] Service interface defined, 1:1 with repository
- [ ] Service receives `TransactionManager` for single-service writes
- [ ] Use cases only for multi-service orchestration or side effects
- [ ] Factory creates lazy singletons for repository/service
- [ ] Factory creates new instance for each use case
- [ ] Sensitive fields omitted before returning to client
