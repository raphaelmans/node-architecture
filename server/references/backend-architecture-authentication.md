# Authentication & Authorization Architecture

> **Purpose**: This document defines the authentication and authorization patterns, including session management, protected procedures, and authorization checks.

---

## 1. Overview

**Principles:**

- Authentication is handled at the middleware layer
- Authorization is handled at the service/use case layer
- Session data is available through tRPC context
- Token management is infrastructure concern, hidden from business logic
- Clear separation between "who are you?" (authn) and "can you do this?" (authz)

**Stack:**

| Concern | Technology |
|---------|------------|
| Session Management | JWT or database sessions |
| Token Storage | HTTP-only cookies |
| Password Hashing | bcrypt or argon2 |
| tRPC Integration | Context + middleware |

---

## 2. Authentication Flow

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
│   ctx.userId = undefined│     │   Requires ctx.userId       │
│   No auth check         │     │   Throws if not authed      │
└─────────────────────────┘     └─────────────────────────────┘
```

---

## 3. Session Types

### 3.1 Type Definitions

```typescript
// shared/kernel/auth.ts

/**
 * Represents an authenticated user's session data.
 * This is the minimal data needed for request processing.
 */
export interface Session {
  userId: string;
  email: string;
  role: UserRole;
  workspaceId?: string;
}

/**
 * User roles for authorization.
 * Extend as needed for your domain.
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

---

## 4. tRPC Context

### 4.1 Context Type

```typescript
// shared/infra/trpc/context.ts

import { randomUUID } from 'crypto';
import type { FetchCreateContextFnOptions } from '@trpc/server/adapters/fetch';
import type { Session } from '@/shared/kernel/auth';
import { verifySessionToken } from '@/shared/infra/auth/session';
import { createRequestLogger, type Logger } from '@/shared/infra/logger';

/**
 * Context available to all tRPC procedures.
 */
export interface Context {
  /** Unique identifier for this request (for logging/tracing) */
  requestId: string;
  
  /** Authenticated session, if available */
  session: Session | null;
  
  /** Convenience accessor for user ID */
  userId: string | null;
  
  /** Request logger with context */
  log: Logger;
}

/**
 * Creates the tRPC context for each request.
 * Extracts and verifies authentication from cookies.
 */
