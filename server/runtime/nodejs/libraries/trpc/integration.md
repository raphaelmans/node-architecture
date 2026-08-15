# tRPC Integration

> Next.js serverless deployment with tRPC specifics.

## Scope and Migration Context

- This document is transport-specific to `tRPC`.
- Current production transport is `tRPC`.
- OpenAPI is a planned/parallel transport for migration scenarios.
- Shared API contracts remain `Zod`-first and transport-agnostic.

Use these docs together:

- `server/core/api-contracts-zod-first.md` (canonical contracts)
- `server/runtime/nodejs/libraries/openapi/README.md` (OpenAPI adapter flow)
- `server/runtime/nodejs/libraries/openapi/parity-testing.md` (coexistence quality gate)

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
import {
  GetUserController,
  ListUsersController,
  CreateUserController,
  RegisterUserController,
} from '../controllers';

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
    makeNotificationOutbox(),
    getContainer().transactionManager,
  );
}

export const makeGetUserController = () =>
  new GetUserController(makeUserService());

export const makeListUsersController = () =>
  new ListUsersController(makeUserService());

export const makeCreateUserController = () =>
  new CreateUserController(makeUserService());

export const makeRegisterUserController = () =>
  new RegisterUserController(makeRegisterUserUseCase());
```

## tRPC Setup

### Base tRPC Configuration

```typescript
// shared/infra/trpc/trpc.ts

import { initTRPC, TRPCError } from '@trpc/server';
import {
  AppError,
  AuthenticationError,
  type AppErrorKind,
} from '@/shared/kernel/errors';
import {
  getPublicErrorMessage,
  canExposeErrorDetails,
  GENERIC_PUBLIC_ERROR_MESSAGE,
} from '@/shared/kernel/public-error';
import { appLogger } from '@/shared/infra/logger';
import { APP_ATTRIBUTES } from '@/shared/infra/observability/attributes';
import type { Context } from './context';

/**
 * Keep only `path` and `zodError` from tRPC shape data.
 * Keeps only explicitly public fields and strips all other metadata.
 */
function pickPublicTrpcShapeData(
  shapeData: Record<string, unknown>,
): Record<string, unknown> {
  const picked: Record<string, unknown> = {};
  if ('path' in shapeData) picked.path = shapeData.path;
  if ('zodError' in shapeData) picked.zodError = shapeData.zodError;
  return picked;
}

const t = initTRPC.context<Context>().create({
  errorFormatter({ error, shape, ctx }) {
    const cause = error.cause;
    const requestId = ctx?.requestId ?? 'unknown';

    if (cause instanceof AppError) {
      appLogger.warn(
        {
          err: cause,
          'error.type': cause.code,
          [APP_ATTRIBUTES.errorDetails]: cause.details,
        },
        cause.message,
      );

      return {
        ...shape,
        message: getPublicErrorMessage(cause),
        data: {
          ...pickPublicTrpcShapeData(shape.data),
          appCode: cause.code,
          requestId,
          ...(canExposeErrorDetails(cause) &&
            cause.publicDetails && { details: cause.publicDetails }),
        },
      };
    }

    // Input validation error — preserve tRPC's BAD_REQUEST shape (Zod messages)
    if (error.code === 'BAD_REQUEST') {
      appLogger.warn(
        { err: error, 'error.type': 'BAD_REQUEST' },
        'Input validation failed',
      );

      return {
        ...shape,
        data: {
          ...pickPublicTrpcShapeData(shape.data),
          requestId,
        },
      };
    }

    // Unknown error — never expose internals
    appLogger.error(
      { err: error, 'error.type': error.constructor.name },
      'Unexpected error',
    );

    return {
      ...shape,
      message: GENERIC_PUBLIC_ERROR_MESSAGE,
      data: {
        ...pickPublicTrpcShapeData(shape.data),
        appCode: 'INTERNAL_ERROR',
        requestId,
      },
    };
  },
});

export const router = t.router;
export const middleware = t.middleware;
```

Transport note:

- Keep the tRPC transport code on the error envelope itself.
- Do not duplicate transport status/code metadata inside `shape.data`.
- Use `shape.data.appCode` for application-specific error codes.

### Context Creation

> **Note:** For Supabase Auth implementation, see [Supabase Auth](../supabase/auth.md#trpc-context). The context includes additional `cookies` and `origin` fields for Supabase SSR.

```typescript
// shared/infra/trpc/context.ts

import { randomUUID } from 'crypto';
import type { FetchCreateContextFnOptions } from '@trpc/server/adapters/fetch';
import type { Session } from '@/shared/kernel/auth';
import type { AppLogger } from '@/shared/kernel/logger';
import { appLogger } from '@/shared/infra/logger';
import {
  getObservabilityContext,
  getTrustedClientIdentifier,
  getTrustedRequestId,
} from '@/shared/infra/observability';

export interface Context {
  requestId: string;
  session: Session | null;
  userId: string | null;
  clientIdentifier: string | null;
  clientIdentifierSource: "authenticated_user" | "trusted_network" | null;
  log: AppLogger;
  // For Supabase Auth, also include:
  // cookies: CookieMethodsServer;
  // origin: string;
}

