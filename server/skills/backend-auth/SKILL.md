---
name: backend-auth
description: Implements authentication and authorization including protected procedures, RBAC, resource-level access control, and session management. Use when adding authentication, protecting routes, implementing permissions, role-based access, or when the user mentions "auth", "login", "protected", "permissions", "roles", "access control".
---

# Authentication & Authorization

## Overview

| Concern | Location | Responsibility |
|---------|----------|----------------|
| Session types | `shared/kernel/auth.ts` | Session, UserRole, Permission |
| Context creation | `shared/infra/trpc/context.ts` | Extract session from request |
| Auth middleware | `shared/infra/trpc/middleware/auth.middleware.ts` | Require authentication |
| Authz middleware | `shared/infra/trpc/middleware/authorize.middleware.ts` | Check permissions |
| Session management | `shared/infra/auth/session.ts` | JWT/DB sessions |
| Auth router | `modules/auth/auth.router.ts` | Login, logout, register |

## Authentication Flow

```
Request
  → Context creation (extract token, verify, attach session)
  → publicProcedure: No auth check
  → protectedProcedure: Requires valid session
```

## Adding Protected Endpoints

### Use `protectedProcedure`

```typescript
// In any router
import { protectedProcedure } from '@/shared/infra/trpc';

export const entityRouter = router({
  // This requires authentication
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input, ctx }) => {
      // ctx.session is guaranteed to exist
      // ctx.userId is guaranteed to be a string
      const entity = await makeEntityService().findById(input.id);
      return wrapResponse(entity);
    }),
});
```

### Context Types

```typescript
// Public context - session may be null
interface Context {
  requestId: string;
  session: Session | null;
  userId: string | null;
  log: Logger;
}

// Authenticated context - session is guaranteed
interface AuthenticatedContext extends Context {
  session: Session;
  userId: string;
}
```

## Role-Based Access Control (RBAC)

### 1. Define Roles and Permissions

```typescript
// shared/kernel/auth.ts
export type UserRole = 'admin' | 'member' | 'viewer';

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

### 2. Create Permission Middleware

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

### 3. Use in Routers

```typescript
import { requirePermission } from '@/shared/infra/trpc/middleware/authorize.middleware';

