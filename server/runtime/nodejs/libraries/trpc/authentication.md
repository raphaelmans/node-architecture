# Authentication & Authorization

> Authentication and authorization patterns including session management, protected procedures, and authorization checks.

## Principles

- Authentication is handled at the middleware layer
- Coarse authentication and role/permission gates may run in transport
  middleware; resource ownership and domain-specific authorization are enforced
  by the service/use-case policy
- Session data is available through tRPC context
- Token management is infrastructure concern, hidden from business logic
- Clear separation between "who are you?" (authn) and "can you do this?" (authz)

## Technology Stack

| Concern | Technology |
|---------|------------|
| Session Management | JWT or database sessions |
| Token Storage | HTTP-only cookies |
| Password Hashing | bcrypt or argon2 |
| tRPC Integration | Context + middleware |

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        Request                              │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Context Creation                          │
│                                                             │
│  1. Extract token from cookie/header                        │
│  2. Verify token (JWT) or load session (DB)                │
│  3. Attach user info to context                            │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│   publicProcedure       │     │   protectedProcedure        │
│                         │     │                             │
│   ctx.userId = null     │     │   Requires ctx.userId       │
│   No auth check         │     │   Throws if not authed      │
└─────────────────────────┘     └─────────────────────────────┘
```

## Session Types

```typescript
// shared/kernel/auth.ts

/**
 * Represents an authenticated user's session data.
 */
export interface Session {
  userId: string;
  email: string;
  role: UserRole;
  workspaceId?: string;
}

/**
 * User roles for authorization.
 */
export type UserRole = 'admin' | 'member' | 'viewer';

/**
 * Session metadata for token management.
 */
export interface SessionMetadata {
  sessionId: string;
  createdAt: Date;
  expiresAt: Date;
  userAgent?: string;
  ipAddress?: string;
}
```

## tRPC Context

### Context Type

```typescript
// shared/infra/trpc/context.ts

import { randomUUID } from 'crypto';
import type { FetchCreateContextFnOptions } from '@trpc/server/adapters/fetch';
import type { Session } from '@/shared/kernel/auth';
import { verifySessionToken } from '@/shared/infra/auth/session';
import {
  createSessionCookieWriter,
  type SessionCookieWriter,
} from '@/shared/infra/auth/session-cookies';
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
  responseCookies: SessionCookieWriter;
}

export async function createContext(
  opts: FetchCreateContextFnOptions,
): Promise<Context> {
  const { req } = opts;

  const requestId =
    getObservabilityContext()?.requestId ??
    getTrustedRequestId(req.headers) ??
    randomUUID();

  const cookies = parseCookies(req.headers.get('cookie') ?? '');
  const token = cookies['session_token'];

  const session = token ? await verifySessionToken(token) : null;
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
    responseCookies: createSessionCookieWriter(),
  };
}
```

### Authenticated Context Type

```typescript
// shared/infra/trpc/context.ts (continued)

/**
 * Context with guaranteed authenticated session.
 * Used by protectedProcedure after auth middleware runs.
 */
export interface AuthenticatedContext extends Context {
  session: Session;
  userId: string;
}

export function isAuthenticated(ctx: Context): ctx is AuthenticatedContext {
  return ctx.session !== null && ctx.userId !== null;
}
```

## tRPC Procedures

### Procedure Definitions

```typescript
// shared/infra/trpc/trpc.ts

import { TRPCError } from '@trpc/server';
import { AuthenticationError } from '@/shared/kernel/errors';
import { APP_ATTRIBUTES } from '@/shared/infra/observability/attributes';

