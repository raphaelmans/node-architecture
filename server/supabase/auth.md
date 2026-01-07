# Supabase Authentication

> Complete authentication implementation using Supabase Auth with tRPC, Next.js middleware, and user roles.

## Overview

This document covers the full authentication flow using Supabase Auth integrated with the layered architecture:

| Component | Location | Responsibility |
|-----------|----------|----------------|
| Supabase Client | `shared/infra/supabase/create-client.ts` | SSR-compatible client creation |
| Auth Repository | `modules/auth/repositories/auth.repository.ts` | Supabase Auth wrapper |
| Auth Service | `modules/auth/services/auth.service.ts` | Business logic, redirect URLs |
| Auth Factory | `modules/auth/factories/auth.factory.ts` | Request-scoped DI |
| User Roles | `modules/user-role/` | Application-level roles in database |
| tRPC Context | `shared/infra/trpc/context.ts` | Session extraction |
| Next.js Proxy | `proxy.ts` | Session refresh, route protection |

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Request Flow                                │
├─────────────────────────────────────────────────────────────────────┤
│  Browser Request                                                      │
│       │                                                               │
│       ▼                                                               │
│  ┌─────────────────┐                                                  │
│  │ Next.js         │ ─── Refresh session cookies                      │
│  │ Proxy           │                                                  │
│  └────────┬────────┘                                                  │
│           │                                                           │
│           ▼                                                           │
│  ┌─────────────────┐     ┌─────────────────┐                          │
│  │ tRPC Context    │ ──► │ Supabase Auth   │ ─── getUser()            │
│  │ createContext() │     └─────────────────┘                          │
│  └────────┬────────┘                                                  │
│           │                                                           │
│           ▼                                                           │
│  ┌─────────────────┐     ┌─────────────────┐                          │
│  │ Session + Role  │ ◄── │ user_roles      │ ─── Drizzle query        │
│  └────────┬────────┘     │ (database)      │                          │
│           │              └─────────────────┘                          │
│           ▼                                                           │
│  ┌─────────────────┐                                                  │
│  │ protectedProc   │ ─── Requires session                             │
│  │ or publicProc   │                                                  │
│  └─────────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Supabase Client Creation

The Supabase client must handle cookies for SSR session management:

```typescript
// shared/infra/supabase/create-client.ts

import { createServerClient, type CookieMethodsServer } from "@supabase/ssr";

/**
 * Creates a Supabase server client with cookie handling for SSR.
 * Used in tRPC context and auth routes.
 */
export function createClient(
  url: string,
  key: string,
  cookies: CookieMethodsServer,
) {
  return createServerClient(url, key, { cookies });
}
```

```typescript
// shared/infra/supabase/types.ts

import type { SupabaseClient as BaseSupabaseClient } from "@supabase/supabase-js";

export type SupabaseClient = BaseSupabaseClient;
```

**Key Points:**
- Uses `@supabase/ssr` for server-side rendering compatibility
- `CookieMethodsServer` enables session persistence across requests
- Client is request-scoped (created per request with cookies)

---

## Auth Repository

The repository wraps Supabase Auth and maps errors to domain errors:

```typescript
// modules/auth/repositories/auth.repository.ts

import type { SupabaseClient } from "@/shared/infra/supabase/types";
import {
  InvalidCredentialsError,
  EmailNotVerifiedError,
  UserAlreadyExistsError,
} from "../errors/auth.errors";

export class AuthRepository {
  constructor(private client: SupabaseClient) {}

  async getCurrentUser() {
    const { data: { user }, error } = await this.client.auth.getUser();
    if (error) throw error;
    return user;
  }

  async signInWithPassword(email: string, password: string) {
    const { data, error } = await this.client.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      if (error.message.includes("Invalid login credentials")) {
        throw new InvalidCredentialsError();
      }
      if (error.message.includes("Email not confirmed")) {
        throw new EmailNotVerifiedError(email);
      }
      throw error;
    }

    return data;
  }

  async signInWithOtp(email: string, redirectTo: string) {
    const { data, error } = await this.client.auth.signInWithOtp({
      email,
      options: { shouldCreateUser: true, emailRedirectTo: redirectTo },
    });

    if (error) throw error;
    return data;
  }

  async signUp(email: string, password: string, redirectTo: string) {
    const { data, error } = await this.client.auth.signUp({
      email,
      password,
      options: { emailRedirectTo: redirectTo },
    });

    if (error) {
      if (error.message.includes("already registered")) {
        throw new UserAlreadyExistsError(email);
      }
      throw error;
    }

    return data;
  }

  async signOut() {
    const { error } = await this.client.auth.signOut();
    if (error) throw error;
  }

  async exchangeCodeForSession(code: string) {
    const { data, error } = await this.client.auth.exchangeCodeForSession(code);
    if (error) throw error;
    return data;
  }
}
```

