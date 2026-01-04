# Backend Architecture: Next.js (Serverless) + tRPC

> **Purpose**: This document extends the primary [Backend Architecture Conventions](./backend-architecture-conventions.md) with specifics for Next.js serverless deployments using tRPC.

---

## 1. Runtime Considerations

### Serverless Constraints

* **Cold starts**: Each invocation may spin up a new instance
* **No persistent process**: Long-lived singletons reset between cold starts
* **Warm instances**: Module-level state persists during warm invocations
* **Connection limits**: Database connections must be pooled carefully

### What This Means

* Lazy singletons still work — they're reused during warm starts
* Database connections should be managed carefully (see Drizzle section)
* Avoid heavy initialization in request paths

---

## 2. Factory Pattern for Serverless

Use **module-level lazy singletons** for repositories and services. This reuses instances during warm invocations without cold start penalty.

```typescript
// modules/user/factories/user.factory.ts

import { getContainer } from '@/shared/infra/container';
import { UserRepository } from '../repositories/user.repository';
import { UserService } from '../services/user.service';
import { CreateUserUseCase } from '../use-cases/create-user.use-case';

let userRepository: UserRepository | null = null;
let userService: UserService | null = null;

export function makeUserRepository() {
  if (!userRepository) {
    userRepository = new UserRepository(getContainer().db);
  }
  return userRepository;
}

export function makeUserService() {
  if (!userService) {
    userService = new UserService(makeUserRepository());
  }
  return userService;
}

export function makeCreateUserUseCase() {
  return new CreateUserUseCase(
    makeUserService(),
    getContainer().transactionManager,
  );
}
```

---

## 3. tRPC Integration

### Router Structure

tRPC routers map to modules. Procedures call factories directly.

```typescript
// modules/user/user.router.ts

import { router, publicProcedure, protectedProcedure } from '@/shared/infra/trpc';
import { CreateUserSchema } from './dtos/create-user.dto';
import { makeUserService, makeCreateUserUseCase } from './factories/user.factory';
import { z } from 'zod';

export const userRouter = router({
  // Write operation → Use Case
  create: protectedProcedure
    .input(CreateUserSchema)
    .mutation(async ({ input }) => {
      return makeCreateUserUseCase().execute(input);
    }),

  // Simple read → Service directly
  getById: protectedProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      return makeUserService().findById(input.id);
    }),

  // List/filter → Service directly
  list: protectedProcedure
    .input(z.object({ 
      limit: z.number().min(1).max(100).default(20),
      cursor: z.string().optional(),
    }))
    .query(async ({ input }) => {
      return makeUserService().list(input);
    }),
});
```

### Root Router

```typescript
// shared/infra/trpc/root.ts

import { router } from './trpc';
import { userRouter } from '@/modules/user/user.router';
import { workspaceRouter } from '@/modules/workspace/workspace.router';

export const appRouter = router({
  user: userRouter,
  workspace: workspaceRouter,
});

export type AppRouter = typeof appRouter;
```

---

## 4. Error Handling in tRPC

Map `AppError` to tRPC errors in a custom error formatter.

```typescript
// shared/infra/trpc/trpc.ts

import { initTRPC, TRPCError } from '@trpc/server';
import { AppError } from '@/shared/kernel/errors';

const t = initTRPC.context<Context>().create({
  errorFormatter({ error, shape }) {
    const cause = error.cause;
    
    if (cause instanceof AppError) {
      return {
        ...shape,
        data: {
          ...shape.data,
          code: cause.code,
          httpStatus: cause.httpStatus,
          details: cause.details,
        },
      };
    }
    
    return shape;
  },
});
```

### Throwing Errors in Procedures

Let `AppError` exceptions bubble up naturally — the formatter handles them.

```typescript
// In a service
throw new NotFoundError('User not found', { userId: id });

// In a use case
throw new BusinessRuleError('Cannot delete workspace with active projects');
```

---

## 5. Drizzle in Serverless

### Connection Management

Use a singleton pattern for the Drizzle client to reuse connections during warm invocations.

```typescript
// shared/infra/db/drizzle.ts

import { drizzle } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';
import * as schema from './schema';

const globalForDb = globalThis as unknown as {
  pool: Pool | undefined;
};

const pool =
  globalForDb.pool ??
  new Pool({
    connectionString: process.env.DATABASE_URL,
    max: 10, // Adjust based on serverless concurrency
  });

if (process.env.NODE_ENV !== 'production') {
  globalForDb.pool = pool;
}

export const db = drizzle(pool, { schema });
```

### Container Integration

```typescript
// shared/infra/container.ts

import { db } from './db/drizzle';
import { TransactionManager, DrizzleTransactionManager } from '@/shared/kernel/transaction';

export interface Container {
  db: typeof db;
  transactionManager: TransactionManager;
}

let container: Container | null = null;

export function getContainer(): Container {
  if (!container) {
    container = {
      db,
      transactionManager: new DrizzleTransactionManager(db),
    };
  }
  return container;
}
```

---

## 6. Folder Structure

```
src/
├─ app/
│  └─ api/
│     └─ trpc/
│        └─ [trpc]/
│           └─ route.ts      # tRPC HTTP handler
│
├─ shared/
│  ├─ kernel/
│  │  ├─ transaction.ts
│  │  └─ errors.ts
│  ├─ infra/
│  │  ├─ db/
│  │  │  ├─ drizzle.ts       # Drizzle client
│  │  │  └─ schema.ts        # Drizzle schema definitions
│  │  ├─ trpc/
│  │  │  ├─ trpc.ts          # tRPC initialization
│  │  │  ├─ root.ts          # Root router
│  │  │  └─ context.ts       # Request context
│  │  └─ container.ts
│  └─ utils/
│
├─ modules/
│  └─ user/
│     ├─ user.router.ts      # tRPC router (replaces controller + routes)
│     ├─ dtos/
│     ├─ use-cases/
│     ├─ factories/
│     ├─ services/
│     └─ repositories/
│
├─ drizzle/
│  └─ migrations/            # Drizzle migrations
│
└─ trpc/
   └─ client.ts              # Client-side tRPC setup
```

---

## 7. Key Differences from Generic Architecture

| Aspect | Generic | Next.js + tRPC |
|--------|---------|----------------|
| HTTP Layer | Controllers + Routes | tRPC Routers + Procedures |
| Request Validation | Manual Zod in controller | Built into tRPC `.input()` |
| Error Mapping | `handleError` function | tRPC `errorFormatter` |
| DB Client | Created in container | Global singleton for serverless |

---

## 8. Checklist

- [ ] Drizzle client uses global singleton pattern
- [ ] Factories use lazy singleton pattern
- [ ] tRPC routers follow: writes → use cases, reads → services
- [ ] Error formatter maps `AppError` to tRPC errors
- [ ] Input validation uses Zod schemas in `.input()`