export async function createContext(
  opts: FetchCreateContextFnOptions,
): Promise<Context> {
  const { req } = opts;

  const requestId =
    getObservabilityContext()?.requestId ??
    getTrustedRequestId(req.headers) ??
    randomUUID();

  // Session extraction varies by auth provider:
  // - JWT: parse cookie, verify token
  // - Supabase: use createClient with cookies, call getUser()
  const session = null; // Extract from auth provider
  const client = getTrustedClientIdentifier(req.headers);

  return {
    requestId,
    session,
    userId: session?.userId ?? null,
    clientIdentifier: session?.userId ?? client?.value ?? null,
    clientIdentifierSource: session
      ? 'authenticated_user'
      : client?.source ?? null,
    log: appLogger,
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

### Procedure Definitions

**Important:** Define middleware inline in `trpc.ts` to avoid circular dependencies. Do NOT create separate middleware files that import from `trpc.ts`.

```typescript
// shared/infra/trpc/trpc.ts (continued)

export const router = t.router;
export const middleware = t.middleware;

const TRPC_CODE_BY_KIND = {
  validation: 'BAD_REQUEST',
  authentication: 'UNAUTHORIZED',
  authorization: 'FORBIDDEN',
  not_found: 'NOT_FOUND',
  conflict: 'CONFLICT',
  business_rule: 'UNPROCESSABLE_CONTENT',
  rate_limit: 'TOO_MANY_REQUESTS',
  internal: 'INTERNAL_SERVER_ERROR',
  bad_gateway: 'BAD_GATEWAY',
  unavailable: 'SERVICE_UNAVAILABLE',
  timeout: 'GATEWAY_TIMEOUT',
} as const satisfies Record<AppErrorKind, string>;

const appErrorMiddleware = t.middleware(async ({ ctx, next }) => {
  try {
    return await next({ ctx });
  } catch (error) {
    if (error instanceof AppError) {
      throw new TRPCError({
        code: TRPC_CODE_BY_KIND[error.kind],
        message: error.message,
        cause: error,
      });
    }
    throw error;
  }
});

/**
 * Logger middleware - request lifecycle tracing.
 * Defined inline to avoid circular dependency with middleware exports.
 */
const loggerMiddleware = t.middleware(async ({ ctx, next, path, type }) => {
  const start = Date.now();

  ctx.log.info(
    {
      'otel.event.name': 'rpc.request.started',
      'rpc.system': 'trpc',
      'rpc.method': path,
      [APP_ATTRIBUTES.operationType]: type,
    },
    'Request started',
  );

  try {
    const result = await next({ ctx });
    const duration = Date.now() - start;

    ctx.log.info(
      {
        'otel.event.name': 'rpc.request.completed',
        'rpc.system': 'trpc',
        'rpc.method': path,
        [APP_ATTRIBUTES.operationType]: type,
        [APP_ATTRIBUTES.durationMs]: duration,
        [APP_ATTRIBUTES.operationOutcome]: 'success',
      },
      'Request completed',
    );

    return result;
  } catch (error) {
    const duration = Date.now() - start;

    ctx.log.info(
      {
        'otel.event.name': 'rpc.request.failed',
        'rpc.system': 'trpc',
        'rpc.method': path,
        [APP_ATTRIBUTES.operationType]: type,
        [APP_ATTRIBUTES.durationMs]: duration,
        [APP_ATTRIBUTES.operationOutcome]: 'error',
      },
      'Request failed',
    );

    throw error;
  }
});

/**
 * Auth middleware - requires valid session.
 */
const authMiddleware = t.middleware(async ({ ctx, next }) => {
  if (!ctx.session || !ctx.userId) {
    throw new TRPCError({
      code: 'UNAUTHORIZED',
      message: 'Authentication required',
      cause: new AuthenticationError('Authentication required'),
    });
  }

  return next({
    ctx: ctx as AuthenticatedContext,
  });
});

// Error mapping is outermost so it also handles errors from later middleware.
const baseProcedure = t.procedure
  .use(appErrorMiddleware)
  .use(loggerMiddleware);

export const publicProcedure = baseProcedure;

export const protectedProcedure = baseProcedure.use(authMiddleware);
```

## Transport-Specific Additions

### Rate Limiting

Apply rate limits in tRPC middleware/procedure factories, not inside services.

See:

- [tRPC Rate Limiting](./rate-limiting.md)
- [Core Rate Limiting Contract](../../../../core/rate-limiting.md)

### Non-JSON Content (FormData, File, Blob)

tRPC v11 supports non-JSON content types natively. Use link splitting so non-JSON operations bypass batching:

- JSON payloads → `httpBatchLink`
- Non-JSON payloads (`FormData`, `File`, `Blob`) → `httpLink`

In Next.js implementations, canonical transport guidance lives at:

- [Next.js FormData Transport](../../metaframeworks/nextjs/formdata-transport.md)

## Router Structure

tRPC routers map to modules. Public procedures call controller factories only.

```typescript
// modules/user/user.router.ts

import { router, publicProcedure, protectedProcedure } from '@/shared/infra/trpc';
import { z } from 'zod';
import {
  CreateUserInputSchema,
  CreateUserResponseSchema,
  GetUserResponseSchema,
  ListUsersInputSchema,
  ListUsersResponseSchema,
  RegisterUserInputSchema,
  RegisterUserResponseSchema,
} from './shared/contracts';
import {
  makeGetUserController,
  makeListUsersController,
  makeCreateUserController,
  makeRegisterUserController,
} from './factories/user.factory';
import { wrapResponse } from '@/shared/utils/response';

export const userRouter = router({
  // Framework adapter → Controller → Service
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input, ctx }) => {
      const result = await makeGetUserController().execute(input, toActor(ctx.session));
      const response = GetUserResponseSchema.parse(result);
      return wrapResponse(response);
    }),

  // Framework adapter → Controller → Service
  list: protectedProcedure
    .input(ListUsersInputSchema)
    .query(async ({ input, ctx }) => {
      const page = await makeListUsersController().execute(input, toActor(ctx.session));
      return {
        ...page,
        data: ListUsersResponseSchema.parse(page.data),
      };
    }),

  // Framework adapter → Controller → Service (service owns transaction)
  create: protectedProcedure
    .input(CreateUserInputSchema)
    .mutation(async ({ input, ctx }) => {
      const result = await makeCreateUserController().execute(input, toActor(ctx.session));
      const response = CreateUserResponseSchema.parse(result);
      return wrapResponse(response);
    }),

  // Framework adapter → Controller → Use Case
  register: publicProcedure
    .input(RegisterUserInputSchema)
    .mutation(async ({ input }) => {
      const result = await makeRegisterUserController().execute(input);
      const response = RegisterUserResponseSchema.parse(result);
      return wrapResponse(response);
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
import { withRequestObservability } from '@/shared/infra/observability';

const handler = (req: Request) =>
  withRequestObservability(req, () =>
    fetchRequestHandler({
      endpoint: '/api/trpc',
      req,
      router: appRouter,
      createContext,
    }),
  );

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

Use a singleton pattern with `postgres.js` driver for better serverless compatibility.

```typescript
// shared/infra/db/drizzle.ts

import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

const createDatabase = () => {
  const isVercel = process.env.VERCEL === "1";
  const connectionString = process.env.DATABASE_URL;

  if (!connectionString) {
    throw new Error("DATABASE_URL is not defined");
  }

  const client = postgres(connectionString, {
    connect_timeout: 30,
    idle_timeout: 20 * 60,
    max_lifetime: 60 * 30,
    max: isVercel ? 5 : 10, // Lower for serverless
    prepare: false,
  });

  return drizzle({ client, casing: "snake_case", schema });
};

// Singleton pattern for development hot reload
const db = global.__db ?? createDatabase();

if (process.env.NODE_ENV !== "production") {
  global.__db = db;
}

declare global {
  var __db: ReturnType<typeof createDatabase> | undefined;
}

export type AppDatabase = typeof db;
export { db };
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
│  │  │  ├─ trpc.ts          # tRPC init + middleware (inline)
│  │  │  ├─ root.ts          # Root router
│  │  │  └─ context.ts       # Request context
│  │  └─ container.ts
│  └─ utils/
│
├─ modules/
│  └─ user/
│     ├─ user.router.ts      # tRPC router
│     ├─ controllers/        # Framework-neutral capability boundary
│     ├─ shared/
│     │  └─ contracts/       # Browser-safe public input/response schemas
│     ├─ dtos/               # Server-only commands (optional)
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
| Framework adapter | Next.js/OpenAPI route handler | tRPC router + procedure |
| Portable boundary | Capability controller | Same capability controller |
| Request validation | Zod in route adapter | Built into tRPC `.input()` |
| Error Mapping | `handleError` function | Shared error middleware + `errorFormatter` |
| DB Client | Created in container | Global singleton for serverless |

## tRPC vs OpenAPI (Important)

- tRPC procedures are RPC-style and type-coupled to TypeScript clients.
- OpenAPI endpoints are HTTP resource operations with explicit status/verb/path contracts.
- Both must call the same capability controller and share Zod input/response contracts.
- During coexistence, run parity tests before shifting traffic between transports.

## Checklist

- [ ] Drizzle client uses global singleton pattern
- [ ] Factories use lazy singleton pattern
- [ ] Shared contract schemas are imported from canonical Zod definitions
- [ ] tRPC context includes `requestId`, `session`, `log`
- [ ] Logger middleware logs request lifecycle
- [ ] Auth middleware narrows context to `AuthenticatedContext`
- [ ] Shared middleware maps `AppError.kind` to a tRPC code once
- [ ] Error formatter sanitizes messages/details and adds `appCode` + `requestId`
- [ ] Input validation uses Zod schemas in `.input()`
- [ ] Every public procedure calls one framework-neutral controller factory
- [ ] Controllers follow: simple operations → one service; orchestration → one use case
- [ ] Root router aggregates all module routers
- [ ] If OpenAPI also exposes the capability, parity tests are present