---

## Auth Errors

Domain-specific errors with unique codes:

```typescript
// modules/auth/errors/auth.errors.ts

import { AuthenticationError, ConflictError } from "@/shared/kernel/errors";

export class InvalidCredentialsError extends AuthenticationError {
  readonly code = "INVALID_CREDENTIALS";

  constructor() {
    super("Invalid email or password");
  }
}

export class EmailNotVerifiedError extends AuthenticationError {
  readonly code = "EMAIL_NOT_VERIFIED";

  constructor(email: string) {
    super("Email not verified", { email });
  }
}

export class UserAlreadyExistsError extends ConflictError {
  readonly code = "USER_ALREADY_EXISTS";

  constructor(email: string) {
    super("User already exists", { email });
  }
}

export class SessionExpiredError extends AuthenticationError {
  readonly code = "SESSION_EXPIRED";

  constructor() {
    super("Session expired, please login again");
  }
}
```

---

## Auth Service

Service layer with redirect URL construction and **business event logging**:

```typescript
// modules/auth/services/auth.service.ts

import type { AuthRepository } from "../repositories/auth.repository";
import { logger } from "@/shared/infra/logger";

export class AuthService {
  constructor(private authRepository: AuthRepository) {}

  async getCurrentUser() {
    return this.authRepository.getCurrentUser();
  }

  async signIn(email: string, password: string) {
    const result = await this.authRepository.signInWithPassword(email, password);

    // Business event: user logged in
    logger.info(
      { event: "user.logged_in", userId: result.user.id, email },
      "User logged in",
    );

    return result;
  }

  async signInWithMagicLink(email: string, baseUrl: string) {
    const redirectTo = `${baseUrl}/auth/callback`;
    const result = await this.authRepository.signInWithOtp(email, redirectTo);

    // Business event: magic link requested
    logger.info(
      { event: "user.magic_link_requested", email },
      "Magic link requested",
    );

    return result;
  }

  async signUp(email: string, password: string, baseUrl: string) {
    const redirectTo = `${baseUrl}/auth/callback`;
    const result = await this.authRepository.signUp(email, password, redirectTo);

    if (result.user) {
      // Business event: user registered
      logger.info(
        { event: "user.registered", userId: result.user.id, email },
        "User registered",
      );
    }

    return result;
  }

  async signOut() {
    await this.authRepository.signOut();

    // Business event: user logged out
    logger.info({ event: "user.logged_out" }, "User logged out");
  }

  async exchangeCodeForSession(code: string) {
    return this.authRepository.exchangeCodeForSession(code);
  }
}
```

---

## User Roles (Application-Level)

Supabase Auth manages authentication. Application-level roles are stored in a separate table linked to `auth.users`:

### Schema

```typescript
// shared/infra/db/schema/user-roles.ts

import { pgTable, uuid, text, timestamp } from "drizzle-orm/pg-core";
import { authUsers } from "drizzle-orm/supabase";
import { createSelectSchema, createInsertSchema } from "drizzle-zod";

export const userRoles = pgTable("user_roles", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: uuid("user_id")
    .notNull()
    .unique()
    .references(() => authUsers.id, { onDelete: "cascade" }),
  role: text("role").notNull().default("member"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

export const UserRoleSchema = createSelectSchema(userRoles);
export const InsertUserRoleSchema = createInsertSchema(userRoles);

export type UserRoleRecord = typeof userRoles.$inferSelect;
export type InsertUserRole = typeof userRoles.$inferInsert;
```

