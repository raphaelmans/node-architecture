# Authentication Patterns Reference

## tRPC Context Setup

### Context Type Definitions

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

export interface AuthenticatedContext extends Context {
  session: Session;
  userId: string;
}

export function isAuthenticated(ctx: Context): ctx is AuthenticatedContext {
  return ctx.session !== null && ctx.userId !== null;
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
// Middleware defined INLINE to avoid circular dependencies
import { initTRPC, TRPCError } from '@trpc/server';
import { AuthenticationError } from '@/shared/kernel/errors';
import type { Context, AuthenticatedContext } from './context';

const t = initTRPC.context<Context>().create({ /* ... */ });

export const router = t.router;
export const middleware = t.middleware;

// Logger middleware - defined inline
const loggerMiddleware = t.middleware(async ({ ctx, next, type }) => {
  const start = Date.now();
  ctx.log.info({ type }, 'Request started');
  try {
    const result = await next({ ctx });
    ctx.log.info({ duration: Date.now() - start, status: 'success', type }, 'Request completed');
    return result;
  } catch (error) {
    ctx.log.info({ duration: Date.now() - start, status: 'error', type }, 'Request failed');
    throw error;
  }
});

// Auth middleware - defined inline
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

const baseProcedure = t.procedure.use(loggerMiddleware);

export const publicProcedure = baseProcedure;
export const protectedProcedure = baseProcedure.use(authMiddleware);
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

## Session Management Patterns

### JWT Session

```typescript
// shared/infra/auth/session.ts
import { SignJWT, jwtVerify, type JWTPayload } from 'jose';
import type { Session } from '@/shared/kernel/auth';

interface SessionPayload extends JWTPayload {
  userId: string;
  email: string;
  role: string;
  workspaceId?: string;
}

export async function createSessionToken(session: Session): Promise<string> {
  const secret = new TextEncoder().encode(process.env.JWT_SECRET!);
  
  return new SignJWT({
    userId: session.userId,
    email: session.email,
    role: session.role,
    workspaceId: session.workspaceId,
  } satisfies SessionPayload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(secret);
}

export async function verifySessionToken(token: string): Promise<Session | null> {
  try {
    const secret = new TextEncoder().encode(process.env.JWT_SECRET!);
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

### Database Sessions (with Revocation)

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
});

// Session service
export class SessionService {
  async create(userId: string, metadata: SessionMetadata): Promise<string> {
    const token = crypto.randomUUID();
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
    
    await this.sessionRepository.create({
      userId,
      token,
      expiresAt,
      userAgent: metadata.userAgent,
      ipAddress: metadata.ipAddress,
    });
    
    return token;
  }
  
  async verify(token: string): Promise<Session | null> {
    const session = await this.sessionRepository.findByToken(token);
    
    if (!session || session.expiresAt < new Date()) {
      return null;
    }
    
    // Update last active
    await this.sessionRepository.updateLastActive(session.id);
    
    const user = await this.userRepository.findById(session.userId);
    return user ? { userId: user.id, email: user.email, role: user.role } : null;
  }
  
  async revoke(token: string): Promise<void> {
    await this.sessionRepository.delete(token);
  }
  
  async revokeAllForUser(userId: string): Promise<void> {
    await this.sessionRepository.deleteAllForUser(userId);
  }
}
```

## Authorization Patterns

### Permission Middleware Factory

```typescript
// shared/infra/trpc/middleware/authorize.middleware.ts
import { TRPCError } from '@trpc/server';
import { middleware } from '../trpc';
import { hasPermission, type Permission, type UserRole } from '@/shared/kernel/auth';

// Single permission
export function requirePermission(permission: Permission) {
  return middleware(async ({ ctx, next }) => {
    if (!ctx.session) {
      throw new TRPCError({ code: 'UNAUTHORIZED' });
    }
    if (!hasPermission(ctx.session.role, permission)) {
      throw new TRPCError({ code: 'FORBIDDEN' });
    }
    return next();
  });
}

// Any of permissions
export function requireAnyPermission(...permissions: Permission[]) {
  return middleware(async ({ ctx, next }) => {
    if (!ctx.session) {
      throw new TRPCError({ code: 'UNAUTHORIZED' });
    }
    const hasAny = permissions.some((p) => hasPermission(ctx.session!.role, p));
    if (!hasAny) {
      throw new TRPCError({ code: 'FORBIDDEN' });
    }
    return next();
  });
}

// Specific role
export function requireRole(role: UserRole) {
  return middleware(async ({ ctx, next }) => {
    if (!ctx.session) {
      throw new TRPCError({ code: 'UNAUTHORIZED' });
    }
    if (ctx.session.role !== role) {
      throw new TRPCError({ code: 'FORBIDDEN' });
    }
    return next();
  });
}

// Any of roles
export function requireAnyRole(...roles: UserRole[]) {
  return middleware(async ({ ctx, next }) => {
    if (!ctx.session) {
      throw new TRPCError({ code: 'UNAUTHORIZED' });
    }
    if (!roles.includes(ctx.session.role)) {
      throw new TRPCError({ code: 'FORBIDDEN' });
    }
    return next();
  });
}
```

### Resource-Level Authorization Service

```typescript
// modules/workspace/services/workspace-authorization.service.ts
export class WorkspaceAuthorizationService {
  constructor(
    private workspaceMemberRepository: IWorkspaceMemberRepository,
  ) {}

  async assertMember(workspaceId: string, userId: string): Promise<WorkspaceMember> {
    const member = await this.workspaceMemberRepository.findByUserAndWorkspace(
      userId,
      workspaceId,
    );
    
    if (!member) {
      throw new WorkspaceAccessDeniedError(workspaceId, userId);
    }
    
    return member;
  }

  async assertRole(
    workspaceId: string,
    userId: string,
    requiredRoles: WorkspaceRole[],
  ): Promise<WorkspaceMember> {
    const member = await this.assertMember(workspaceId, userId);
    
    if (!requiredRoles.includes(member.role)) {
      throw new WorkspaceInsufficientRoleError(workspaceId, userId, requiredRoles);
    }
    
    return member;
  }

  async assertOwner(workspaceId: string, userId: string): Promise<WorkspaceMember> {
    return this.assertRole(workspaceId, userId, ['owner']);
  }

  async assertAdmin(workspaceId: string, userId: string): Promise<WorkspaceMember> {
    return this.assertRole(workspaceId, userId, ['owner', 'admin']);
  }
}
```

### Using Resource Authorization

```typescript
// In service
export class ProjectService {
  constructor(
    private projectRepository: IProjectRepository,
    private workspaceAuthService: WorkspaceAuthorizationService,
    private transactionManager: TransactionManager,
  ) {}

  async create(data: ProjectInsert, userId: string, ctx?: RequestContext): Promise<Project> {
    const exec = async (ctx: RequestContext) => {
      // Check user has write access to workspace
      await this.workspaceAuthService.assertRole(
        data.workspaceId,
        userId,
        ['owner', 'admin', 'member'],
      );
      
      return this.projectRepository.create(data, ctx);
    };
    
    if (ctx?.tx) return exec(ctx);
    return this.transactionManager.run((tx) => exec({ tx }));
  }

  async delete(id: string, userId: string, ctx?: RequestContext): Promise<void> {
    const exec = async (ctx: RequestContext) => {
      const project = await this.projectRepository.findById(id, ctx);
      if (!project) {
        throw new ProjectNotFoundError(id);
      }
      
      // Only workspace admins can delete
      await this.workspaceAuthService.assertAdmin(project.workspaceId, userId);
      
      await this.projectRepository.delete(id, ctx);
    };
    
    if (ctx?.tx) return exec(ctx);
    return this.transactionManager.run((tx) => exec({ tx }));
  }
}
```

## Multi-Tenant Patterns

### Workspace-Scoped Queries

```typescript
// Repository with workspace scope
export class ProjectRepository {
  async findByWorkspace(
    workspaceId: string,
    filters: ProjectFilters,
    ctx?: RequestContext,
  ): Promise<{ data: Project[]; total: number }> {
    const client = this.getClient(ctx);
    
    // Always filter by workspace
    const conditions = [eq(projects.workspaceId, workspaceId)];
    
    if (filters.status) {
      conditions.push(eq(projects.status, filters.status));
    }
    
    // ... rest of query
  }
}

// Router with workspace from context
getByWorkspace: protectedProcedure
  .input(ListProjectsSchema)
  .query(async ({ input, ctx }) => {
    // Use workspace from session
    if (!ctx.session.workspaceId) {
      throw new TRPCError({ code: 'BAD_REQUEST', message: 'No workspace selected' });
    }
    
    return makeProjectService().list(ctx.session.workspaceId, input);
  }),
```

### Switching Workspace Context

```typescript
// Auth router
switchWorkspace: protectedProcedure
  .input(z.object({ workspaceId: z.string().uuid() }))
  .mutation(async ({ input, ctx }) => {
    // Verify membership
    await makeWorkspaceAuthService().assertMember(input.workspaceId, ctx.userId);
    
    // Issue new token with workspace
    const token = await createSessionToken({
      ...ctx.session,
      workspaceId: input.workspaceId,
    });
    
    return {
      cookie: createCookie(SESSION_COOKIE_NAME, token),
    };
  }),
```

## API Key Authentication (Optional)

```typescript
// For programmatic access
export const apiKeys = pgTable('api_keys', {
  id: uuid('id').primaryKey().defaultRandom(),
  workspaceId: uuid('workspace_id').notNull().references(() => workspaces.id),
  name: text('name').notNull(),
  keyHash: text('key_hash').notNull(),
  keyPrefix: text('key_prefix').notNull(), // First 8 chars for identification
  permissions: text('permissions').array().notNull(),
  expiresAt: timestamp('expires_at'),
  lastUsedAt: timestamp('last_used_at'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// Context creation with API key support
export async function createContext(opts: FetchCreateContextFnOptions): Promise<Context> {
  const { req } = opts;
  const requestId = req.headers.get('x-request-id') ?? randomUUID();
  
  // Check for API key first
  const apiKey = req.headers.get('x-api-key');
  if (apiKey) {
    const session = await verifyApiKey(apiKey);
    if (session) {
      return { requestId, session, userId: session.userId, log: createRequestLogger({ requestId }) };
    }
  }
  
  // Fall back to session cookie
  const cookies = parseCookies(req.headers.get('cookie') ?? '');
  const token = cookies['session_token'];
  const session = token ? await verifySessionToken(token) : null;
  
  return {
    requestId,
    session,
    userId: session?.userId ?? null,
    log: createRequestLogger({ requestId, userId: session?.userId }),
  };
}
```

## Security Best Practices

### Prevent User Enumeration

```typescript
// Login - same error for invalid email or password
async login(input: LoginInput): Promise<AuthResult> {
  const user = await this.userService.findByEmail(input.email);
  
  // Generic message regardless of whether user exists
  if (!user || !(await verifyPassword(input.password, user.passwordHash))) {
    throw new AuthenticationError('Invalid credentials');
  }
  
  // ... create session
}

// Password reset - same response whether email exists or not
async requestPasswordReset(email: string): Promise<void> {
  const user = await this.userService.findByEmail(email);
  
  if (user) {
    await this.sendPasswordResetEmail(user);
  }
  
  // Always return success to prevent enumeration
  logger.info({ email }, 'Password reset requested');
}
```

### Rate Limiting

```typescript
// Middleware for rate limiting
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(5, '1m'), // 5 requests per minute
});

export const rateLimitMiddleware = middleware(async ({ ctx, next }) => {
  const identifier = ctx.userId ?? ctx.requestId;
  const { success, remaining } = await ratelimit.limit(identifier);
  
  if (!success) {
    throw new TRPCError({
      code: 'TOO_MANY_REQUESTS',
      message: 'Rate limit exceeded',
    });
  }
  
  return next();
});

// Apply to sensitive endpoints
login: publicProcedure
  .use(rateLimitMiddleware)
  .input(LoginSchema)
  .mutation(/* ... */),
```

### Audit Logging

```typescript
// Log security events
logger.info(
  { event: 'auth.login', userId: user.id, email: user.email, ip: ctx.ipAddress },
  'User logged in',
);

logger.warn(
  { event: 'auth.login_failed', email: input.email, ip: ctx.ipAddress },
  'Login failed',
);

logger.info(
  { event: 'auth.logout', userId: ctx.userId },
  'User logged out',
);

logger.warn(
  { event: 'auth.permission_denied', userId: ctx.userId, permission, resource },
  'Permission denied',
);
```
