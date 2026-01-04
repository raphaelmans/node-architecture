# Authentication & Authorization

> Authentication and authorization patterns including session management, protected procedures, and authorization checks.

## Principles

- Authentication is handled at the middleware layer
- Authorization is handled at the service/use case layer
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

### Auth Middleware

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

```typescript
// shared/infra/trpc/trpc.ts

import { authMiddleware } from './middleware/auth.middleware';
import { loggerMiddleware } from './middleware/logger.middleware';

const baseProcedure = t.procedure.use(loggerMiddleware);

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

import { z } from 'zod';
import { router, publicProcedure, protectedProcedure } from '@/shared/infra/trpc';
import { makeAuthUseCase } from './factories/auth.factory';
import { createCookie, createExpiredCookie, SESSION_COOKIE_NAME } from '@/shared/infra/auth/cookies';

const LoginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

const RegisterSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  password: z.string().min(8).max(100),
});

export const authRouter = router({
  login: publicProcedure
    .input(LoginSchema)
    .mutation(async ({ input }) => {
      const result = await makeAuthUseCase().login(input);

      return {
        user: result.user,
        cookie: createCookie(SESSION_COOKIE_NAME, result.token),
      };
    }),

  register: publicProcedure
    .input(RegisterSchema)
    .mutation(async ({ input }) => {
      const result = await makeAuthUseCase().register(input);

      return {
        user: result.user,
        cookie: createCookie(SESSION_COOKIE_NAME, result.token),
      };
    }),

  logout: protectedProcedure.mutation(async () => {
    return {
      success: true,
      cookie: createExpiredCookie(SESSION_COOKIE_NAME),
    };
  }),

  me: protectedProcedure.query(async ({ ctx }) => {
    return {
      id: ctx.session.userId,
      email: ctx.session.email,
      role: ctx.session.role,
    };
  }),
});
```

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
// shared/infra/trpc/middleware/authorize.middleware.ts

import { TRPCError } from '@trpc/server';
import { middleware } from '../trpc';
import { hasPermission, type Permission } from '@/shared/kernel/auth';

export function requirePermission(permission: Permission) {
  return middleware(async ({ ctx, next }) => {
    if (!ctx.session) {
      throw new TRPCError({
        code: 'UNAUTHORIZED',
        message: 'Authentication required',
      });
    }

    if (!hasPermission(ctx.session.role, permission)) {
      throw new TRPCError({
        code: 'FORBIDDEN',
        message: 'Insufficient permissions',
      });
    }

    return next();
  });
}
```

### Using Authorization in Routers

```typescript
// modules/user/user.router.ts

import { requirePermission } from '@/shared/infra/trpc/middleware/authorize.middleware';

export const userRouter = router({
  // Any authenticated user can read
  list: protectedProcedure
    .query(async () => {
      return makeUserService().list();
    }),

  // Only admins can delete users
  delete: protectedProcedure
    .use(requirePermission('manage_users'))
    .input(z.object({ id: z.string() }))
    .mutation(async ({ input }) => {
      await makeUserService().delete(input.id);
      return { success: true };
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
      // Service handles authorization
      return makeWorkspaceService().getById(input.id, ctx.userId);
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
├─ shared/
│  ├─ kernel/
│  │  └─ auth.ts              # Session, UserRole, Permission types
│  ├─ infra/
│  │  ├─ auth/
│  │  │  ├─ session.ts        # JWT/DB session management
│  │  │  └─ cookies.ts        # Cookie utilities
│  │  └─ trpc/
│  │     ├─ context.ts        # Context creation with session
│  │     ├─ trpc.ts           # Procedure definitions
│  │     └─ middleware/
│  │        ├─ auth.middleware.ts       # Authentication check
│  │        └─ authorize.middleware.ts  # Permission check
│  └─ utils/
│     └─ password.ts          # bcrypt utilities
│
├─ modules/
│  └─ auth/
│     ├─ auth.router.ts       # Login, register, logout, me
│     ├─ use-cases/
│     │  └─ auth.use-case.ts  # Authentication logic
│     └─ factories/
│        └─ auth.factory.ts   # Auth use case factory
```

## Security Checklist

### Authentication
- [ ] Passwords hashed with bcrypt (cost factor >= 12) or argon2
- [ ] Session tokens are cryptographically secure
- [ ] Tokens stored in HTTP-only cookies
- [ ] Cookies use Secure flag in production
- [ ] SameSite attribute set to 'lax' or 'strict'
- [ ] Generic error messages prevent user enumeration
- [ ] Failed login attempts are logged

### Session Management
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