**Key Points:**
- Uses `authUsers` from `drizzle-orm/supabase` to reference Supabase's `auth.users`
- `onDelete: "cascade"` ensures cleanup when Supabase user is deleted
- Role is application-defined (not Supabase's built-in roles)

### Repository

```typescript
// modules/user-role/repositories/user-role.repository.ts

import { eq } from "drizzle-orm";
import { userRoles, type UserRoleRecord, type InsertUserRole } from "@/shared/infra/db/schema";
import type { RequestContext } from "@/shared/kernel/context";
import type { DbClient, DrizzleTransaction } from "@/shared/infra/db/types";

export interface IUserRoleRepository {
  findByUserId(userId: string, ctx?: RequestContext): Promise<UserRoleRecord | null>;
  create(data: InsertUserRole, ctx?: RequestContext): Promise<UserRoleRecord>;
}

export class UserRoleRepository implements IUserRoleRepository {
  constructor(private db: DbClient) {}

  private getClient(ctx?: RequestContext): DbClient | DrizzleTransaction {
    return (ctx?.tx as DrizzleTransaction) ?? this.db;
  }

  async findByUserId(userId: string, ctx?: RequestContext): Promise<UserRoleRecord | null> {
    const client = this.getClient(ctx);
    const result = await client
      .select()
      .from(userRoles)
      .where(eq(userRoles.userId, userId))
      .limit(1);

    return result[0] ?? null;
  }

  async create(data: InsertUserRole, ctx?: RequestContext): Promise<UserRoleRecord> {
    const client = this.getClient(ctx);
    const result = await client.insert(userRoles).values(data).returning();
    return result[0];
  }
}
```

### Service

```typescript
// modules/user-role/services/user-role.service.ts

import type { TransactionManager } from "@/shared/kernel/transaction";
import type { RequestContext } from "@/shared/kernel/context";
import type { IUserRoleRepository } from "../repositories/user-role.repository";
import type { UserRoleRecord, InsertUserRole } from "@/shared/infra/db/schema";
import { UserRoleAlreadyExistsError } from "../errors/user-role.errors";

export interface IUserRoleService {
  findByUserId(userId: string, ctx?: RequestContext): Promise<UserRoleRecord | null>;
  create(data: InsertUserRole, ctx?: RequestContext): Promise<UserRoleRecord>;
}

export class UserRoleService implements IUserRoleService {
  constructor(
    private userRoleRepository: IUserRoleRepository,
    private transactionManager: TransactionManager,
  ) {}

  async findByUserId(userId: string, ctx?: RequestContext): Promise<UserRoleRecord | null> {
    return this.userRoleRepository.findByUserId(userId, ctx);
  }

  async create(data: InsertUserRole, ctx?: RequestContext): Promise<UserRoleRecord> {
    if (ctx?.tx) {
      return this.createInternal(data, ctx);
    }
    return this.transactionManager.run((tx) => this.createInternal(data, { tx }));
  }

  private async createInternal(data: InsertUserRole, ctx: RequestContext): Promise<UserRoleRecord> {
    const existing = await this.userRoleRepository.findByUserId(data.userId, ctx);
    if (existing) {
      throw new UserRoleAlreadyExistsError(data.userId);
    }
    return this.userRoleRepository.create(data, ctx);
  }
}
```

---

## Register User Use Case

Multi-service orchestration for user registration:

```typescript
// modules/auth/use-cases/register-user.use-case.ts

import type { AuthService } from "../services/auth.service";
import type { IUserRoleService } from "@/modules/user-role/services/user-role.service";
import type { TransactionManager } from "@/shared/kernel/transaction";
import type { RegisterDTO } from "../dtos/register.dto";

export class RegisterUserUseCase {
  constructor(
    private authService: AuthService,
    private userRoleService: IUserRoleService,
    private transactionManager: TransactionManager,
  ) {}

  async execute(input: RegisterDTO, baseUrl: string) {
    // 1. Create user in Supabase (outside transaction - external service)
    const result = await this.authService.signUp(
      input.email,
      input.password,
      baseUrl,
    );

    if (!result.user) {
      throw new Error("Failed to create user");
    }

    // 2. Create user role in database (within transaction)
    await this.transactionManager.run(async (tx) => {
      await this.userRoleService.create(
        { userId: result.user!.id, role: "member" },
        { tx },
      );
    });

    return {
      user: { id: result.user.id, email: result.user.email },
      session: result.session,
    };
  }
}
```

**Key Points:**
- Supabase signup is outside transaction (external service)
- Database record creation is within transaction
- If DB insert fails, Supabase user exists but has no role (handle in context creation)

---

## Auth Factories (Request-Scoped)

Auth factories are **request-scoped** because Supabase client needs cookies:

```typescript
// modules/auth/factories/auth.factory.ts

import type { CookieMethodsServer } from "@supabase/ssr";
import { createClient } from "@/shared/infra/supabase/create-client";
import { env } from "@/lib/env";
import { getContainer } from "@/shared/infra/container";
import { AuthRepository } from "../repositories/auth.repository";
import { AuthService } from "../services/auth.service";
import { RegisterUserUseCase } from "../use-cases/register-user.use-case";
import { makeUserRoleService } from "@/modules/user-role/factories/user-role.factory";

/**
 * Auth factories are REQUEST-SCOPED (not lazy singletons)
 * because Supabase client needs request-specific cookies.
 */
export function makeAuthRepository(cookies: CookieMethodsServer) {
  const client = createClient(
    env.SUPABASE_URL,
    env.SUPABASE_SECRET_KEY,
    cookies,
  );
  return new AuthRepository(client);
}

export function makeAuthService(cookies: CookieMethodsServer) {
  return new AuthService(makeAuthRepository(cookies));
}

export function makeRegisterUserUseCase(cookies: CookieMethodsServer) {
  return new RegisterUserUseCase(
    makeAuthService(cookies),
    makeUserRoleService(),
    getContainer().transactionManager,
  );
}
```

---

## tRPC Context

The context extracts session from Supabase and enriches with role from database:

```typescript
// shared/infra/trpc/context.ts

import { randomUUID } from "crypto";
import { cookies, headers } from "next/headers";
import type { FetchCreateContextFnOptions } from "@trpc/server/adapters/fetch";
import type { CookieMethodsServer } from "@supabase/ssr";
import { createClient } from "@/shared/infra/supabase/create-client";
import { createRequestLogger } from "@/shared/infra/logger";
import { env } from "@/lib/env";
import type { Session } from "@/shared/kernel/auth";
import { makeUserRoleRepository } from "@/modules/user-role/factories/user-role.factory";

export interface Context {
  requestId: string;
  session: Session | null;
  userId: string | null;
  cookies: CookieMethodsServer;
  origin: string;
  log: ReturnType<typeof createRequestLogger>;
}

export interface AuthenticatedContext extends Context {
  session: Session;
  userId: string;
}

export async function createContext({ req }: FetchCreateContextFnOptions): Promise<Context> {
  const requestId = req.headers.get("x-request-id") ?? randomUUID();
  const cookieStore = await cookies();
  const headerStore = await headers();

  const cookieMethods: CookieMethodsServer = {
    getAll() {
      return cookieStore.getAll();
    },
    setAll(cookiesToSet) {
      cookiesToSet.forEach(({ name, value, options }) => {
        try {
          cookieStore.set(name, value, options);
        } catch {
          // Server Component - ignore
        }
      });
    },
  };

  // Get current user from Supabase
  const supabase = createClient(
    env.NEXT_PUBLIC_SUPABASE_URL,
    env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
    cookieMethods,
  );
  let session: Session | null = null;

  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      // Fetch role from user_roles table
      const userRole = await makeUserRoleRepository().findByUserId(user.id);
      session = {
        userId: user.id,
        email: user.email!,
        role: (userRole?.role as Session["role"]) ?? "member",
      };
    }
  } catch {
    // No session
  }

  const log = createRequestLogger({
    requestId,
    userId: session?.userId,
    method: req.method,
    path: new URL(req.url).pathname,
  });

  return {
    requestId,
    session,
    userId: session?.userId ?? null,
    cookies: cookieMethods,
    origin: headerStore.get("origin") ?? "http://localhost:3000",
    log,
  };
}
```

---

## tRPC Middleware & Procedures

**Important:** Define all middleware inline in `trpc.ts` to avoid circular dependencies. Do NOT create separate middleware files that import from `trpc.ts`.

```typescript
// shared/infra/trpc/trpc.ts

import { initTRPC, TRPCError } from "@trpc/server";
import { AppError, AuthenticationError } from "@/shared/kernel/errors";
import type { Context, AuthenticatedContext } from "./context";

const t = initTRPC.context<Context>().create({
  errorFormatter({ error, shape, ctx }) {
    const cause = error.cause;
    const requestId = ctx?.requestId ?? "unknown";

    if (cause instanceof AppError) {
      ctx?.log.warn({ err: cause, code: cause.code, details: cause.details, requestId }, cause.message);
      return {
        ...shape,
        data: {
          ...shape.data,
          code: cause.code,
          httpStatus: cause.httpStatus,
          requestId,
          details: cause.details,
        },
      };
    }

    ctx?.log.error({ err: error, requestId }, "Unexpected error");
    return {
      ...shape,
      data: { ...shape.data, code: "INTERNAL_ERROR", requestId },
    };
  },
});

export const router = t.router;
export const middleware = t.middleware;

/**
 * Logger middleware - request lifecycle tracing.
 * Defined inline to avoid circular dependency with middleware exports.
 */
const loggerMiddleware = t.middleware(async ({ ctx, next, type }) => {
  const start = Date.now();

  ctx.log.info({ type }, "Request started");

  // Log input at debug level only in development
  if (process.env.NODE_ENV !== "production") {
    ctx.log.debug("Request processing");
  }

  try {
    const result = await next({ ctx });
    const duration = Date.now() - start;

    ctx.log.info({ duration, status: "success", type }, "Request completed");

    return result;
  } catch (error) {
    const duration = Date.now() - start;

    ctx.log.info({ duration, status: "error", type }, "Request failed");

    throw error;
  }
});

/**
 * Auth middleware - requires valid session.
 * Defined inline to avoid circular dependency.
 */
const authMiddleware = t.middleware(async ({ ctx, next }) => {
  if (!ctx.session || !ctx.userId) {
    throw new TRPCError({
      code: "UNAUTHORIZED",
      message: "Authentication required",
      cause: new AuthenticationError("Authentication required"),
    });
  }

  return next({ ctx: ctx as AuthenticatedContext });
});

/**
 * Base procedure with logging - all procedures use this
 */
const loggedProcedure = t.procedure.use(loggerMiddleware);

export const publicProcedure = loggedProcedure;
export const protectedProcedure = loggedProcedure.use(authMiddleware);
```

---

## Auth Router

```typescript
// modules/auth/auth.router.ts

import { router, publicProcedure, protectedProcedure } from "@/shared/infra/trpc/trpc";
import { makeAuthService, makeRegisterUserUseCase } from "./factories/auth.factory";
import { LoginSchema, RegisterSchema, MagicLinkSchema } from "./dtos";

export const authRouter = router({
  login: publicProcedure
    .input(LoginSchema)
    .mutation(async ({ input, ctx }) => {
      const authService = makeAuthService(ctx.cookies);
      const result = await authService.signIn(input.email, input.password);
      return { user: { id: result.user.id, email: result.user.email } };
    }),

  loginWithMagicLink: publicProcedure
    .input(MagicLinkSchema)
    .mutation(async ({ input, ctx }) => {
      const authService = makeAuthService(ctx.cookies);
      await authService.signInWithMagicLink(input.email, ctx.origin);
      return { success: true, message: "Magic link sent to email" };
    }),

  register: publicProcedure
    .input(RegisterSchema)
    .mutation(async ({ input, ctx }) => {
      const useCase = makeRegisterUserUseCase(ctx.cookies);
      const result = await useCase.execute(input, ctx.origin);
      return result;
    }),

  logout: protectedProcedure
    .mutation(async ({ ctx }) => {
      const authService = makeAuthService(ctx.cookies);
      await authService.signOut();
      return { success: true };
    }),

  me: protectedProcedure
    .query(async ({ ctx }) => {
      return {
        id: ctx.session.userId,
        email: ctx.session.email,
        role: ctx.session.role,
      };
    }),
});
```

---

## Next.js Middleware

Session refresh and route protection:

> **Note:** In Next.js 16+, `middleware.ts` is renamed to `proxy.ts` and the export is renamed from `middleware` to `proxy`. The proxy runtime is nodejs-only (edge runtime not supported).

```typescript
// proxy.ts

import { type NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

const PROTECTED_ROUTES = ["/dashboard", "/settings", "/profile"];
const AUTH_ROUTES = ["/login", "/register", "/magic-link"];

function matchesRoute(path: string, routes: string[]): boolean {
  return routes.some((route) => path === route || path.startsWith(`${route}/`));
}

/**
 * Next.js proxy for session refresh and route protection.
 * - Refreshes Supabase session on every request
 * - Redirects unauthenticated users from protected routes to /login
 * - Redirects authenticated users from auth routes to /
 */
export async function proxy(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => {
            request.cookies.set(name, value);
          });
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) => {
            supabaseResponse.cookies.set(name, value, options);
          });
        },
      },
    },
  );

  // Refresh session
  const { data: { user } } = await supabase.auth.getUser();
  const path = request.nextUrl.pathname;

  // Redirect unauthenticated users from protected routes
  if (!user && matchesRoute(path, PROTECTED_ROUTES)) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", path);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect authenticated users from auth routes
  if (user && matchesRoute(path, AUTH_ROUTES)) {
    const redirectTo = request.nextUrl.searchParams.get("redirect") || "/";
    return NextResponse.redirect(new URL(redirectTo, request.url));
  }

  return supabaseResponse;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
```

---

## Auth Callback Route

Handles OAuth and magic link redirects:

```typescript
// app/auth/callback/route.ts

import { NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/";

  if (code) {
    const cookieStore = await cookies();
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
      {
        cookies: {
          getAll() {
            return cookieStore.getAll();
          },
          setAll(cookiesToSet) {
            cookiesToSet.forEach(({ name, value, options }) => {
              cookieStore.set(name, value, options);
            });
          },
        },
      },
    );

    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  return NextResponse.redirect(`${origin}/auth/auth-code-error`);
}
```

---

## Kernel Types

```typescript
// shared/kernel/auth.ts

export interface Session {
  userId: string;
  email: string;
  role: UserRole;
}

export type UserRole = "admin" | "member" | "viewer";

export const ROLE_PERMISSIONS = {
  admin: ["read", "write", "delete", "manage_users"] as const,
  member: ["read", "write"] as const,
  viewer: ["read"] as const,
};

export type Permission = (typeof ROLE_PERMISSIONS)[keyof typeof ROLE_PERMISSIONS][number];

export function hasPermission(role: UserRole, permission: Permission): boolean {
  return (ROLE_PERMISSIONS[role] as readonly string[]).includes(permission);
}
```

---

## Environment Variables

```bash
# .env.local

# Supabase (public - safe to expose)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx

# Supabase (server-only - NEVER expose)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=sb_secret_xxx

# Database
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

---

## File Structure

```
src/
├── app/
│   ├── auth/
│   │   └── callback/
│   │       └── route.ts          # OAuth/magic link callback
│   └── api/
│       └── trpc/
│           └── [trpc]/
│               └── route.ts
├── proxy.ts                       # Session refresh + route protection (Next.js 16+)
├── shared/
│   ├── kernel/
│   │   ├── auth.ts               # Session, UserRole, Permission
│   │   ├── context.ts            # RequestContext
│   │   ├── transaction.ts        # TransactionManager
│   │   └── errors.ts             # Base error classes
│   └── infra/
│       ├── supabase/
│       │   ├── create-client.ts  # SSR client factory
│       │   └── types.ts          # SupabaseClient type
│       ├── db/
│       │   ├── drizzle.ts        # Database client
│       │   ├── transaction.ts    # DrizzleTransactionManager
│       │   ├── types.ts          # DbClient, DrizzleTransaction
│       │   └── schema/
│       │       ├── user-roles.ts # user_roles table
│       │       └── index.ts
│       ├── trpc/
│       │   ├── trpc.ts           # tRPC init + procedures
│       │   ├── context.ts        # Session extraction
│       │   └── root.ts           # Root router
│       └── container.ts          # Composition root
└── modules/
    ├── auth/
    │   ├── dtos/
    │   │   ├── login.dto.ts
    │   │   ├── register.dto.ts
    │   │   └── index.ts
    │   ├── errors/
    │   │   └── auth.errors.ts
    │   ├── repositories/
    │   │   └── auth.repository.ts
    │   ├── services/
    │   │   └── auth.service.ts
    │   ├── use-cases/
    │   │   └── register-user.use-case.ts
    │   ├── factories/
    │   │   └── auth.factory.ts
    │   └── auth.router.ts
    └── user-role/
        ├── errors/
        │   └── user-role.errors.ts
        ├── repositories/
        │   └── user-role.repository.ts
        ├── services/
        │   └── user-role.service.ts
        └── factories/
            └── user-role.factory.ts
```

---

## Checklist

### Supabase Setup
- [ ] Create Supabase project
- [ ] Get publishable and secret keys
- [ ] Configure email templates for magic link/confirmation
- [ ] Set redirect URLs in Supabase dashboard

### Infrastructure
- [ ] `create-client.ts` with SSR cookie handling
- [ ] Environment variables configured
- [ ] Database migrations for `user_roles` table

### Auth Module
- [ ] `AuthRepository` wrapping Supabase Auth
- [ ] `AuthService` with redirect URL construction
- [ ] Domain errors (`InvalidCredentialsError`, etc.)
- [ ] DTOs with Zod schemas
- [ ] Request-scoped factories

### User Role Module
- [ ] `user_roles` schema with FK to `auth.users`
- [ ] `UserRoleRepository` with transaction support
- [ ] `UserRoleService` with tx ownership pattern
- [ ] Lazy singleton factories

### tRPC Integration
- [ ] Context extracts session + role
- [ ] `publicProcedure` and `protectedProcedure`
- [ ] Error formatter maps `AppError`
- [ ] Auth router with login/register/logout/me

### Next.js
- [ ] Middleware for session refresh
- [ ] Route protection (redirect unauthenticated)
- [ ] Auth callback route handler

### Registration Flow
- [ ] `RegisterUserUseCase` orchestrates Supabase + DB
- [ ] User role created on registration
- [ ] Email confirmation flow works

---

## Architecture Alignment

| Core Principle | Supabase Auth Implementation |
|----------------|------------------------------|
| **Repository pattern** | `AuthRepository` wraps Supabase Auth client |
| **Service layer** | `AuthService` adds business logic (redirect URLs) |
| **Domain errors** | Supabase errors mapped to `AppError` subclasses |
| **Request-scoped DI** | Factories accept `cookies` parameter |
| **Transaction ownership** | `UserRoleService` owns DB transaction |
| **Use case orchestration** | `RegisterUserUseCase` coordinates auth + DB |
| **Kernel types** | `Session`, `UserRole`, `Permission` in kernel |
