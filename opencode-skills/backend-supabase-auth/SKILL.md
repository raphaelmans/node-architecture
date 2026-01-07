---
name: backend-supabase-auth
description: Implement Supabase authentication with tRPC, user roles, Next.js proxy, magic links, and request-scoped factories
---

# Supabase Authentication

Use this skill when implementing authentication with Supabase Auth in a Next.js + tRPC project.

## Architecture

```
Request → Proxy (refresh) → tRPC Context (session) → Router → Service → Repository
```

| Component | Location | Responsibility |
|-----------|----------|----------------|
| Supabase Client | `shared/infra/supabase/create-client.ts` | SSR client creation |
| Auth Repository | `modules/auth/repositories/auth.repository.ts` | Supabase Auth wrapper |
| Auth Service | `modules/auth/services/auth.service.ts` | Business logic, logging |
| Auth Factory | `modules/auth/factories/auth.factory.ts` | Request-scoped DI |
| User Roles | `modules/user-role/` | Application roles in DB |
| tRPC Context | `shared/infra/trpc/context.ts` | Session extraction |
| Next.js Proxy | `proxy.ts` | Session refresh, route protection |

> **Note:** In Next.js 16+, `middleware.ts` is renamed to `proxy.ts` and the export is `proxy` instead of `middleware`. The proxy runtime is nodejs-only (edge runtime not supported).

## Step-by-Step

### 1. Supabase Client

```typescript
// shared/infra/supabase/create-client.ts
import { createServerClient, type CookieMethodsServer } from "@supabase/ssr";

export function createClient(
  url: string,
  key: string,
  cookies: CookieMethodsServer
) {
  return createServerClient(url, key, { cookies });
}
```

### 2. Auth Repository

```typescript
// modules/auth/repositories/auth.repository.ts
import type { SupabaseClient } from "@supabase/supabase-js";
import { InvalidCredentialsError, EmailNotVerifiedError } from "../errors/auth.errors";

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
    if (error) throw error;
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

### 3. Auth Service (with logging)

```typescript
// modules/auth/services/auth.service.ts
import { logger } from "@/shared/infra/logger";
import type { AuthRepository } from "../repositories/auth.repository";

export class AuthService {
  constructor(private authRepository: AuthRepository) {}

  async signIn(email: string, password: string) {
    const result = await this.authRepository.signInWithPassword(email, password);

    logger.info(
      { event: "user.logged_in", userId: result.user.id, email },
      "User logged in"
    );

    return result;
  }

  async signInWithMagicLink(email: string, baseUrl: string) {
    const redirectTo = `${baseUrl}/auth/callback`;
    const result = await this.authRepository.signInWithOtp(email, redirectTo);

    logger.info(
      { event: "user.magic_link_requested", email },
      "Magic link requested"
    );

    return result;
  }

  async signUp(email: string, password: string, baseUrl: string) {
    const redirectTo = `${baseUrl}/auth/callback`;
    const result = await this.authRepository.signUp(email, password, redirectTo);

    if (result.user) {
      logger.info(
        { event: "user.registered", userId: result.user.id, email },
        "User registered"
      );
    }

    return result;
  }

  async signOut() {
    await this.authRepository.signOut();
    logger.info({ event: "user.logged_out" }, "User logged out");
  }
}
```

### 4. Auth Errors

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
```

### 5. User Roles Schema

```typescript
// shared/infra/db/schema/user-roles.ts
import { pgTable, uuid, text, timestamp } from "drizzle-orm/pg-core";
import { authUsers } from "drizzle-orm/supabase";

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
```

### 6. Request-Scoped Factories

```typescript
// modules/auth/factories/auth.factory.ts
import type { CookieMethodsServer } from "@supabase/ssr";
import { createClient } from "@/shared/infra/supabase/create-client";
import { env } from "@/lib/env";
import { AuthRepository } from "../repositories/auth.repository";
import { AuthService } from "../services/auth.service";

// REQUEST-SCOPED (not singletons)
export function makeAuthRepository(cookies: CookieMethodsServer) {
  const client = createClient(env.SUPABASE_URL, env.SUPABASE_SECRET_KEY, cookies);
  return new AuthRepository(client);
}

export function makeAuthService(cookies: CookieMethodsServer) {
  return new AuthService(makeAuthRepository(cookies));
}
```

### 7. tRPC Context

```typescript
// shared/infra/trpc/context.ts
import { cookies, headers } from "next/headers";
import { createClient } from "@/shared/infra/supabase/create-client";
import { env } from "@/lib/env";
import { makeUserRoleRepository } from "@/modules/user-role/factories";

export async function createContext({ req }) {
  const requestId = req.headers.get("x-request-id") ?? crypto.randomUUID();
  const cookieStore = await cookies();

  const cookieMethods = {
    getAll: () => cookieStore.getAll(),
    setAll: (toSet) => toSet.forEach(({ name, value, options }) => {
      try { cookieStore.set(name, value, options); } catch {}
    }),
  };

  // Get user from Supabase
  const supabase = createClient(
    env.NEXT_PUBLIC_SUPABASE_URL,
    env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
    cookieMethods
  );

  let session = null;
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      const userRole = await makeUserRoleRepository().findByUserId(user.id);
      session = {
        userId: user.id,
        email: user.email,
        role: userRole?.role ?? "member",
      };
    }
  } catch {}

  return {
    requestId,
    session,
    userId: session?.userId ?? null,
    cookies: cookieMethods,
    origin: (await headers()).get("origin") ?? "http://localhost:3000",
  };
}
```