export async function createContext(
  opts: FetchCreateContextFnOptions,
): Promise<Context> {
  const { req } = opts;
  
  // Generate request ID (use incoming header if present for distributed tracing)
  const requestId = req.headers.get('x-request-id') ?? randomUUID();
  
  // Extract session token from cookie
  const cookies = parseCookies(req.headers.get('cookie') ?? '');
  const token = cookies['session_token'];
  
  // Verify session (returns null if invalid/expired)
  const session = token ? await verifySessionToken(token) : null;
  
  // Create request logger with context
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

/**
 * Simple cookie parser.
 */
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

### 4.2 Context Type for Protected Routes

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

/**
 * Type guard to check if context is authenticated.
 */
export function isAuthenticated(ctx: Context): ctx is AuthenticatedContext {
  return ctx.session !== null && ctx.userId !== null;
}
```

---

## 5. tRPC Procedures

### 5.1 Base tRPC Setup

```typescript
// shared/infra/trpc/trpc.ts

import { initTRPC, TRPCError } from '@trpc/server';
import type { Context, AuthenticatedContext } from './context';
import { AppError } from '@/shared/kernel/errors';

/**
 * Initialize tRPC with context and error formatting.
 */
const t = initTRPC.context<Context>().create({
  errorFormatter({ error, shape, ctx }) {
    const cause = error.cause;
    const requestId = ctx?.requestId ?? 'unknown';

    if (cause instanceof AppError) {
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

### 5.2 Auth Middleware

```typescript
// shared/infra/trpc/middleware/auth.middleware.ts

import { TRPCError } from '@trpc/server';
import { middleware } from '../trpc';
import type { AuthenticatedContext } from '../context';

/**
 * Middleware that requires authentication.
 * Throws UNAUTHORIZED if no valid session.
 */
export const authMiddleware = middleware(async ({ ctx, next }) => {
  if (!ctx.session || !ctx.userId) {
    throw new TRPCError({
      code: 'UNAUTHORIZED',
      message: 'Authentication required',
    });
  }

  // Narrow the context type to AuthenticatedContext
  return next({
    ctx: ctx as AuthenticatedContext,
  });
});
```

### 5.3 Logger Middleware

```typescript
// shared/infra/trpc/middleware/logger.middleware.ts

import { middleware } from '../trpc';

/**
 * Middleware that logs request lifecycle.
 */
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

### 5.4 Procedure Definitions

```typescript
// shared/infra/trpc/trpc.ts (continued)

import { authMiddleware } from './middleware/auth.middleware';
import { loggerMiddleware } from './middleware/logger.middleware';

/**
 * Base procedure with logging.
 */
const baseProcedure = t.procedure.use(loggerMiddleware);

/**
 * Public procedure - no authentication required.
 * Use for: login, register, public data
 */
export const publicProcedure = baseProcedure;

/**
 * Protected procedure - requires valid session.
 * Context is narrowed to AuthenticatedContext.
 * Use for: all authenticated operations
 */
export const protectedProcedure = baseProcedure.use(authMiddleware);
```

---

## 6. Session Management

### 6.1 JWT-Based Sessions

```typescript
// shared/infra/auth/session.ts

import { SignJWT, jwtVerify, type JWTPayload } from 'jose';
import type { Session } from '@/shared/kernel/auth';
import { getConfig } from '@/shared/infra/config';

const config = getConfig();

/**
 * JWT payload structure.
 */
interface SessionPayload extends JWTPayload {
  userId: string;
  email: string;
  role: string;
  workspaceId?: string;
}

/**
 * Creates a signed session token (JWT).
 */
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
    .setExpirationTime(config.auth.sessionDuration) // e.g., '7d'
    .sign(secret);

  return token;
}

/**
 * Verifies and decodes a session token.
 * Returns null if token is invalid or expired.
 */
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
    // Token invalid, expired, or tampered
    return null;
  }
}
```

### 6.2 Database Sessions (Alternative)

For applications requiring session revocation or multi-device management:

```typescript
// shared/infra/db/schema.ts

import { pgTable, text, timestamp, index } from 'drizzle-orm/pg-core';

export const sessions = pgTable('sessions', {
  id: text('id').primaryKey(),
  userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
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

```typescript
// shared/infra/auth/session.ts (database version)

import { eq, and, gt } from 'drizzle-orm';
import { sessions, users } from '@/shared/infra/db/schema';
import { db } from '@/shared/infra/db/drizzle';
import type { Session } from '@/shared/kernel/auth';
import { generateId } from '@/shared/utils/id';

/**
 * Creates a new database session.
 */
export async function createSession(
  userId: string,
  metadata?: { userAgent?: string; ipAddress?: string },
): Promise<string> {
  const token = generateId(); // or crypto.randomBytes(32).toString('hex')
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days

  await db.insert(sessions).values({
    id: generateId(),
    userId,
    token,
    userAgent: metadata?.userAgent,
    ipAddress: metadata?.ipAddress,
    expiresAt,
  });

  return token;
}

/**
 * Verifies a session token against the database.
 */
export async function verifySessionToken(token: string): Promise<Session | null> {
  const result = await db
    .select({
      userId: users.id,
      email: users.email,
      role: users.role,
      workspaceId: users.workspaceId,
    })
    .from(sessions)
    .innerJoin(users, eq(sessions.userId, users.id))
    .where(
      and(
        eq(sessions.token, token),
        gt(sessions.expiresAt, new Date()),
      ),
    )
    .limit(1);

  if (!result[0]) {
    return null;
  }

  // Update last active timestamp (fire and forget)
  db.update(sessions)
    .set({ lastActiveAt: new Date() })
    .where(eq(sessions.token, token))
    .catch(() => {}); // Ignore errors

  return result[0] as Session;
}

/**
 * Revokes a specific session.
 */
export async function revokeSession(token: string): Promise<void> {
  await db.delete(sessions).where(eq(sessions.token, token));
}

/**
 * Revokes all sessions for a user.
 */
export async function revokeAllUserSessions(userId: string): Promise<void> {
  await db.delete(sessions).where(eq(sessions.userId, userId));
}
```

---

## 7. Cookie Management

### 7.1 Cookie Utilities

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

/**
 * Default options for session cookie.
 */
const SESSION_COOKIE_OPTIONS: CookieOptions = {
  httpOnly: true,
  secure: config.env === 'production',
  sameSite: 'lax',
  path: '/',
  maxAge: 7 * 24 * 60 * 60, // 7 days in seconds
};

/**
 * Creates a Set-Cookie header value.
 */
export function createCookie(
  name: string,
  value: string,
  options: CookieOptions = {},
): string {
  const opts = { ...SESSION_COOKIE_OPTIONS, ...options };
  
  let cookie = `${name}=${value}`;
  
  if (opts.maxAge !== undefined) {
    cookie += `; Max-Age=${opts.maxAge}`;
  }
  if (opts.expires) {
    cookie += `; Expires=${opts.expires.toUTCString()}`;
  }
  if (opts.path) {
    cookie += `; Path=${opts.path}`;
  }
  if (opts.domain) {
    cookie += `; Domain=${opts.domain}`;
  }
  if (opts.secure) {
    cookie += '; Secure';
  }
  if (opts.httpOnly) {
    cookie += '; HttpOnly';
  }
  if (opts.sameSite) {
    cookie += `; SameSite=${opts.sameSite}`;
  }

  return cookie;
}

/**
 * Creates a cookie that expires immediately (for logout).
 */
export function createExpiredCookie(name: string): string {
  return createCookie(name, '', { maxAge: 0 });
}

/**
 * Session cookie name.
 */
export const SESSION_COOKIE_NAME = 'session_token';
```

---

## 8. Auth Module Implementation

### 8.1 Auth Service

```typescript
// modules/auth/services/auth.service.ts

import type { TransactionManager } from '@/shared/kernel/transaction';
import { AuthenticationError } from '@/shared/kernel/errors';
import type { IUserRepository } from '@/modules/user/repositories/user.repository.interface';
import { createSessionToken, verifySessionToken } from '@/shared/infra/auth/session';
import { verifyPassword, hashPassword } from '@/shared/utils/password';
import { generateId } from '@/shared/utils/id';
import { logger } from '@/shared/infra/logger';

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  name: string;
}

export interface AuthResult {
  token: string;
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
  };
}

export class AuthService {
  constructor(
    private userRepository: IUserRepository,
    private transactionManager: TransactionManager,
  ) {}

  /**
   * Authenticates user and creates session.
   */
  async login(input: LoginInput): Promise<AuthResult> {
    const user = await this.userRepository.findByEmail(input.email);
    
    if (!user) {
      // Use generic message to prevent user enumeration
      throw new AuthenticationError('Invalid email or password');
    }

    const validPassword = await verifyPassword(input.password, user.passwordHash);
    
    if (!validPassword) {
      logger.warn({ userId: user.id }, 'Failed login attempt');
      throw new AuthenticationError('Invalid email or password');
    }

    const token = await createSessionToken({
      userId: user.id,
      email: user.email,
      role: user.role,
    });

    logger.info({ event: 'user.login', userId: user.id }, 'User logged in');

    return {
      token,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        role: user.role,
      },
    };
  }

  /**
   * Registers new user and creates session.
   */
  async register(input: RegisterInput): Promise<AuthResult> {
    const user = await this.transactionManager.run(async (tx) => {
      const existing = await this.userRepository.findByEmail(input.email, { tx });
      
      if (existing) {
        throw new AuthenticationError('Email already registered');
      }

      const passwordHash = await hashPassword(input.password);

      return this.userRepository.create(
        {
          id: generateId(),
          email: input.email,
          name: input.name,
          passwordHash,
          role: 'member',
        },
        { tx },
      );
    });

    const token = await createSessionToken({
      userId: user.id,
      email: user.email,
      role: user.role,
    });

    logger.info({ event: 'user.registered', userId: user.id }, 'User registered');

    return {
      token,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        role: user.role,
      },
    };
  }

  /**
   * Validates current session.
   */
  async validateSession(token: string): Promise<AuthResult['user'] | null> {
    const session = await verifySessionToken(token);
    
    if (!session) {
      return null;
    }

    const user = await this.userRepository.findById(session.userId);
    
    if (!user) {
      return null;
    }

    return {
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
    };
  }
}
```

### 8.2 Auth Router

```typescript
// modules/auth/auth.router.ts