// Middleware defined inline to avoid circular dependencies
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
    ctx.log.info(
      {
        'otel.event.name': 'rpc.request.completed',
        'rpc.system': 'trpc',
        'rpc.method': path,
        [APP_ATTRIBUTES.operationType]: type,
        [APP_ATTRIBUTES.durationMs]: Date.now() - start,
        [APP_ATTRIBUTES.operationOutcome]: 'success',
      },
      'Request completed',
    );
    return result;
  } catch (error) {
    ctx.log.info(
      {
        'otel.event.name': 'rpc.request.failed',
        'rpc.system': 'trpc',
        'rpc.method': path,
        [APP_ATTRIBUTES.operationType]: type,
        [APP_ATTRIBUTES.durationMs]: Date.now() - start,
        [APP_ATTRIBUTES.operationOutcome]: 'error',
      },
      'Request failed',
    );
    throw error;
  }
});

const authMiddleware = t.middleware(async ({ ctx, next }) => {
  if (!ctx.session || !ctx.userId) {
    throw new TRPCError({
      code: 'UNAUTHORIZED',
      message: 'Authentication required',
      cause: new AuthenticationError('Authentication required'),
    });
  }
  return next({ ctx: ctx as AuthenticatedContext });
});

// `baseProcedure` is defined in the shared tRPC setup and already applies
// central `AppError.kind` mapping before `loggerMiddleware`.

/**
 * Public procedure - no authentication required.
 * Use for: login, register, public data
 */
export const publicProcedure = baseProcedure;

/**
 * Protected procedure - requires valid session.
 * Context is narrowed to AuthenticatedContext.
 */
export const protectedProcedure = baseProcedure.use(authMiddleware);
```

## Session Management

### JWT-Based Sessions

```typescript
// shared/infra/auth/session.ts

import { SignJWT, jwtVerify, type JWTPayload } from 'jose';
import type { Session } from '@/shared/kernel/auth';
import { getConfig } from '@/shared/infra/config';

const config = getConfig();

interface SessionPayload extends JWTPayload {
  userId: string;
  email: string;
  role: string;
  workspaceId?: string;
}

