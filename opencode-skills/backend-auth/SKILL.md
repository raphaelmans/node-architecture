---
name: backend-auth
description: Implement authentication and authorization with protected procedures, RBAC, resource-level access control, and session management in Next.js + tRPC projects
---

# Authentication & Authorization

Use this skill when implementing auth, protecting routes, or adding permission checks.

## Architecture

| Component | Location | Responsibility |
|-----------|----------|----------------|
| Session types | `shared/kernel/auth.ts` | Session, UserRole, Permission |
| Context creation | `shared/infra/trpc/context.ts` | Extract session from request |
| Auth middleware | `shared/infra/trpc/middleware/auth.middleware.ts` | Require authentication |
| Authz middleware | `shared/infra/trpc/middleware/authorize.middleware.ts` | Check permissions |
| Auth router | `modules/auth/auth.router.ts` | Login, logout, register |

## Adding Protected Endpoints

### Use `protectedProcedure`

```typescript
import { protectedProcedure } from '@/shared/infra/trpc'

export const entityRouter = router({
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input, ctx }) => {
      // ctx.session is guaranteed to exist
      // ctx.userId is guaranteed to be a string
      const entity = await makeEntityService().findById(input.id)
      return wrapResponse(entity)
    }),
})
```

## Role-Based Access Control (RBAC)

### 1. Define Roles and Permissions

```typescript
// shared/kernel/auth.ts
export type UserRole = 'admin' | 'member' | 'viewer'

export const ROLE_PERMISSIONS = {
  admin: ['read', 'write', 'delete', 'manage_users', 'manage_settings'],
  member: ['read', 'write'],
  viewer: ['read'],
} as const

export type Permission = (typeof ROLE_PERMISSIONS)[keyof typeof ROLE_PERMISSIONS][number]

export function hasPermission(role: UserRole, permission: Permission): boolean {
  return (ROLE_PERMISSIONS[role] as readonly string[]).includes(permission)
}
```

### 2. Permission Middleware

```typescript
// shared/infra/trpc/middleware/authorize.middleware.ts
import { TRPCError } from '@trpc/server'
import { middleware } from '../trpc'
import { hasPermission, type Permission } from '@/shared/kernel/auth'

export function requirePermission(permission: Permission) {
  return middleware(async ({ ctx, next }) => {
    if (!ctx.session) {
      throw new TRPCError({ code: 'UNAUTHORIZED', message: 'Authentication required' })
    }

    if (!hasPermission(ctx.session.role, permission)) {
      throw new TRPCError({ code: 'FORBIDDEN', message: 'Insufficient permissions' })
    }

    return next()
  })
}
```

### 3. Use in Routers

```typescript
import { requirePermission } from '@/shared/infra/trpc/middleware/authorize.middleware'

export const userRouter = router({
  // Any authenticated user
  list: protectedProcedure.query(async () => {
    return makeUserService().list()
  }),

  // Only admins
  delete: protectedProcedure
    .use(requirePermission('manage_users'))
    .input(z.object({ id: z.string().uuid() }))
    .mutation(async ({ input }) => {
      await makeUserService().delete(input.id)
      return { success: true }
    }),
})
```

## Resource-Level Authorization

Handle in the service layer:

### 1. Access Check in Service

```typescript
export class WorkspaceService implements IWorkspaceService {
  async assertAccess(workspaceId: string, userId: string): Promise<void> {
    const member = await this.workspaceMemberRepository.findByUserAndWorkspace(
      userId,
      workspaceId
    )

    if (!member) {
      throw new WorkspaceAccessDeniedError(workspaceId, userId)
    }
  }

  async getById(workspaceId: string, userId: string): Promise<Workspace> {
    await this.assertAccess(workspaceId, userId)

    const workspace = await this.workspaceRepository.findById(workspaceId)
    if (!workspace) {
      throw new WorkspaceNotFoundError(workspaceId)
    }

    return workspace
  }
}
```

### 2. Pass userId from Router

```typescript
export const workspaceRouter = router({
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input, ctx }) => {
      return makeWorkspaceService().getById(input.id, ctx.userId)
    }),
})
```

### 3. Authorization Errors

```typescript
export class WorkspaceAccessDeniedError extends AuthorizationError {
  readonly code = 'WORKSPACE_ACCESS_DENIED'

  constructor(workspaceId: string, userId: string) {
    super('Access to workspace denied', { workspaceId, userId })
  }
}
```

## Session Management

### JWT-Based Sessions

```typescript
// shared/infra/auth/session.ts
import { SignJWT, jwtVerify } from 'jose'
import type { Session } from '@/shared/kernel/auth'

export async function createSessionToken(session: Session): Promise<string> {
  const secret = new TextEncoder().encode(config.auth.jwtSecret)

  return new SignJWT({
    userId: session.userId,
    email: session.email,
    role: session.role,
  })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(config.auth.sessionDuration)
    .sign(secret)
}

export async function verifySessionToken(token: string): Promise<Session | null> {
  try {
    const secret = new TextEncoder().encode(config.auth.jwtSecret)
    const { payload } = await jwtVerify(token, secret)
    return {
      userId: payload.userId as string,
      email: payload.email as string,
      role: payload.role as Session['role'],
    }
  } catch {
    return null
  }
}
```

### Auth Router

```typescript
export const authRouter = router({
  login: publicProcedure.input(LoginSchema).mutation(async ({ input }) => {
    const result = await makeAuthUseCase().login(input)
    return {
      user: result.user,
      cookie: createCookie(SESSION_COOKIE_NAME, result.token),
    }
  }),

  logout: protectedProcedure.mutation(async () => {
    return {
      success: true,
      cookie: createExpiredCookie(SESSION_COOKIE_NAME),
    }
  }),

  me: protectedProcedure.query(async ({ ctx }) => {
    return {
      id: ctx.session.userId,
      email: ctx.session.email,
      role: ctx.session.role,
    }
  }),
})
```

## Checklist

### Authentication
- [ ] Passwords hashed with bcrypt (cost >= 12) or argon2
- [ ] Session tokens cryptographically secure
- [ ] Tokens stored in HTTP-only cookies
- [ ] Secure flag in production
- [ ] SameSite attribute set
- [ ] Generic error messages (prevent enumeration)

### Authorization
- [ ] All protected routes use `protectedProcedure`
- [ ] Permission checks at service layer
- [ ] Resource ownership verified
- [ ] Sensitive operations require re-auth