import { z } from 'zod';
import { router, publicProcedure, protectedProcedure } from '@/shared/infra/trpc';
import { makeAuthService } from './factories/auth.factory';
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
  /**
   * Login - returns user and sets session cookie.
   */
  login: publicProcedure
    .input(LoginSchema)
    .mutation(async ({ input, ctx }) => {
      const result = await makeAuthService().login(input);

      // Return cookie header for client to set
      return {
        user: result.user,
        cookie: createCookie(SESSION_COOKIE_NAME, result.token),
      };
    }),

  /**
   * Register - creates user and sets session cookie.
   */
  register: publicProcedure
    .input(RegisterSchema)
    .mutation(async ({ input }) => {
      const result = await makeAuthService().register(input);

      return {
        user: result.user,
        cookie: createCookie(SESSION_COOKIE_NAME, result.token),
      };
    }),

  /**
   * Logout - clears session cookie.
   */
  logout: protectedProcedure.mutation(async ({ ctx }) => {
    // For database sessions, also revoke the session
    // await revokeSession(ctx.session.token);

    return {
      success: true,
      cookie: createExpiredCookie(SESSION_COOKIE_NAME),
    };
  }),

  /**
   * Get current user - validates session.
   */
  me: protectedProcedure.query(async ({ ctx }) => {
    return {
      id: ctx.session.userId,
      email: ctx.session.email,
      role: ctx.session.role,
    };
  }),
});
```

### 8.3 Auth Factory

```typescript
// modules/auth/factories/auth.factory.ts