export async function createSessionToken(session: Session): Promise<string> {
  const secret = new TextEncoder().encode(config.auth.jwtSecret);

  const token = await new SignJWT({
    userId: session.userId,
    email: session.email,
    role: session.role,
    workspaceId: session.workspaceId,
  } satisfies SessionPayload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(config.auth.sessionDuration)
    .sign(secret);

  return token;
}

export async function verifySessionToken(token: string): Promise<Session | null> {
  try {
    const secret = new TextEncoder().encode(config.auth.jwtSecret);

    const { payload } = await jwtVerify(token, secret);
    const data = payload as SessionPayload;

    return {
      userId: data.userId,
      email: data.email,
      role: data.role as Session['role'],
      workspaceId: data.workspaceId,
    };
  } catch {
    return null;
  }
}
```

### Database Sessions (Alternative)

For applications requiring session revocation:

```typescript
// shared/infra/db/schema.ts

export const sessions = pgTable('sessions', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  token: text('token').notNull().unique(),
  userAgent: text('user_agent'),
  ipAddress: text('ip_address'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  expiresAt: timestamp('expires_at').notNull(),
  lastActiveAt: timestamp('last_active_at').defaultNow().notNull(),
}, (table) => ({
  userIdIdx: index('sessions_user_id_idx').on(table.userId),
  tokenIdx: index('sessions_token_idx').on(table.token),
}));
```

## Cookie Management

```typescript
// shared/infra/auth/cookies.ts

import { getConfig } from '@/shared/infra/config';

const config = getConfig();

export interface CookieOptions {
  maxAge?: number;
  expires?: Date;
  path?: string;
  domain?: string;
  secure?: boolean;
  httpOnly?: boolean;
  sameSite?: 'strict' | 'lax' | 'none';
}

const SESSION_COOKIE_OPTIONS: CookieOptions = {
  httpOnly: true,
  secure: config.env === 'production',
  sameSite: 'lax',
  path: '/',
  maxAge: 7 * 24 * 60 * 60, // 7 days
};

export function createCookie(
  name: string,
  value: string,
  options: CookieOptions = {},
): string {
  const opts = { ...SESSION_COOKIE_OPTIONS, ...options };

  let cookie = `${name}=${value}`;

  if (opts.maxAge !== undefined) cookie += `; Max-Age=${opts.maxAge}`;
  if (opts.expires) cookie += `; Expires=${opts.expires.toUTCString()}`;
  if (opts.path) cookie += `; Path=${opts.path}`;
  if (opts.domain) cookie += `; Domain=${opts.domain}`;
  if (opts.secure) cookie += '; Secure';
  if (opts.httpOnly) cookie += '; HttpOnly';
  if (opts.sameSite) cookie += `; SameSite=${opts.sameSite}`;

  return cookie;
}

export function createExpiredCookie(name: string): string {
  return createCookie(name, '', { maxAge: 0 });
}

export const SESSION_COOKIE_NAME = 'session_token';
```

## Auth Router

```typescript
// modules/auth/auth.router.ts

import { router, publicProcedure, protectedProcedure } from '@/shared/infra/trpc';
import {
  makeCurrentSessionController,
  makeLoginController,
  makeLogoutController,
  makeRegisterController,
} from './factories/auth.factory';
import { wrapResponse } from '@/shared/utils/response';
import {
  AuthResponseSchema,
  CurrentSessionResponseSchema,
  LoginInputSchema,
  LogoutResponseSchema,
  RegisterUserInputSchema,
} from './shared/contracts';

export const authRouter = router({
  login: publicProcedure
    .input(LoginInputSchema)
    .mutation(async ({ input, ctx }) => {
      const result = await makeLoginController().execute(input);
      ctx.responseCookies.setSession(result.sessionToken);
      return wrapResponse(AuthResponseSchema.parse(result.response));
    }),

  register: publicProcedure
    .input(RegisterUserInputSchema)
    .mutation(async ({ input, ctx }) => {
      const result = await makeRegisterController().execute(input);
      ctx.responseCookies.setSession(result.sessionToken);
      return wrapResponse(AuthResponseSchema.parse(result.response));
    }),

  logout: protectedProcedure.mutation(async ({ ctx }) => {
    await makeLogoutController().execute(toActor(ctx.session));
    ctx.responseCookies.clearSession();
    return wrapResponse(LogoutResponseSchema.parse({ success: true }));
  }),

  me: protectedProcedure.query(async ({ ctx }) => {
    const result = await makeCurrentSessionController().execute(
      toActor(ctx.session),
    );
    const response = CurrentSessionResponseSchema.parse(result);
    return wrapResponse(response);
  }),
});
```

`responseCookies` is transport infrastructure. It writes an HTTP-only, secure, same-site cookie through the framework response mechanism. Session tokens/cookie strings never appear in the shared response payload, logs, or product analytics.

## Authorization Patterns

### Role-Based Access Control (RBAC)

```typescript
// shared/kernel/auth.ts

export const ROLE_PERMISSIONS = {
  admin: ['read', 'write', 'delete', 'manage_users', 'manage_settings'],
  member: ['read', 'write'],
  viewer: ['read'],
} as const;

export type Permission = (typeof ROLE_PERMISSIONS)[keyof typeof ROLE_PERMISSIONS][number];

export function hasPermission(role: UserRole, permission: Permission): boolean {
  return (ROLE_PERMISSIONS[role] as readonly string[]).includes(permission);
}
```

### Authorization Middleware

```typescript
// src/lib/shared/infra/trpc/trpc.ts (continued)

import { hasPermission, type Permission } from '@/shared/kernel/auth';
import {
  AuthenticationError,
  AuthorizationError,
} from '@/shared/kernel/errors';

export function requirePermission(permission: Permission) {
  return t.middleware(async ({ ctx, next }) => {
    if (!ctx.session) {
      throw new AuthenticationError('Authentication required');
    }

    if (!hasPermission(ctx.session.role, permission)) {
      throw new AuthorizationError('Insufficient permissions');
    }

    return next();
  });
}
```

### Using Authorization in Routers

```typescript
// modules/user/user.router.ts

import { requirePermission } from '@/shared/infra/trpc';
import { wrapResponse } from '@/shared/utils/response';
import {
  DeleteUserResponseSchema,
  ListUsersResponseSchema,
} from './shared/contracts';

export const userRouter = router({
  // Any authenticated user can read
  list: protectedProcedure
    .query(async ({ ctx }) => {
      const page = await makeListUsersController().execute({}, toActor(ctx.session));
      return {
        ...page,
        data: ListUsersResponseSchema.parse(page.data),
      };
    }),

  // Only admins can delete users
  delete: protectedProcedure
    .use(requirePermission('manage_users'))
    .input(z.object({ id: z.string() }))
    .mutation(async ({ input, ctx }) => {
      const result = await makeDeleteUserController().execute(input, toActor(ctx.session));
      return wrapResponse(DeleteUserResponseSchema.parse(result));
    }),
});
```

### Resource-Level Authorization

For checking ownership or resource-specific access:

```typescript
// modules/workspace/services/workspace.service.ts

import { WorkspaceAccessDeniedError } from '../errors/workspace.errors';

export class WorkspaceService {
  async assertAccess(workspaceId: string, userId: string): Promise<void> {
    const member = await this.workspaceMemberRepository.findByUserAndWorkspace(
      userId,
      workspaceId,
    );

    if (!member) {
      throw new WorkspaceAccessDeniedError(workspaceId, userId);
    }
  }

  async getById(workspaceId: string, userId: string): Promise<Workspace> {
    await this.assertAccess(workspaceId, userId);

    const workspace = await this.workspaceRepository.findById(workspaceId);
    if (!workspace) {
      throw new WorkspaceNotFoundError(workspaceId);
    }

    return workspace;
  }
}
```

```typescript
// modules/workspace/workspace.router.ts

export const workspaceRouter = router({
  getById: protectedProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input, ctx }) => {
      // Controller delegates resource authorization to the service policy.
      const result = await makeGetWorkspaceController().execute(
        input,
        toActor(ctx.session),
      );
      return wrapResponse(GetWorkspaceResponseSchema.parse(result));
    }),
});
```

## Password Utilities

```typescript
// shared/utils/password.ts

