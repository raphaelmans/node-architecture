# tRPC Integration

> Next.js serverless deployment with tRPC specifics.

## Runtime Considerations

### Serverless Constraints

- **Cold starts**: Each invocation may spin up a new instance
- **No persistent process**: Long-lived singletons reset between cold starts
- **Warm instances**: Module-level state persists during warm invocations
- **Connection limits**: Database connections must be pooled carefully

### What This Means

- Lazy singletons still work — they're reused during warm starts
- Database connections should use global singleton pattern
- Avoid heavy initialization in request paths

## Factory Pattern for Serverless

Use **module-level lazy singletons** for repositories and services. This reuses instances during warm invocations without cold start penalty.

```typescript
// modules/user/factories/user.factory.ts

import { getContainer } from '@/shared/infra/container';
import { UserRepository } from '../repositories/user.repository';
import { UserService } from '../services/user.service';
import { RegisterUserUseCase } from '../use-cases/register-user.use-case';

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
    userService = new UserService(
      makeUserRepository(),
      getContainer().transactionManager,
    );
  }
  return userService;
}

export function makeRegisterUserUseCase() {
  return new RegisterUserUseCase(
    makeUserService(),
    makeWorkspaceService(),
    makeEmailService(),
    getContainer().transactionManager,
  );
}
```

## tRPC Setup

### Base tRPC Configuration

```typescript
// shared/infra/trpc/trpc.ts

import { initTRPC, TRPCError } from '@trpc/server';
import { AppError } from '@/shared/kernel/errors';
import { logger } from '@/shared/infra/logger';
import type { Context } from './context';

const t = initTRPC.context<Context>().create({
  errorFormatter({ error, shape, ctx }) {
    const cause = error.cause;
    const requestId = ctx?.requestId ?? 'unknown';

    if (cause instanceof AppError) {
      logger.warn(
        {
          err: cause,
          code: cause.code,
          details: cause.details,
          requestId,
        },
        cause.message,
      );

      return {
        ...shape,
        data: {
          ...shape.data,
          code: cause.code,
          requestId,
          details: cause.details,
        },
      };
    }

    logger.error({ err: error, requestId }, 'Unexpected error');

    return {
      ...shape,
      data: {
        ...shape.data,
        code: 'INTERNAL_ERROR',
        requestId,
      },
    };
  },
});

export const router = t.router;
export const middleware = t.middleware;
```

### Context Creation

```typescript
// shared/infra/trpc/context.ts

import { randomUUID } from 'crypto';
import type { FetchCreateContextFnOptions } from '@trpc/server/adapters/fetch';
import type { Session } from '@/shared/kernel/auth';
import { verifySessionToken } from '@/shared/infra/auth/session';
import { createRequestLogger, type Logger } from '@/shared/infra/logger';

export interface Context {
  requestId: string;
  session: Session | null;
  userId: string | null;
  log: Logger;
}

export async function createContext(
  opts: FetchCreateContextFnOptions,
): Promise<Context> {
  const { req } = opts;
  
  const requestId = req.headers.get('x-request-id') ?? randomUUID();
  
  const cookies = parseCookies(req.headers.get('cookie') ?? '');
  const token = cookies['session_token'];
  
  const session = token ? await verifySessionToken(token) : null;
  
  const log = createRequestLogger({
    requestId,
    userId: session?.userId,
  });

  return {
    requestId,
    session,
    userId: session?.userId ?? null,
    log,
  };
}

function parseCookies(cookieHeader: string): Record<string, string> {
  const cookies: Record<string, string> = {};
  
  for (const cookie of cookieHeader.split(';')) {
    const [name, ...rest] = cookie.trim().split('=');
    if (name) {
      cookies[name] = rest.join('=');
    }
  }
  
  return cookies;
}
```

### Middleware

```typescript
// shared/infra/trpc/middleware/auth.middleware.ts

import { TRPCError } from '@trpc/server';
import { middleware } from '../trpc';
import type { AuthenticatedContext } from '../context';

export const authMiddleware = middleware(async ({ ctx, next }) => {
  if (!ctx.session || !ctx.userId) {
    throw new TRPCError({
      code: 'UNAUTHORIZED',
      message: 'Authentication required',
    });
  }

  return next({
    ctx: ctx as AuthenticatedContext,
  });
});
```

```typescript
// shared/infra/trpc/middleware/logger.middleware.ts

import { middleware } from '../trpc';

export const loggerMiddleware = middleware(async ({ ctx, next, path, type }) => {
  const start = Date.now();
  
  ctx.log.info({ path, type }, 'Request started');

  try {
    const result = await next();
    const duration = Date.now() - start;
    
    ctx.log.info({ path, type, duration, status: 'success' }, 'Request completed');
    
    return result;
  } catch (error) {
    const duration = Date.now() - start;
    
    ctx.log.info({ path, type, duration, status: 'error' }, 'Request failed');
    
    throw error;
  }
});
```

### Procedure Definitions