export const userRouter = router({
  // Any authenticated user
  list: protectedProcedure
    .query(async () => {
      return makeUserService().list();
    }),

  // Only admins
  delete: protectedProcedure
    .use(requirePermission('manage_users'))
    .input(z.object({ id: z.string().uuid() }))
    .mutation(async ({ input }) => {
      await makeUserService().delete(input.id);
      return { success: true };
    }),
});
```

## Resource-Level Authorization

For checking ownership or resource-specific access, handle in the service layer:

### 1. Create Access Check in Service

```typescript
// modules/workspace/services/workspace.service.ts
export class WorkspaceService implements IWorkspaceService {
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

### 2. Pass userId from Router

```typescript
// modules/workspace/workspace.router.ts
export const workspaceRouter = router({
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input, ctx }) => {
      // Pass userId for authorization
      return makeWorkspaceService().getById(input.id, ctx.userId);
    }),
});
```

### 3. Create Authorization Errors

```typescript
// modules/workspace/errors/workspace.errors.ts
export class WorkspaceAccessDeniedError extends AuthorizationError {
  readonly code = 'WORKSPACE_ACCESS_DENIED';

  constructor(workspaceId: string, userId: string) {
    super('Access to workspace denied', { workspaceId, userId });
  }
}
```

## Session Management

### JWT-Based Sessions

```typescript
// shared/infra/auth/session.ts
import { SignJWT, jwtVerify } from 'jose';
import type { Session } from '@/shared/kernel/auth';
import { getConfig } from '@/shared/infra/config';

const config = getConfig();

export async function createSessionToken(session: Session): Promise<string> {
  const secret = new TextEncoder().encode(config.auth.jwtSecret);
  
  return new SignJWT({
    userId: session.userId,
    email: session.email,
    role: session.role,
    workspaceId: session.workspaceId,
  })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(config.auth.sessionDuration)
    .sign(secret);
}

export async function verifySessionToken(token: string): Promise<Session | null> {
  try {
    const secret = new TextEncoder().encode(config.auth.jwtSecret);
    const { payload } = await jwtVerify(token, secret);
    
    return {
      userId: payload.userId as string,
      email: payload.email as string,
      role: payload.role as Session['role'],
      workspaceId: payload.workspaceId as string | undefined,
    };
  } catch {
    return null;
  }
}
```

### Cookie Management

```typescript
// shared/infra/auth/cookies.ts
const SESSION_COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax' as const,
  path: '/',
  maxAge: 7 * 24 * 60 * 60, // 7 days
};

export const SESSION_COOKIE_NAME = 'session_token';

export function createCookie(name: string, value: string): string {
  const opts = SESSION_COOKIE_OPTIONS;
  let cookie = `${name}=${value}`;
  cookie += `; Max-Age=${opts.maxAge}`;
  cookie += `; Path=${opts.path}`;
  if (opts.secure) cookie += '; Secure';
  cookie += '; HttpOnly';
  cookie += `; SameSite=${opts.sameSite}`;
  return cookie;
}

export function createExpiredCookie(name: string): string {
  return `${name}=; Max-Age=0; Path=/`;
}
```

## Auth Module Implementation

### Auth Router

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

### Auth Use Case

```typescript
// modules/auth/use-cases/auth.use-case.ts
import type { IUserService } from '@/modules/user/services/user.service';
import { AuthenticationError } from '@/shared/kernel/errors';
import { createSessionToken } from '@/shared/infra/auth/session';
import { hashPassword, verifyPassword } from '@/shared/utils/password';

export class AuthUseCase {
  constructor(private userService: IUserService) {}

  async login(input: LoginInput): Promise<AuthResult> {
    const user = await this.userService.findByEmail(input.email);
    
    if (!user) {
      // Generic message to prevent user enumeration
      throw new AuthenticationError('Invalid credentials');
    }

    const valid = await verifyPassword(input.password, user.passwordHash);
    if (!valid) {
      throw new AuthenticationError('Invalid credentials');
    }

    const token = await createSessionToken({
      userId: user.id,
      email: user.email,
      role: user.role,
    });

    return {
      user: omitSensitive(user),
      token,
    };
  }

  async register(input: RegisterInput): Promise<AuthResult> {
    const passwordHash = await hashPassword(input.password);
    
    const user = await this.userService.create({
      email: input.email,
      name: input.name,
      passwordHash,
    });

    const token = await createSessionToken({
      userId: user.id,
      email: user.email,
      role: user.role,
    });

    return {
      user: omitSensitive(user),
      token,
    };
  }
}
```

## Common Patterns

### Requiring Re-authentication for Sensitive Operations

```typescript
// DTO with password confirmation
export const DeleteAccountSchema = z.object({
  password: z.string().min(1),
});

// Router
deleteAccount: protectedProcedure
  .input(DeleteAccountSchema)
  .mutation(async ({ input, ctx }) => {
    // Verify password before sensitive operation
    await makeAuthUseCase().verifyPassword(ctx.userId, input.password);
    await makeUserService().delete(ctx.userId);
    return { success: true };
  }),
```

### Workspace-Scoped Sessions

```typescript
// Session includes workspace context
interface Session {
  userId: string;
  email: string;
  role: UserRole;
  workspaceId?: string;  // Current workspace
}

// Switch workspace
switchWorkspace: protectedProcedure
  .input(z.object({ workspaceId: z.string().uuid() }))
  .mutation(async ({ input, ctx }) => {
    // Verify access
    await makeWorkspaceService().assertAccess(input.workspaceId, ctx.userId);
    
    // Create new session with workspace
    const token = await createSessionToken({
      ...ctx.session,
      workspaceId: input.workspaceId,
    });
    
    return {
      cookie: createCookie(SESSION_COOKIE_NAME, token),
    };
  }),
```

### Checking Multiple Permissions

```typescript
export function requireAnyPermission(...permissions: Permission[]) {
  return middleware(async ({ ctx, next }) => {
    if (!ctx.session) {
      throw new TRPCError({ code: 'UNAUTHORIZED' });
    }

    const hasAny = permissions.some((p) => hasPermission(ctx.session.role, p));
    if (!hasAny) {
      throw new TRPCError({ code: 'FORBIDDEN' });
    }

    return next();
  });
}

// Usage
.use(requireAnyPermission('write', 'manage_users'))
```

## Security Checklist

### Authentication
- [ ] Passwords hashed with bcrypt (cost >= 12) or argon2
- [ ] Session tokens cryptographically secure
- [ ] Tokens stored in HTTP-only cookies
- [ ] Secure flag in production
- [ ] SameSite attribute set
- [ ] Generic error messages (prevent enumeration)
- [ ] Failed logins logged

### Session Management
- [ ] Reasonable expiration (7-30 days)
- [ ] Session revocation on logout
- [ ] New session on login (prevent fixation)

### Authorization
- [ ] All protected routes use `protectedProcedure`
- [ ] Permission checks at service layer
- [ ] Resource ownership verified
- [ ] Sensitive operations require re-auth

See [references/auth-patterns.md](references/auth-patterns.md) for more examples.