import { getContainer } from '@/shared/infra/container';
import { makeUserRepository } from '@/modules/user/factories/user.factory';
import { AuthService } from '../services/auth.service';

let authService: AuthService | null = null;

export function makeAuthService(): AuthService {
  if (!authService) {
    authService = new AuthService(
      makeUserRepository(),
      getContainer().transactionManager,
    );
  }
  return authService;
}
```

---

## 9. Authorization Patterns

### 9.1 Role-Based Access Control (RBAC)

```typescript
// shared/kernel/auth.ts (extended)

/**
 * Permissions mapped to roles.
 */
export const ROLE_PERMISSIONS = {
  admin: ['read', 'write', 'delete', 'manage_users', 'manage_settings'],
  member: ['read', 'write'],
  viewer: ['read'],
} as const;

export type Permission = (typeof ROLE_PERMISSIONS)[keyof typeof ROLE_PERMISSIONS][number];

/**
 * Checks if a role has a specific permission.
 */
export function hasPermission(role: UserRole, permission: Permission): boolean {
  return (ROLE_PERMISSIONS[role] as readonly string[]).includes(permission);
}
```

### 9.2 Authorization Middleware

```typescript
// shared/infra/trpc/middleware/authorize.middleware.ts

import { TRPCError } from '@trpc/server';
import { middleware } from '../trpc';
import { hasPermission, type Permission } from '@/shared/kernel/auth';

/**
 * Creates middleware that requires specific permission.
 */
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

### 9.3 Using Authorization in Routers

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

### 9.4 Resource-Level Authorization

For checking ownership or resource-specific access:

```typescript
// modules/workspace/services/workspace.service.ts

import { AuthorizationError } from '@/shared/kernel/errors';
import { WorkspaceAccessDeniedError } from '../errors/workspace.errors';

export class WorkspaceService {
  /**
   * Checks if user has access to workspace.
   */
  async assertAccess(workspaceId: string, userId: string): Promise<void> {
    const member = await this.workspaceMemberRepository.findByUserAndWorkspace(
      userId,
      workspaceId,
    );

    if (!member) {
      throw new WorkspaceAccessDeniedError(workspaceId, userId);
    }
  }

  /**
   * Gets workspace with access check.
   */
  async getById(workspaceId: string, userId: string): Promise<Workspace> {
    await this.assertAccess(workspaceId, userId);
    return this.workspaceRepository.findByIdOrThrow(workspaceId);
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

---

## 10. Password Utilities

```typescript
// shared/utils/password.ts

import bcrypt from 'bcrypt';

const SALT_ROUNDS = 12;

/**
 * Hashes a password using bcrypt.
 */
export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

/**
 * Verifies a password against a hash.
 */
export async function verifyPassword(
  password: string,
  hash: string,
): Promise<boolean> {
  return bcrypt.compare(password, hash);
}
```

---

## 11. Folder Structure

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
│     ├─ services/
│     │  └─ auth.service.ts   # Authentication logic
│     └─ factories/
│        └─ auth.factory.ts   # Auth service factory
```

---

## 12. Security Checklist

### Authentication
- [ ] Passwords hashed with bcrypt (cost factor ≥12) or argon2
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