import bcrypt from 'bcrypt';

const SALT_ROUNDS = 12;

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

export async function verifyPassword(
  password: string,
  hash: string,
): Promise<boolean> {
  return bcrypt.compare(password, hash);
}
```

## Folder Structure

```
src/
└─ lib/
   ├─ shared/
   │  ├─ kernel/
   │  │  └─ auth.ts              # Session, UserRole, Permission types
   │  ├─ infra/
   │  │  ├─ auth/
   │  │  │  ├─ session.ts        # JWT/DB session management
   │  │  │  └─ cookies.ts        # Cookie utilities
   │  │  └─ trpc/
   │  │     ├─ context.ts        # Context creation with session
   │  │     └─ trpc.ts           # Procedures + middleware
   │  └─ utils/
   │     └─ password.ts          # bcrypt utilities
   │
   └─ modules/
      └─ auth/
         ├─ auth.router.ts       # Login, register, logout, me
         ├─ controllers/
         ├─ use-cases/
         └─ factories/
```

## Security Checklist

### Authentication Checks
- [ ] Passwords hashed with bcrypt (cost factor >= 12) or argon2
- [ ] Session tokens are cryptographically secure
- [ ] Tokens stored in HTTP-only cookies
- [ ] Cookies use Secure flag in production
- [ ] SameSite attribute set to 'lax' or 'strict'
- [ ] Generic error messages prevent user enumeration
- [ ] Failed login attempts are logged

### Session Checks
- [ ] Sessions have reasonable expiration (7-30 days)
- [ ] Session can be revoked (logout, security events)
- [ ] New session created on login (prevent session fixation)

### Authorization
- [ ] All protected routes require authentication
- [ ] Permission checks at service layer
- [ ] Resource ownership verified before access
- [ ] Sensitive operations require re-authentication

### General
- [ ] HTTPS required in production
- [ ] Rate limiting on auth endpoints
- [ ] Audit logging for security events