```typescript
// shared/infra/trpc/trpc.ts (continued)

import { authMiddleware } from './middleware/auth.middleware';
import { loggerMiddleware } from './middleware/logger.middleware';

const baseProcedure = t.procedure.use(loggerMiddleware);

export const publicProcedure = baseProcedure;

export const protectedProcedure = baseProcedure.use(authMiddleware);
```

## Router Structure

tRPC routers map to modules. Procedures call factories directly.

```typescript
// modules/user/user.router.ts

import { router, publicProcedure, protectedProcedure } from '@/shared/infra/trpc';
import { z } from 'zod';
import { CreateUserSchema } from './dtos/create-user.dto';
import { RegisterUserSchema } from './dtos/register-user.dto';
import { makeUserService, makeRegisterUserUseCase } from './factories/user.factory';
import { wrapResponse } from '@/shared/utils/response';
import { UserNotFoundError } from './errors/user.errors';

export const userRouter = router({
  // Read → Service directly
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input }) => {
      const user = await makeUserService().findById(input.id);
      if (!user) {
        throw new UserNotFoundError(input.id);
      }
      return wrapResponse(omitSensitive(user));
    }),

  // List/filter → Service directly
  list: protectedProcedure
    .input(ListUsersInputSchema)
    .query(async ({ input }) => {
      return makeUserService().list(input);
    }),

  // Simple write → Service (owns transaction)
  create: protectedProcedure
    .input(CreateUserSchema)
    .mutation(async ({ input }) => {
      const user = await makeUserService().create(input);
      return wrapResponse(omitSensitive(user));
    }),

  // Multi-service orchestration → Use Case
  register: publicProcedure
    .input(RegisterUserSchema)
    .mutation(async ({ input }) => {
      return makeRegisterUserUseCase().execute(input);
    }),
});
```

### Root Router

```typescript
// shared/infra/trpc/root.ts

import { router } from './trpc';
import { userRouter } from '@/modules/user/user.router';
import { workspaceRouter } from '@/modules/workspace/workspace.router';
import { authRouter } from '@/modules/auth/auth.router';

export const appRouter = router({
  auth: authRouter,
  user: userRouter,
  workspace: workspaceRouter,
});

export type AppRouter = typeof appRouter;
```

## Next.js API Route Handler

```typescript
// app/api/trpc/[trpc]/route.ts

import { fetchRequestHandler } from '@trpc/server/adapters/fetch';
import { appRouter } from '@/shared/infra/trpc/root';
import { createContext } from '@/shared/infra/trpc/context';

const handler = (req: Request) =>
  fetchRequestHandler({
    endpoint: '/api/trpc',
    req,
    router: appRouter,
    createContext,
  });

export { handler as GET, handler as POST };
```

## Error Handling in tRPC

Map `AppError` to tRPC errors in the error formatter.

### Throwing Errors in Procedures

Let `AppError` exceptions bubble up naturally — the formatter handles them.

```typescript
// In a service
throw new UserNotFoundError(id);

// In a use case
throw new BusinessRuleError('Cannot delete workspace with active projects');
```

### The Error Formatter

The error formatter (shown above) automatically:
- Extracts `AppError` from the cause
- Logs at appropriate level
- Returns structured response with `code`, `requestId`, and `details`

## Drizzle in Serverless

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
import { DrizzleTransactionManager } from './db/transaction';
import type { TransactionManager } from '@/shared/kernel/transaction';

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

## Folder Structure

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
│  │  │  ├─ context.ts       # Request context
│  │  │  └─ middleware/
│  │  │     ├─ auth.middleware.ts
│  │  │     └─ logger.middleware.ts
│  │  └─ container.ts
│  └─ utils/
│
├─ modules/
│  └─ user/
│     ├─ user.router.ts      # tRPC router
│     ├─ dtos/
│     ├─ use-cases/
│     ├─ factories/
│     ├─ services/
│     └─ repositories/
│
├─ drizzle/
│  └─ migrations/
│
└─ trpc/
   └─ client.ts              # Client-side tRPC setup
```

## Key Differences from Generic Architecture

| Aspect | Generic | Next.js + tRPC |
|--------|---------|----------------|
| HTTP Layer | Controllers + Routes | tRPC Routers + Procedures |
| Request Validation | Manual Zod in controller | Built into tRPC `.input()` |
| Error Mapping | `handleError` function | tRPC `errorFormatter` |
| DB Client | Created in container | Global singleton for serverless |

## Checklist

- [ ] Drizzle client uses global singleton pattern
- [ ] Factories use lazy singleton pattern
- [ ] tRPC context includes `requestId`, `session`, `log`
- [ ] Logger middleware logs request lifecycle
- [ ] Auth middleware narrows context to `AuthenticatedContext`
- [ ] Error formatter maps `AppError` to tRPC errors
- [ ] Input validation uses Zod schemas in `.input()`
- [ ] Routers follow: reads → services, writes → services or use cases
- [ ] Root router aggregates all module routers