### 8. tRPC Setup (Inline Middleware)

**Important:** Define all middleware inline in `trpc.ts` to avoid circular dependencies. Do NOT create separate middleware files.

```typescript
// shared/infra/trpc/trpc.ts
import { initTRPC, TRPCError } from "@trpc/server";
import { AppError, AuthenticationError } from "@/shared/kernel/errors";
import type { Context, AuthenticatedContext } from "./context";

const t = initTRPC.context<Context>().create({
  errorFormatter({ error, shape, ctx }) {
    const cause = error.cause;
    const requestId = ctx?.requestId;

    if (cause instanceof AppError) {
      ctx?.log.warn(
        { err: cause, code: cause.code, details: cause.details, requestId },
        cause.message,
      );
      return { ...shape, data: { ...shape.data, code: cause.code, requestId } };
    }

    ctx?.log.error({ err: error, requestId }, "Unexpected error");
    return { ...shape, data: { ...shape.data, requestId } };
  },
});

export const router = t.router;
export const middleware = t.middleware;

/**
 * Logger middleware - defined inline to avoid circular deps
 */
const loggerMiddleware = t.middleware(async ({ ctx, next, type }) => {
  const start = Date.now();
  ctx.log.info({ type }, "Request started");

  try {
    const result = await next({ ctx });
    ctx.log.info({ duration: Date.now() - start, status: "success", type }, "Request completed");
    return result;
  } catch (error) {
    ctx.log.info({ duration: Date.now() - start, status: "error", type }, "Request failed");
    throw error;
  }
});

/**
 * Auth middleware - defined inline to avoid circular deps
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

const loggedProcedure = t.procedure.use(loggerMiddleware);
export const publicProcedure = loggedProcedure;
export const protectedProcedure = loggedProcedure.use(authMiddleware);
```

### 9. Auth Router

```typescript
// modules/auth/auth.router.ts
import { router, publicProcedure, protectedProcedure } from "@/shared/infra/trpc";
import { makeAuthService } from "./factories/auth.factory";
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
      return { success: true };
    }),

  logout: protectedProcedure.mutation(async ({ ctx }) => {
    const authService = makeAuthService(ctx.cookies);
    await authService.signOut();
    return { success: true };
  }),

  me: protectedProcedure.query(async ({ ctx }) => ({
    id: ctx.session.userId,
    email: ctx.session.email,
    role: ctx.session.role,
  })),
});
```

### 10. Next.js Proxy (Next.js 16+)

> **Note:** In Next.js 16+, `middleware.ts` is renamed to `proxy.ts` and the export is `proxy` instead of `middleware`.

```typescript
// proxy.ts
import { type NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

const PROTECTED = ["/dashboard", "/settings"];
const AUTH = ["/login", "/register"];

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
        getAll: () => request.cookies.getAll(),
        setAll: (toSet) => {
          toSet.forEach(({ name, value }) => request.cookies.set(name, value));
          supabaseResponse = NextResponse.next({ request });
          toSet.forEach(({ name, value, options }) => 
            supabaseResponse.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  const { data: { user } } = await supabase.auth.getUser();
  const path = request.nextUrl.pathname;

  // Redirect unauthenticated from protected
  if (!user && matchesRoute(path, PROTECTED)) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("redirect", path);
    return NextResponse.redirect(url);
  }

  // Redirect authenticated from auth pages
  if (user && matchesRoute(path, AUTH)) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return supabaseResponse;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
```

### 11. Auth Callback Route

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
          getAll: () => cookieStore.getAll(),
          setAll: (toSet) => toSet.forEach(({ name, value, options }) => 
            cookieStore.set(name, value, options)
          ),
        },
      }
    );

    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  return NextResponse.redirect(`${origin}/auth/error`);
}
```

## Environment Variables

```bash
# Public
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx

# Server only
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SECRET_KEY=sb_secret_xxx
DATABASE_URL=postgresql://...
```

## Checklist

### Supabase Setup
- [ ] Project created with email auth enabled
- [ ] Redirect URLs configured
- [ ] Email templates customized

### Infrastructure
- [ ] `create-client.ts` with SSR cookies
- [ ] Environment variables set
- [ ] `user_roles` migration run

### Auth Module
- [ ] Repository wraps Supabase Auth
- [ ] Service logs business events
- [ ] Domain errors defined
- [ ] Request-scoped factories

### tRPC Integration
- [ ] Context extracts session + role
- [ ] `protectedProcedure` requires session
- [ ] Auth router endpoints

### Next.js
- [ ] Proxy refreshes session (`proxy.ts` with `export async function proxy`)
- [ ] Route protection works
- [ ] Callback route handles OAuth/magic link

---

## Auth Module Implementation Checklist

Use this checklist when implementing authentication to ensure nothing is missed.

### Auth Errors (`errors/auth.errors.ts`)
- [ ] `InvalidCredentialsError` with `readonly code = 'AUTH_INVALID_CREDENTIALS'`
- [ ] `EmailNotVerifiedError` with `readonly code = 'AUTH_EMAIL_NOT_VERIFIED'`
- [ ] `UserAlreadyExistsError` with `readonly code = 'AUTH_USER_ALREADY_EXISTS'`
- [ ] `SessionExpiredError` with `readonly code = 'AUTH_SESSION_EXPIRED'`
- [ ] All errors extend appropriate base class (`AuthenticationError`, `ConflictError`)
- [ ] Error messages are user-safe (no stack traces, internal details)

```typescript
// CORRECT - has unique code
export class InvalidCredentialsError extends AuthenticationError {
  readonly code = 'AUTH_INVALID_CREDENTIALS';
  constructor() {
    super('Invalid email or password');
  }
}

// WRONG - missing code (will use parent's generic code)
export class InvalidCredentialsError extends AuthenticationError {
  constructor() {
    super('Invalid email or password');
  }
}
```

### Auth Repository (`repositories/auth.repository.ts`)
- [ ] Interface `IAuthRepository` defined
- [ ] Class implements interface: `class AuthRepository implements IAuthRepository`
- [ ] Maps external errors (Supabase, etc.) to domain errors
- [ ] No business logic
- [ ] No logging

### Auth Service (`services/auth.service.ts`)
- [ ] Interface `IAuthService` defined
- [ ] Class implements interface: `class AuthService implements IAuthService`
- [ ] Constructor accepts `IAuthRepository` (interface, not concrete)
- [ ] Business event logging for all auth actions:
  - [ ] `user.logged_in` on successful login
  - [ ] `user.registered` on successful signup
  - [ ] `user.logged_out` on logout
  - [ ] `user.magic_link_requested` on magic link request
  - [ ] `user.session_exchanged` on OAuth/callback
- [ ] Redirect URLs constructed in service layer

### Auth Factory (`factories/auth.factory.ts`)
- [ ] Request-scoped pattern (NOT lazy singleton) - auth needs cookies
- [ ] Accepts `CookieMethodsServer` parameter
- [ ] Creates fresh instances per request

### Auth Use Cases (if applicable)
- [ ] `RegisterUserUseCase` for multi-service registration
- [ ] Throws domain errors (NOT generic `Error`)
- [ ] Depends on service interfaces (NOT concrete classes)
- [ ] Transaction manager for DB operations
- [ ] External service calls (Supabase) OUTSIDE transaction
- [ ] DB operations INSIDE transaction

```typescript
// CORRECT - domain error
if (!result.user) {
  throw new AuthRegistrationFailedError(input.email);
}

// WRONG - generic error
if (!result.user) {
  throw new Error('Failed to create user');
}
```

### tRPC Context (`shared/infra/trpc/context.ts`)
- [ ] Extracts session from auth provider (Supabase)
- [ ] Enriches with application role from database
- [ ] Creates child logger with `requestId`, `userId`
- [ ] Exposes `cookies` for request-scoped factories

### tRPC Procedures (`shared/infra/trpc/trpc.ts`)
- [ ] Logger middleware applied to all procedures
- [ ] `publicProcedure` uses logger middleware
- [ ] `protectedProcedure` uses logger + auth middleware
- [ ] Error formatter includes `requestId` in all error logs
- [ ] Known errors logged at `warn` level
- [ ] Unknown errors logged at `error` level

```typescript
// CORRECT - includes requestId
ctx?.log.warn(
  { err: cause, code: cause.code, details: cause.details, requestId },
  cause.message,
);

// WRONG - missing requestId
ctx?.log.warn(
  { err: cause, code: cause.code, details: cause.details },
  cause.message,
);
```

### Auth Router (`auth.router.ts`)
- [ ] `login` - public, calls service
- [ ] `register` - public, calls use case (if multi-service)
- [ ] `logout` - protected, calls service
- [ ] `me` - protected, returns session from context
- [ ] Magic link endpoint if needed
- [ ] No direct logging (handled by middleware)

### tRPC Middleware (Inline in `trpc.ts`)
- [ ] All middleware defined inline in `trpc.ts` (avoid circular deps)
- [ ] NO separate middleware files that import from `trpc.ts`
- [ ] Logger middleware defined with `t.middleware()`
- [ ] Auth middleware defined with `t.middleware()`

### Proxy (`proxy.ts`) - Next.js 16+
- [ ] File named `proxy.ts` (not `middleware.ts`)
- [ ] Export named `proxy` (not `middleware`)
- [ ] Session refresh on every request
- [ ] Protected routes redirect to login
- [ ] Auth routes redirect authenticated users away
- [ ] Preserves `?redirect=` for post-login navigation

### User Roles (if applicable)
- [ ] `user_roles` table schema with FK to auth users
- [ ] `IUserRoleRepository` interface
- [ ] `IUserRoleService` interface
- [ ] Business event: `user_role.created`
- [ ] Lazy singleton factory (DB-backed, not request-scoped)
