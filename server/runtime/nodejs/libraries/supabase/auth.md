# Supabase Authentication

> Complete authentication implementation using Supabase Auth with tRPC, Next.js Proxy, and user roles. Uses **PKCE flow** for magic links and email verification.

## Overview

This concrete example combines Supabase Auth with Drizzle-backed global application roles. It does not require an ORM for Supabase-only repositories and does not model organization/branch roles; use [data access](./data-access.md), [tenancy](../../../../core/tenancy.md), and [RBAC](../../../../core/rbac.md) for those conventions. Resolve vendor APIs and migration details from the installed version's official documentation rather than copying this example unchanged.

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

## PKCE Flow vs Implicit Flow

This implementation uses **PKCE (Proof Key for Code Exchange)** flow, which is the recommended approach for SSR applications.

| Aspect | Implicit Flow | PKCE Flow (Recommended) |
|--------|---------------|-------------------------|
| **URL Parameter** | `code` | `token_hash` |
| **Verification Method** | `exchangeCodeForSession(code)` | `verifyOtp({ token_hash, type })` |
| **Route Handler** | `/auth/callback` | `/auth/confirm` |
| **Security** | Less secure | More secure for SSR |

### PKCE Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Magic Link PKCE Flow                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  1. User requests magic link                                           │
│     └─► POST /api/trpc/auth.loginWithMagicLink                        │
│                                                                        │
│  2. Service calls Supabase signInWithOtp                               │
│     └─► emailRedirectTo: https://app.com/auth/confirm?redirect=%2F...  │
│                                                                        │
│  3. Supabase sends email with link:                                    │
│     └─► {{ .RedirectTo }}&token_hash=xxx&type=magiclink                │
│                                                                        │
│  4. User clicks link → Route handler verifies                          │
│     └─► supabase.auth.verifyOtp({ token_hash, type: 'magiclink' })    │
│                                                                        │
│  5. Session cookies set → Redirect to `redirect` param                 │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Supabase Dashboard Configuration

**IMPORTANT:** The `{{ .SiteURL }}` variable in email templates is controlled by Supabase Dashboard, not your environment variables.

### URL Configuration

Navigate to **Supabase Dashboard → Authentication → URL Configuration**:

| Setting | Value | Notes |
|---------|-------|-------|
| **Site URL** | `https://yourdomain.com` | Default allow-listed base URL |
| **Redirect URLs** | `https://yourdomain.com` | Allow root redirects |
| | `http://localhost:3000` | Allow local root redirects |
| | `https://yourdomain.com/auth/confirm**` | PKCE email links (`/auth/confirm?...`) |
| | `https://yourdomain.com/auth/callback**` | OAuth callback (`/auth/callback?...`) |
| | `http://localhost:3000/auth/confirm**` | Local development |
| | `http://localhost:3000/auth/callback**` | Local development |

### Email Templates

Templates are version-controlled under `supabase/templates/*` and pushed to Supabase via CLI.

**How it works:** your backend passes `emailRedirectTo` as a fully-qualified `/auth/confirm?redirect=...` URL. In the template, use `{{ .RedirectTo }}` as the base and append `token_hash` + `type`.

**Push templates + auth config:**
```bash
supabase link --project-ref <project-ref>
supabase config push --project-ref <project-ref>
```

If you prefer manual changes, you can still paste the HTML into **Supabase Dashboard → Authentication → Email Templates**.

**Magic Link Template:**
```html
<h2>Magic Link</h2>
<p>Follow this link to login:</p>
<p><a href="{{ .RedirectTo }}&token_hash={{ .TokenHash }}&type=magiclink">Log In</a></p>
```

**Signup Confirmation Template:**
```html
<h2>Confirm your signup</h2>
<p><a href="{{ .RedirectTo }}&token_hash={{ .TokenHash }}&type=signup">Confirm your email</a></p>
```

**Password Recovery Template:**
```html
<h2>Reset your password</h2>
<p><a href="{{ .RedirectTo }}&token_hash={{ .TokenHash }}&type=recovery">Reset Password</a></p>
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

The repository is an anti-corruption adapter: it wraps Supabase Auth, maps provider errors to domain errors, and maps provider `User`/`Session` objects to provider-neutral module models before returning them.

Branch on Supabase Auth `error.code`, never localized/message text. See the official [Supabase Auth error codes](https://supabase.com/docs/guides/auth/debugging/error-codes).

```typescript
// modules/auth/models/auth.models.ts

export interface AuthUser {
  id: string;
  email: string | null;
}

export interface AuthSessionState {
  userId: string;
  expiresAt: number | null;
}

export interface AuthResult {
  user: AuthUser | null;
  session: AuthSessionState | null;
}

export interface AuthenticatedAuthResult {
  user: AuthUser;
  session: AuthSessionState;
}
```

```typescript
// modules/auth/repositories/auth.repository.ts

import type { SupabaseClient } from "@/shared/infra/supabase/types";
import type { User, Session } from "@supabase/supabase-js";
import type { AppError } from "@/shared/kernel/errors";
import type {
  AuthUser,
  AuthResult,
  AuthenticatedAuthResult,
} from "../models/auth.models";
import {
  InvalidCredentialsError,
  EmailNotVerifiedError,
  SessionExpiredError,
  AuthProviderUnavailableError,
} from "../errors/auth.errors";

function translateSupabaseAuthError(error: { code?: string }): AppError {
  if (error.code === "invalid_credentials") return new InvalidCredentialsError();
  if (error.code === "email_not_confirmed") return new EmailNotVerifiedError();
  if (
    error.code === "session_not_found" ||
    error.code === "refresh_token_not_found" ||
    error.code === "refresh_token_already_used"
  ) {
    return new SessionExpiredError();
  }

  // Keep the provider code as internal diagnostics only. The public formatter
  // returns the generic 5xx message for this bad-gateway domain error.
  return new AuthProviderUnavailableError(error.code);
}

export interface IAuthRepository {
  getCurrentUser(): Promise<AuthUser | null>;
  signInWithPassword(email: string, password: string): Promise<AuthenticatedAuthResult>;
  signInWithOtp(email: string, redirectTo: string): Promise<AuthResult>;
  signUp(email: string, password: string, redirectTo: string): Promise<AuthResult>;
  signOut(): Promise<void>;
  exchangeCodeForSession(code: string): Promise<AuthenticatedAuthResult>;
  // PKCE flow methods
  verifyMagicLink(tokenHash: string): Promise<AuthResult>;
  verifySignUp(tokenHash: string): Promise<AuthResult>;
  verifyRecovery(tokenHash: string): Promise<void>;
}

// These helpers are private to the Supabase adapter. They select only the
// provider-neutral fields the application needs.
function toAuthUser(user: User | null): AuthUser | null { /* ... */ }
function toAuthResult(data: { user: User | null; session: Session | null }): AuthResult { /* ... */ }
function toAuthenticatedAuthResult(data: { user: User; session: Session }): AuthenticatedAuthResult { /* ... */ }

export class AuthRepository implements IAuthRepository {
  constructor(private client: SupabaseClient) {}

  async getCurrentUser(): Promise<AuthUser | null> {
    const { data: { user }, error } = await this.client.auth.getUser();
    if (error) throw translateSupabaseAuthError(error);
    return toAuthUser(user);
  }

  async signInWithPassword(email: string, password: string): Promise<AuthenticatedAuthResult> {
    const { data, error } = await this.client.auth.signInWithPassword({
      email,
      password,
    });

    if (error) throw translateSupabaseAuthError(error);

    return toAuthenticatedAuthResult(data);
  }

  async signInWithOtp(email: string, redirectTo: string): Promise<AuthResult> {
    const { data, error } = await this.client.auth.signInWithOtp({
      email,
      options: { shouldCreateUser: true, emailRedirectTo: redirectTo },
    });

    if (error) throw translateSupabaseAuthError(error);
    return toAuthResult(data);
  }

  async signUp(email: string, password: string, redirectTo: string): Promise<AuthResult> {
    const { data, error } = await this.client.auth.signUp({
      email,
      password,
      options: { emailRedirectTo: redirectTo },
    });

    if (error) throw translateSupabaseAuthError(error);

    return toAuthResult(data);
  }

  async signOut(): Promise<void> {
    const { error } = await this.client.auth.signOut();
    if (error) throw translateSupabaseAuthError(error);
  }

  // OAuth flow (kept for OAuth providers)
  async exchangeCodeForSession(code: string): Promise<AuthenticatedAuthResult> {
    const { data, error } = await this.client.auth.exchangeCodeForSession(code);
    if (error) throw translateSupabaseAuthError(error);
    return toAuthenticatedAuthResult(data);
  }

  // PKCE flow methods
  async verifyMagicLink(tokenHash: string): Promise<AuthResult> {
    const { data, error } = await this.client.auth.verifyOtp({
      token_hash: tokenHash,
      type: "magiclink",
    });
    if (error) throw translateSupabaseAuthError(error);
    return toAuthResult(data);
  }

  async verifySignUp(tokenHash: string): Promise<AuthResult> {
    const { data, error } = await this.client.auth.verifyOtp({
      token_hash: tokenHash,
      type: "signup",
    });
    if (error) throw translateSupabaseAuthError(error);
    return toAuthResult(data);
  }

  async verifyRecovery(tokenHash: string): Promise<void> {
    const { error } = await this.client.auth.verifyOtp({
      token_hash: tokenHash,
      type: "recovery",
    });
    if (error) throw translateSupabaseAuthError(error);
  }
}
```

---

## Auth Errors

Domain-specific errors with unique codes:

```typescript
// modules/auth/errors/auth.errors.ts

import {
  AuthenticationError,
  BadGatewayError,
  InternalError,
} from "@/shared/kernel/errors";

export class InvalidCredentialsError extends AuthenticationError {
  readonly code = "INVALID_CREDENTIALS";

  constructor() {
    super("Invalid email or password");
  }
}

export class EmailNotVerifiedError extends AuthenticationError {
  readonly code = "EMAIL_NOT_VERIFIED";

  constructor() {
    super("Email not verified");
  }
}

export class SessionExpiredError extends AuthenticationError {
  readonly code = "SESSION_EXPIRED";

  constructor() {
    super("Session expired, please login again");
  }
}

export class AuthRegistrationFailedError extends BadGatewayError {
  readonly code = "AUTH_REGISTRATION_FAILED";

  constructor() {
    super("Authentication provider did not create a user");
  }
}

export class AuthProviderUnavailableError extends BadGatewayError {
  readonly code = "AUTH_PROVIDER_UNAVAILABLE";

  constructor(providerCode?: string) {
    super("Authentication provider request failed", { providerCode });
  }
}

export class UserProvisioningFailedError extends InternalError {
  readonly code = "USER_PROVISIONING_FAILED";

  constructor(userId: string) {
    super("User provisioning failed", { userId });
  }
}
```

---

## Shared Auth Contracts

```typescript
// modules/auth/shared/contracts/auth.contract.ts

import { z } from "zod";
import { S } from "@/shared/kernel/schemas";

export const LoginInputSchema = z.object({
  email: S.auth.email,
  password: S.auth.loginPassword,
});

export type LoginInput = z.infer<typeof LoginInputSchema>;

export const MagicLinkInputSchema = z.object({
  email: S.auth.email,
  redirect: S.common.optionalText,
});

export type MagicLinkInput = z.infer<typeof MagicLinkInputSchema>;

const AuthUserResponseSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email().nullable(),
});

export const LoginResponseSchema = z.object({ user: AuthUserResponseSchema });
export const MagicLinkResponseSchema = z.object({ success: z.literal(true) });
export const RegisterUserResponseSchema = z.object({ accepted: z.literal(true) });
export const LogoutResponseSchema = z.object({ success: z.literal(true) });
export const CurrentSessionResponseSchema = AuthUserResponseSchema.extend({
  role: z.enum(["admin", "member", "viewer"]),
});
export const VerifyAuthResponseSchema = z.object({
  user: AuthUserResponseSchema.nullable(),
});
export const RecoveryResponseSchema = z.object({ success: z.literal(true) });

export type LoginResponse = z.infer<typeof LoginResponseSchema>;
export type MagicLinkResponse = z.infer<typeof MagicLinkResponseSchema>;
export type RegisterUserResponse = z.infer<typeof RegisterUserResponseSchema>;
export type LogoutResponse = z.infer<typeof LogoutResponseSchema>;
export type CurrentSessionResponse = z.infer<typeof CurrentSessionResponseSchema>;
export type VerifyAuthResponse = z.infer<typeof VerifyAuthResponseSchema>;
export type RecoveryResponse = z.infer<typeof RecoveryResponseSchema>;
```

```typescript
// modules/auth/shared/contracts/verify-auth.contract.ts

import { z } from "zod";
import { S } from "@/shared/kernel/schemas";

export const VerifyTokenHashInputSchema = z.object({
  token_hash: S.common.requiredText,
});

export type VerifyTokenHashInput = z.infer<typeof VerifyTokenHashInputSchema>;
```

```typescript
// modules/auth/shared/contracts/index.ts

export * from "./auth.contract";
export * from "./register-user.contract";
export * from "./verify-auth.contract";
```

---

## Auth Service

Service layer with redirect URL construction and **business event logging**:

```typescript
// modules/auth/services/auth.service.ts

import type { IAuthRepository } from "../repositories/auth.repository";
import type {
  AuthUser,
  AuthResult,
  AuthenticatedAuthResult,
} from "../models/auth.models";
import type { AppLogger } from "@/shared/kernel/logger";
import { getSafeRedirectPath } from "@/shared/lib/redirects";

export interface IAuthService {
  getCurrentUser(): Promise<AuthUser | null>;
  signIn(email: string, password: string): Promise<AuthenticatedAuthResult>;
  signInWithMagicLink(email: string, baseUrl: string, redirect?: string): Promise<AuthResult>;
  signUp(email: string, password: string, baseUrl: string, redirect?: string): Promise<AuthResult>;
  signOut(): Promise<void>;
  exchangeCodeForSession(code: string): Promise<AuthenticatedAuthResult>;
  // PKCE flow methods
  verifyMagicLink(tokenHash: string): Promise<AuthResult>;
  verifySignUp(tokenHash: string): Promise<AuthResult>;
  verifyRecovery(tokenHash: string): Promise<void>;
}

export class AuthService implements IAuthService {
  constructor(
    private readonly authRepository: IAuthRepository,
    private readonly logger: AppLogger,
  ) {}

  async getCurrentUser(): Promise<AuthUser | null> {
    return this.authRepository.getCurrentUser();
  }

  async signIn(email: string, password: string): Promise<AuthenticatedAuthResult> {
    const result = await this.authRepository.signInWithPassword(email, password);

    this.logger.info(
      { "otel.event.name": "user.logged_in", "user.id": result.user.id },
      "User logged in",
    );

    return result;
  }

  async signInWithMagicLink(email: string, baseUrl: string, redirect?: string): Promise<AuthResult> {
    // PKCE flow: redirect to /auth/confirm with an explicit, safe in-app redirect
    const safeRedirect = getSafeRedirectPath(redirect, { fallback: "/" });
    const redirectTo = `${baseUrl}/auth/confirm?redirect=${encodeURIComponent(safeRedirect)}`;
    const result = await this.authRepository.signInWithOtp(email, redirectTo);

    this.logger.info(
      { "otel.event.name": "user.magic_link_requested" },
      "Magic link requested",
    );

    return result;
  }

  async signUp(email: string, password: string, baseUrl: string, redirect?: string): Promise<AuthResult> {
    // PKCE flow: redirect to /auth/confirm with an explicit, safe in-app redirect
    const safeRedirect = getSafeRedirectPath(redirect, { fallback: "/" });
    const redirectTo = `${baseUrl}/auth/confirm?redirect=${encodeURIComponent(safeRedirect)}`;
    const result = await this.authRepository.signUp(email, password, redirectTo);

    if (result.user) {
      this.logger.info(
        { "otel.event.name": "user.registered", "user.id": result.user.id },
        "User registered",
      );
    }

    return result;
  }

  async signOut(): Promise<void> {
    await this.authRepository.signOut();

    this.logger.info(
      { "otel.event.name": "user.logged_out" },
      "User logged out",
    );
  }

  async exchangeCodeForSession(code: string): Promise<AuthenticatedAuthResult> {
    const result = await this.authRepository.exchangeCodeForSession(code);

    if (result.user) {
      this.logger.info(
        { "otel.event.name": "user.session_exchanged", "user.id": result.user.id },
        "Session exchanged from code",
      );
    }

    return result;
  }

  // PKCE flow methods
  async verifyMagicLink(tokenHash: string): Promise<AuthResult> {
    const result = await this.authRepository.verifyMagicLink(tokenHash);

    if (result.user) {
      this.logger.info(
        { "otel.event.name": "user.magic_link_verified", "user.id": result.user.id },
        "Magic link verified",
      );
    }

    return result;
  }

  async verifySignUp(tokenHash: string): Promise<AuthResult> {
    const result = await this.authRepository.verifySignUp(tokenHash);

    if (result.user) {
      this.logger.info(
        { "otel.event.name": "user.signup_verified", "user.id": result.user.id },
        "Signup verified",
      );
    }

    return result;
  }

  async verifyRecovery(tokenHash: string): Promise<void> {
    await this.authRepository.verifyRecovery(tokenHash);

    this.logger.info(
      { "otel.event.name": "user.recovery_verified" },
      "Password recovery verified",
    );
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

export type UserRoleRow = typeof userRoles.$inferSelect;
export type InsertUserRoleRow = typeof userRoles.$inferInsert;
```

**Key Points:**
- Uses `authUsers` from `drizzle-orm/supabase` to reference Supabase's `auth.users`
- `onDelete: "cascade"` ensures cleanup when Supabase user is deleted
- Role is application-defined (not Supabase's built-in roles)

### Repository

Define the application record/input independently of the table. In this example global role names remain project-specific strings; validation and grant policy belong to the owning application operation.

```typescript
// modules/user-role/models/user-role.ts
export interface UserRoleRecord {
  id: string;
  userId: string;
  role: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface InsertUserRole {
  userId: string;
  role: string;
}
```

```typescript
// modules/user-role/repositories/user-role.repository.ts

import { eq } from "drizzle-orm";
import { userRoles, type UserRoleRow } from "@/shared/infra/db/schema";
import type { UserRoleRecord, InsertUserRole } from "../models/user-role";
import type { TransactionOptions } from "@/shared/kernel/transaction";
import type { DbClient, DrizzleTransaction } from "@/shared/infra/db/types";

export interface IUserRoleRepository {
  findByUserId(userId: string, options?: TransactionOptions): Promise<UserRoleRecord | null>;
  create(data: InsertUserRole, options?: TransactionOptions): Promise<UserRoleRecord>;
  ensureExists(data: InsertUserRole, options: TransactionOptions): Promise<UserRoleRecord>;
}

function toUserRoleRecord(row: UserRoleRow): UserRoleRecord {
  return {
    id: row.id,
    userId: row.userId,
    role: row.role,
    createdAt: row.createdAt,
    updatedAt: row.updatedAt,
  };
}

export class UserRoleRepository implements IUserRoleRepository {
  constructor(private db: DbClient) {}

  private getClient(options?: TransactionOptions): DbClient | DrizzleTransaction {
    return (options?.tx as unknown as DrizzleTransaction) ?? this.db;
  }

  async findByUserId(userId: string, options?: TransactionOptions): Promise<UserRoleRecord | null> {
    const client = this.getClient(options);
    const result = await client
      .select()
      .from(userRoles)
      .where(eq(userRoles.userId, userId))
      .limit(1);

    return result[0] ? toUserRoleRecord(result[0]) : null;
  }

  async create(data: InsertUserRole, options?: TransactionOptions): Promise<UserRoleRecord> {
    const client = this.getClient(options);
    const result = await client.insert(userRoles).values(data).returning();
    return toUserRoleRecord(result[0]);
  }

  async ensureExists(
    data: InsertUserRole,
    options: TransactionOptions,
  ): Promise<UserRoleRecord> {
    const client = this.getClient(options);
    const inserted = await client
      .insert(userRoles)
      .values(data)
      .onConflictDoNothing({ target: userRoles.userId })
      .returning();

    return inserted[0]
      ? toUserRoleRecord(inserted[0])
      : (await this.findByUserId(data.userId, options))!;
  }
}
```

### Service

```typescript
// modules/user-role/services/user-role.service.ts

import type { TransactionManager } from "@/shared/kernel/transaction";
import type { TransactionOptions } from "@/shared/kernel/transaction";
import type { IUserRoleRepository } from "../repositories/user-role.repository";
import type { UserRoleRecord, InsertUserRole } from "../models/user-role";
import { UserRoleAlreadyExistsError } from "../errors/user-role.errors";

export interface IUserRoleService {
  findByUserId(userId: string, options?: TransactionOptions): Promise<UserRoleRecord | null>;
  create(data: InsertUserRole, options?: TransactionOptions): Promise<UserRoleRecord>;
  ensureExists(data: InsertUserRole, options: TransactionOptions): Promise<UserRoleRecord>;
}

export class UserRoleService implements IUserRoleService {
  constructor(
    private userRoleRepository: IUserRoleRepository,
    private transactionManager: TransactionManager,
  ) {}

  async findByUserId(userId: string, options?: TransactionOptions): Promise<UserRoleRecord | null> {
    return this.userRoleRepository.findByUserId(userId, options);
  }

  async create(data: InsertUserRole, options?: TransactionOptions): Promise<UserRoleRecord> {
    if (options?.tx) {
      return this.createInternal(data, options);
    }
    return this.transactionManager.run((tx) => this.createInternal(data, { tx }));
  }

  async ensureExists(
    data: InsertUserRole,
    options: TransactionOptions,
  ): Promise<UserRoleRecord> {
    return this.userRoleRepository.ensureExists(data, options);
  }

  private async createInternal(data: InsertUserRole, options: TransactionOptions): Promise<UserRoleRecord> {
    const existing = await this.userRoleRepository.findByUserId(data.userId, options);
    if (existing) {
      throw new UserRoleAlreadyExistsError(data.userId);
    }
    return this.userRoleRepository.create(data, options);
  }
}
```

---

## Managed User Provisioning Use Case

The compensating workflow below is for a trusted/admin flow that must create provider and local state immediately. Do not use it for public self-signup because doing so can defeat Supabase's email-enumeration protections.

```typescript
// modules/auth/use-cases/provision-managed-user.use-case.ts

import type { IAuthService } from "../services/auth.service";
import type { IUserRoleService } from "@/modules/user-role/services/user-role.service";
import type { TransactionManager } from "@/shared/kernel/transaction";
import type { AppLogger } from "@/shared/kernel/logger";
import type { RegisterUserInput } from "../shared/contracts";
import {
  AuthRegistrationFailedError,
  UserProvisioningFailedError,
} from "../errors/auth.errors";

export interface IAuthProvisioningCompensator {
  deleteUser(userId: string): Promise<void>;
}

export class ProvisionManagedUserUseCase {
  constructor(
    private readonly authService: IAuthService,
    private readonly userRoleService: IUserRoleService,
    private readonly authCompensator: IAuthProvisioningCompensator,
    private readonly transactionManager: TransactionManager,
    private readonly logger: AppLogger,
  ) {}

  async execute(input: RegisterUserInput, baseUrl: string) {
    // 1. Create user in Supabase (outside transaction - external service)
    const result = await this.authService.signUp(
      input.email,
      input.password,
      baseUrl,
    );

    if (!result.user) {
      throw new AuthRegistrationFailedError();
    }

    // 2. Provision local state. This cannot share a transaction with Supabase Auth.
    try {
      await this.transactionManager.run(async (tx) => {
        await this.userRoleService.create(
          { userId: result.user!.id, role: "member" },
          { tx },
        );
      });
    } catch (error) {
      try {
        await this.authCompensator.deleteUser(result.user.id);
      } catch (compensationError) {
        this.logger.error(
          {
            err: compensationError,
            "otel.event.name": "auth.user_provisioning.compensation_failed",
            "user.id": result.user.id,
          },
          "User provisioning compensation failed",
        );
      }
      throw new UserProvisioningFailedError(result.user.id);
    }

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
- The flow is a saga, not one atomic transaction: local provisioning failure triggers best-effort provider compensation
- Authorization fails closed when no local role exists, and a reconciliation job must repair any failed compensation
- The compensator is an infrastructure adapter using privileged credentials; it is injected only into the use case

For public self-signup, return the same `{ accepted: true }` response whether the address is new or already registered. Complete local role/profile provisioning only after verified signup, using an idempotent `CompleteSignupUseCase`. If local provisioning temporarily fails, protected authorization remains fail-closed and reconciliation retries it.

```typescript
export class CompleteSignupUseCase {
  constructor(
    private readonly authService: IAuthService,
    private readonly userRoleService: IUserRoleService,
    private readonly transactionManager: TransactionManager,
    private readonly logger: AppLogger,
  ) {}

  async execute(tokenHash: string): Promise<AuthResult> {
    const result = await this.authService.verifySignUp(tokenHash);
    if (!result.user) throw new AuthRegistrationFailedError();

    await this.transactionManager.run(async (tx) => {
      await this.userRoleService.ensureExists(
        { userId: result.user!.id, role: "member" },
        { tx },
      );
    });

    this.logger.info(
      {
        "otel.event.name": "auth.signup_provisioned",
        "user.id": result.user.id,
      },
      "Verified signup provisioned",
    );

    return result;
  }
}
```

`ensureExists` is idempotent under a unique `userId` constraint. Repeated verification/callback delivery must not create duplicate roles.

---

## Auth Factories (Request-Scoped)

Auth factories are **request-scoped** because Supabase client needs cookies:

```typescript
// modules/auth/factories/auth.factory.ts

import type { CookieMethodsServer } from "@supabase/ssr";
import { createClient } from "@/shared/infra/supabase/create-client";
import { createPrivilegedAuthClient } from "@/shared/infra/supabase/privileged-client";
import { env } from "@/lib/env";
import { getContainer } from "@/shared/infra/container";
import { AuthRepository } from "../repositories/auth.repository";
import { AuthService } from "../services/auth.service";
import { ProvisionManagedUserUseCase } from "../use-cases/provision-managed-user.use-case";
import { CompleteSignupUseCase } from "../use-cases/complete-signup.use-case";
import {
  CurrentSessionController,
  ExchangeOAuthCodeController,
  LoginController,
  LoginWithMagicLinkController,
  LogoutController,
  RegisterController,
  VerifyMagicLinkController,
  VerifyRecoveryController,
  VerifySignupController,
} from "../controllers";
import { SupabaseAuthProvisioningCompensator } from "../providers/supabase-auth-provisioning-compensator";
import { makeUserRoleService } from "@/modules/user-role/factories/user-role.factory";

/**
 * Auth factories are REQUEST-SCOPED (not lazy singletons)
 * because Supabase client needs request-specific cookies.
 */
export function makeAuthRepository(cookies: CookieMethodsServer) {
  const client = createClient(
    env.SUPABASE_URL,
    env.SUPABASE_PUBLISHABLE_KEY,
    cookies,
  );
  return new AuthRepository(client);
}

// This request-scoped user client deliberately uses the publishable key. The
// authenticated user's JWT determines authorization and RLS behavior. Only
// `createPrivilegedAuthClient` uses `SUPABASE_SECRET_KEY`.

function makeAuthService(cookies: CookieMethodsServer) {
  return new AuthService(
    makeAuthRepository(cookies),
    getContainer().appLogger,
  );
}

function makeAuthProvisioningCompensator() {
  return new SupabaseAuthProvisioningCompensator(
    createPrivilegedAuthClient(),
  );
}

export function makeProvisionManagedUserUseCase(cookies: CookieMethodsServer) {
  return new ProvisionManagedUserUseCase(
    makeAuthService(cookies),
    makeUserRoleService(),
    makeAuthProvisioningCompensator(),
    getContainer().transactionManager,
    getContainer().appLogger,
  );
}

export function makeCompleteSignupUseCase(cookies: CookieMethodsServer) {
  return new CompleteSignupUseCase(
    makeAuthService(cookies),
    makeUserRoleService(),
    getContainer().transactionManager,
    getContainer().appLogger,
  );
}

// Framework adapters resolve only these outer, request-scoped factories.
export const makeLoginController = (cookies: CookieMethodsServer) =>
  new LoginController(makeAuthService(cookies));
export const makeLoginWithMagicLinkController = (cookies: CookieMethodsServer) =>
  new LoginWithMagicLinkController(makeAuthService(cookies));
export const makeRegisterController = (cookies: CookieMethodsServer) =>
  new RegisterController(makeAuthService(cookies));
export const makeLogoutController = (cookies: CookieMethodsServer) =>
  new LogoutController(makeAuthService(cookies));
export const makeCurrentSessionController = (cookies: CookieMethodsServer) =>
  new CurrentSessionController(makeAuthService(cookies));
export const makeExchangeOAuthCodeController = (cookies: CookieMethodsServer) =>
  new ExchangeOAuthCodeController(makeAuthService(cookies));
export const makeVerifyMagicLinkController = (cookies: CookieMethodsServer) =>
  new VerifyMagicLinkController(makeAuthService(cookies));
export const makeVerifySignupController = (cookies: CookieMethodsServer) =>
  new VerifySignupController(makeCompleteSignupUseCase(cookies));
export const makeVerifyRecoveryController = (cookies: CookieMethodsServer) =>
  new VerifyRecoveryController(makeAuthService(cookies));
```

---

## tRPC Context

The context extracts session from Supabase and enriches with role from database:

```typescript
// shared/infra/trpc/context.ts

import { randomUUID } from "crypto";
import { cookies } from "next/headers";
import type { FetchCreateContextFnOptions } from "@trpc/server/adapters/fetch";
import type { CookieMethodsServer } from "@supabase/ssr";
import type { AppLogger } from "@/shared/kernel/logger";
import {
  getObservabilityContext,
  getTrustedClientIdentifier,
  getTrustedRequestId,
} from "@/shared/infra/observability";
import type { Session } from "@/shared/kernel/auth";

export interface Context {
  requestId: string;
  session: Session | null;
  userId: string | null;
  clientIdentifier: string | null;
  clientIdentifierSource: "authenticated_user" | "trusted_network" | null;
  cookies: CookieMethodsServer;
  origin: string;
  log: AppLogger;
}

export interface AuthenticatedContext extends Context {
  session: Session;
  userId: string;
}

export interface SessionResolver {
  resolve(cookieMethods: CookieMethodsServer): Promise<Session | null>;
}

interface ContextDependencies {
  sessionResolver: SessionResolver;
  log: AppLogger;
  applicationOrigin: string;
}

export function makeCreateContext(deps: ContextDependencies) {
  return async function createContext(
    { req }: FetchCreateContextFnOptions,
  ): Promise<Context> {
    const requestId =
      getObservabilityContext()?.requestId ??
      getTrustedRequestId(req.headers) ??
      randomUUID();
    const cookieStore = await cookies();
    const client = getTrustedClientIdentifier(req.headers);

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

    // The module-owned resolver composes AuthService and UserRoleService. It
    // returns null only for genuine anonymous/expired sessions. Provider or
    // database outages remain typed errors and propagate to central mapping.
    const session = await deps.sessionResolver.resolve(cookieMethods);

    return {
      requestId,
      session,
      userId: session?.userId ?? null,
      clientIdentifier: session?.userId ?? client?.value ?? null,
      clientIdentifierSource: session
        ? "authenticated_user"
        : client?.source ?? null,
      cookies: cookieMethods,
      origin: new URL(deps.applicationOrigin).origin,
      log: deps.log,
    };
  };
}
```

Compose `makeCreateContext` in the Next.js/tRPC entrypoint with a
module-owned `SessionResolver`, `appLogger`, and validated application origin.
The shared context adapter does not construct Supabase clients or call module
repositories directly.

---

## tRPC Middleware & Procedures

**Important:** Define all middleware inline in `trpc.ts` to avoid circular dependencies. Do NOT create separate middleware files that import from `trpc.ts`.

```typescript
// shared/infra/trpc/trpc.ts

import { initTRPC, TRPCError } from "@trpc/server";
import {
  AppError,
  AuthenticationError,
  type AppErrorKind,
} from "@/shared/kernel/errors";
import {
  getPublicErrorMessage,
  canExposeErrorDetails,
  GENERIC_PUBLIC_ERROR_MESSAGE,
} from "@/shared/kernel/public-error";
import { appLogger } from "@/shared/infra/logger";
import { APP_ATTRIBUTES } from "@/shared/infra/observability/attributes";
import { getObservabilityContext } from "@/shared/infra/observability";
import type { Context, AuthenticatedContext } from "./context";

function pickPublicTrpcShapeData(
  shapeData: Record<string, unknown>,
): Record<string, unknown> {
  const picked: Record<string, unknown> = {};
  if ("path" in shapeData) picked.path = shapeData.path;
  if ("zodError" in shapeData) picked.zodError = shapeData.zodError;
  return picked;
}

const t = initTRPC.context<Context>().create({
  errorFormatter({ error, shape, ctx }) {
    const cause = error.cause;
    const requestId =
      ctx?.requestId ?? getObservabilityContext()?.requestId ?? "unknown";

    if (cause instanceof AppError) {
      appLogger.warn(
        {
          err: cause,
          "error.type": cause.code,
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

    appLogger.error(
      { err: error, "error.type": error.constructor.name },
      "Unexpected error",
    );
    return {
      ...shape,
      message: GENERIC_PUBLIC_ERROR_MESSAGE,
      data: {
        ...pickPublicTrpcShapeData(shape.data),
        appCode: "INTERNAL_ERROR",
        requestId,
      },
    };
  },
});

export const router = t.router;
export const middleware = t.middleware;

const TRPC_CODE_BY_KIND = {
  validation: "BAD_REQUEST",
  authentication: "UNAUTHORIZED",
  authorization: "FORBIDDEN",
  not_found: "NOT_FOUND",
  conflict: "CONFLICT",
  business_rule: "UNPROCESSABLE_CONTENT",
  rate_limit: "TOO_MANY_REQUESTS",
  internal: "INTERNAL_SERVER_ERROR",
  bad_gateway: "BAD_GATEWAY",
  unavailable: "SERVICE_UNAVAILABLE",
  timeout: "GATEWAY_TIMEOUT",
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
      "otel.event.name": "rpc.request.started",
      "rpc.system": "trpc",
      "rpc.method": path,
      [APP_ATTRIBUTES.operationType]: type,
    },
    "Request started",
  );

  // The logger adapter's configured level suppresses debug records in
  // environments where they are disabled.
  ctx.log.debug({}, "Request processing");

  try {
    const result = await next({ ctx });
    const duration = Date.now() - start;

    ctx.log.info(
      {
        "otel.event.name": "rpc.request.completed",
        "rpc.system": "trpc",
        "rpc.method": path,
        [APP_ATTRIBUTES.operationType]: type,
        [APP_ATTRIBUTES.durationMs]: duration,
        [APP_ATTRIBUTES.operationOutcome]: "success",
      },
      "Request completed",
    );

    return result;
  } catch (error) {
    const duration = Date.now() - start;

    ctx.log.info(
      {
        "otel.event.name": "rpc.request.failed",
        "rpc.system": "trpc",
        "rpc.method": path,
        [APP_ATTRIBUTES.operationType]: type,
        [APP_ATTRIBUTES.durationMs]: duration,
        [APP_ATTRIBUTES.operationOutcome]: "error",
      },
      "Request failed",
    );

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
 * Base procedure with central error mapping and logging.
 */
const baseProcedure = t.procedure
  .use(appErrorMiddleware)
  .use(loggerMiddleware);

export const publicProcedure = baseProcedure;
export const protectedProcedure = baseProcedure.use(authMiddleware);
```

---

## Auth Router

```typescript
// modules/auth/auth.router.ts

import { router, publicProcedure, protectedProcedure } from "@/shared/infra/trpc/trpc";
import { wrapResponse } from "@/shared/utils/response";
import {
  makeCurrentSessionController,
  makeLoginController,
  makeLoginWithMagicLinkController,
  makeLogoutController,
  makeRegisterController,
  makeVerifyMagicLinkController,
  makeVerifyRecoveryController,
  makeVerifySignupController,
} from "./factories/auth.factory";
import {
  CurrentSessionResponseSchema,
  LoginInputSchema,
  LoginResponseSchema,
  LogoutResponseSchema,
  MagicLinkInputSchema,
  MagicLinkResponseSchema,
  RecoveryResponseSchema,
  RegisterUserInputSchema,
  RegisterUserResponseSchema,
  VerifyAuthResponseSchema,
  VerifyTokenHashInputSchema,
} from "./shared/contracts";

export const authRouter = router({
  login: publicProcedure
    .input(LoginInputSchema)
    .mutation(async ({ input, ctx }) => {
      const result = await makeLoginController(ctx.cookies).execute(input);
      const response = LoginResponseSchema.parse(result);
      return wrapResponse(response);
    }),

  loginWithMagicLink: publicProcedure
    .input(MagicLinkInputSchema)
    .mutation(async ({ input, ctx }) => {
      const result = await makeLoginWithMagicLinkController(ctx.cookies)
        .execute(input, { origin: ctx.origin });
      return wrapResponse(MagicLinkResponseSchema.parse(result));
    }),

  register: publicProcedure
    .input(RegisterUserInputSchema)
    .mutation(async ({ input, ctx }) => {
      const result = await makeRegisterController(ctx.cookies)
        .execute(input, { origin: ctx.origin });
      return wrapResponse(RegisterUserResponseSchema.parse(result));
    }),

  logout: protectedProcedure
    .mutation(async ({ ctx }) => {
      const result = await makeLogoutController(ctx.cookies).execute();
      return wrapResponse(LogoutResponseSchema.parse(result));
    }),

  me: protectedProcedure
    .query(async ({ ctx }) => {
      const result = await makeCurrentSessionController(ctx.cookies).execute(
        toActor(ctx.session),
      );
      const response = CurrentSessionResponseSchema.parse(result);
      return wrapResponse(response);
    }),

  // PKCE flow verification endpoints
  verifyMagicLink: publicProcedure
    .input(VerifyTokenHashInputSchema)
    .mutation(async ({ input, ctx }) => {
      const result = await makeVerifyMagicLinkController(ctx.cookies)
        .execute(input);
      const response = VerifyAuthResponseSchema.parse(result);
      return wrapResponse(response);
    }),

  verifySignUp: publicProcedure
    .input(VerifyTokenHashInputSchema)
    .mutation(async ({ input, ctx }) => {
      const result = await makeVerifySignupController(ctx.cookies)
        .execute(input);
      const response = VerifyAuthResponseSchema.parse(result);
      return wrapResponse(response);
    }),

  verifyRecovery: publicProcedure
    .input(VerifyTokenHashInputSchema)
    .mutation(async ({ input, ctx }) => {
      const result = await makeVerifyRecoveryController(ctx.cookies)
        .execute(input);
      return wrapResponse(RecoveryResponseSchema.parse(result));
    }),
});
```

---

## Next.js Proxy

Session refresh and route protection:

> **Note:** In Next.js 16+, `middleware.ts` is renamed to `proxy.ts` and the export is renamed from `middleware` to `proxy`. The proxy runtime is nodejs-only (edge runtime not supported).

```typescript
// proxy.ts

import { type NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";
import { env } from "@/env";

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
    env.NEXT_PUBLIC_SUPABASE_URL,
    env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
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

## Auth Confirm Route (PKCE Flow)

Handles magic link, signup confirmation, and password recovery:

```typescript
// app/auth/confirm/route.ts

import { type EmailOtpType } from "@supabase/supabase-js";
import type { CookieMethodsServer } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { appLogger } from "@/shared/infra/logger";
import {
  makeVerifyMagicLinkController,
  makeVerifyRecoveryController,
  makeVerifySignupController,
} from "@/modules/auth/factories/auth.factory";
import {
  APP_ATTRIBUTES,
  withRequestObservability,
} from "@/shared/infra/observability";

/**
 * Auth confirm route handler for PKCE flow (magic link, signup, recovery).
 * Verifies token_hash and creates session via verifyOtp.
 */
async function handleAuthConfirm(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const token_hash = searchParams.get("token_hash");
  const type = searchParams.get("type") as EmailOtpType | null;

  const redirectTo = request.nextUrl.clone();
  redirectTo.searchParams.delete("token_hash");
  redirectTo.searchParams.delete("type");

  // Default redirect to dashboard
  redirectTo.pathname = "/dashboard";

  if (!token_hash || !type) {
    appLogger.warn(
      {
        "otel.event.name": "auth.confirm.invalid_request",
        "code.function.name": "AuthConfirmRoute.GET",
        [APP_ATTRIBUTES.authVerificationType]: type,
      },
      "Missing token_hash or type parameter",
    );
    redirectTo.pathname = "/";
    return NextResponse.redirect(redirectTo);
  }

  const cookieStore = await cookies();
  const cookieMethods: CookieMethodsServer = {
    getAll() {
      return cookieStore.getAll();
    },
    setAll(cookiesToSet) {
      cookiesToSet.forEach(({ name, value, options }) => {
        cookieStore.set(name, value, options);
      });
    },
  };

  switch (type) {
    case "magiclink":
      try {
        const result = await makeVerifyMagicLinkController(cookieMethods)
          .execute({ tokenHash: token_hash });

        if (result.user) {
          appLogger.info(
            { "otel.event.name": "user.magic_link_verified", "user.id": result.user.id },
            "Magic link verified",
          );
        }

        return NextResponse.redirect(redirectTo);
      } catch (error) {
        appLogger.error(
          {
            "otel.event.name": "auth.verification.failed",
            "code.function.name": "AuthConfirmRoute.GET",
            "error.type": error instanceof Error ? error.constructor.name : "UnknownError",
            [APP_ATTRIBUTES.authVerificationType]: "magiclink",
            err: error,
          },
          "Magic link verification failed",
        );
      }
      break;

    case "signup":
      try {
        const result = await makeVerifySignupController(cookieMethods)
          .execute({ tokenHash: token_hash });

        if (result.user) {
          appLogger.info(
            {
              "otel.event.name": "user.signup_verified",
              [APP_ATTRIBUTES.targetUserId]: result.user.id,
            },
            "Signup verified",
          );
        }

        return NextResponse.redirect(redirectTo);
      } catch (error) {
        appLogger.error(
          {
            "otel.event.name": "auth.verification.failed",
            "code.function.name": "AuthConfirmRoute.GET",
            "error.type": error instanceof Error ? error.constructor.name : "UnknownError",
            [APP_ATTRIBUTES.authVerificationType]: "signup",
            err: error,
          },
          "Signup verification failed",
        );
      }
      break;

    case "recovery":
      try {
        await makeVerifyRecoveryController(cookieMethods)
          .execute({ tokenHash: token_hash });

        appLogger.info(
          { "otel.event.name": "user.recovery_verified" },
          "Password recovery verified",
        );

        return NextResponse.redirect(redirectTo);
      } catch (error) {
        appLogger.error(
          {
            "otel.event.name": "auth.verification.failed",
            "code.function.name": "AuthConfirmRoute.GET",
            "error.type": error instanceof Error ? error.constructor.name : "UnknownError",
            [APP_ATTRIBUTES.authVerificationType]: "recovery",
            err: error,
          },
          "Password recovery verification failed",
        );
      }
      break;

    default:
      appLogger.warn(
        {
          "otel.event.name": "auth.confirm.unknown_verification_type",
          "code.function.name": "AuthConfirmRoute.GET",
          [APP_ATTRIBUTES.authVerificationType]: type,
        },
        "Unknown verification type",
      );
  }

  // Fallback: redirect to home on error
  redirectTo.pathname = "/";
  return NextResponse.redirect(redirectTo);
}

export async function GET(request: NextRequest) {
  return withRequestObservability(request, () => handleAuthConfirm(request));
}
```

---

## Auth Callback Route (OAuth Flow)

Kept for OAuth providers that use authorization codes:

```typescript
// app/auth/callback/route.ts

import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import type { CookieMethodsServer } from "@supabase/ssr";
import { env } from "@/lib/env";
import { makeExchangeOAuthCodeController } from "@/modules/auth/factories/auth.factory";
import { handleError } from "@/shared/infra/http/error-handler";
import { withRequestObservability } from "@/shared/infra/observability";
import { getSafeRedirectPath } from "@/shared/lib/redirects";

function resolveSafeAppRedirect(
  requestedPath: string | null,
  appOrigin: string,
): URL {
  const trustedOrigin = new URL(appOrigin).origin;
  const safePath = getSafeRedirectPath(requestedPath ?? undefined, {
    fallback: "/",
  });

  // Defense in depth: URL parsing normalizes backslashes, so verify the final
  // resolved origin instead of trusting a string prefix check.
  try {
    const resolved = new URL(safePath, trustedOrigin);
    return resolved.origin === trustedOrigin
      ? resolved
      : new URL("/", trustedOrigin);
  } catch {
    return new URL("/", trustedOrigin);
  }
}

/**
 * Auth callback route handler for OAuth flows.
 * Exchanges authorization code for session.
 */
export async function GET(request: Request) {
  return withRequestObservability(request, async ({ requestId }) => {
    const { searchParams } = new URL(request.url);
    const code = searchParams.get("code");
    const appOrigin = new URL(env.NEXT_PUBLIC_APP_URL).origin;
    const successUrl = resolveSafeAppRedirect(
      searchParams.get("next"),
      appOrigin,
    );
    const failureUrl = new URL("/", appOrigin);
    failureUrl.searchParams.set("authError", "oauth_callback_failed");

    if (code) {
      const cookieStore = await cookies();
      const cookieMethods: CookieMethodsServer = {
        getAll: () => cookieStore.getAll(),
        setAll: (cookiesToSet) => cookiesToSet.forEach(
          ({ name, value, options }) => cookieStore.set(name, value, options),
        ),
      };

      try {
        await makeExchangeOAuthCodeController(cookieMethods).execute({ code });
        return NextResponse.redirect(successUrl);
      } catch (error) {
        // Browser OAuth callbacks need a safe redirect response. Reuse the
        // central mapper for one sanitized operational log, but do not expose
        // provider diagnostics in the redirect.
        handleError(error, requestId, {
          "otel.event.name": "auth.oauth_code_exchange.failed",
        });
        return NextResponse.redirect(failureUrl);
      }
    }

    // Missing code: redirect to the same safe application error destination.
    return NextResponse.redirect(failureUrl);
  });
}
```

The final-origin comparison is required even when a shared path sanitizer is
used: URL parsing treats backslashes as separators in special schemes, so a
prefix-only check can be bypassed. Exchange failures are logged once through
the central handler and become a same-origin browser redirect instead of an
unhandled route-level 500.

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

In a Next.js application, declare and validate these names in the canonical
[environment boundary](../../metaframeworks/nextjs/environment-variables.md).
The values below document deployment configuration; application code imports
the validated `env` object instead of reading `process.env` directly.

```bash
# .env.local

# App URL (production deployment URL)
# Used for constructing redirect URLs in code
NEXT_PUBLIC_APP_URL=https://yourdomain.com

# Supabase (public - safe to expose)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx

# Supabase (server-only - NEVER expose)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx
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
│   │   ├── callback/
│   │   │   └── route.ts          # OAuth callback (code exchange)
│   │   └── confirm/
│   │       └── route.ts          # PKCE callback (token_hash verification)
│   └── api/
│       └── trpc/
│           └── [trpc]/
│               └── route.ts
├── proxy.ts                       # Session refresh + route protection (Next.js 16+)
└── lib/
    ├── shared/
    │   ├── kernel/
    │   │   ├── auth.ts               # Session, UserRole, Permission
    │   │   ├── transaction.ts        # TransactionManager + TransactionOptions
    │   │   └── errors.ts             # Base error classes
    │   └── infra/
    │       ├── supabase/
    │       │   ├── create-client.ts  # SSR client factory
    │       │   ├── privileged-client.ts # Secret-key admin factory
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
    │       │   ├── context.ts        # Calls injected SessionResolver
    │       │   └── root.ts           # Root router
    │       └── container.ts          # Composition root
    └── modules/
        ├── auth/
        │   ├── shared/contracts/     # Public input/response payloads
        │   ├── models/               # Provider-neutral auth models
        │   ├── errors/
        │   ├── controllers/          # Framework-neutral auth capabilities
        │   ├── repositories/
        │   ├── services/
        │   ├── use-cases/
        │   │   ├── complete-signup.use-case.ts
        │   │   └── provision-managed-user.use-case.ts
        │   ├── providers/            # Privileged compensator adapter
        │   ├── factories/
        │   └── auth.router.ts
        └── user-role/
            ├── errors/
            ├── repositories/
            ├── services/
            └── factories/
```

---

## Checklist

### Supabase Dashboard Setup
- [ ] Create Supabase project
- [ ] Get publishable and secret keys
- [ ] **Set Site URL** to production domain (e.g., `https://yourdomain.com`)
- [ ] **Add Redirect URLs:**
  - `https://yourdomain.com` (root)
  - `http://localhost:3000` (dev root)
  - `https://yourdomain.com/auth/confirm**` (PKCE)
  - `https://yourdomain.com/auth/callback**` (OAuth)
  - `http://localhost:3000/auth/confirm**` (dev PKCE)
  - `http://localhost:3000/auth/callback**` (dev OAuth)
- [ ] **Configure email templates** to use `{{ .RedirectTo }}&token_hash={{ .TokenHash }}&type=...` (or push via `supabase config push`)

### Environment Variable Checks
- [ ] `NEXT_PUBLIC_APP_URL` set to production URL
- [ ] `NEXT_PUBLIC_SUPABASE_URL` configured
- [ ] `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` configured
- [ ] `SUPABASE_URL` configured
- [ ] `SUPABASE_PUBLISHABLE_KEY` configured for request-scoped user clients
- [ ] `SUPABASE_SECRET_KEY` configured
- [ ] `DATABASE_URL` configured

### Infrastructure
- [ ] `create-client.ts` with SSR cookie handling
- [ ] Database migrations for `user_roles` table

### Auth Module
- [ ] `AuthRepository` with PKCE methods (`verifyMagicLink`, `verifySignUp`, `verifyRecovery`)
- [ ] `AuthService` with redirect URL construction to `/auth/confirm?redirect=...`
- [ ] Domain errors (`InvalidCredentialsError`, etc.)
- [ ] Shared auth Zod contracts (including `VerifyTokenHashInputSchema`)
- [ ] Request-scoped factories

### User Role Module
- [ ] `user_roles` schema with FK to `auth.users`
- [ ] `UserRoleRepository` with transaction support
- [ ] `UserRoleService` with tx ownership pattern
- [ ] Lazy singleton factories

### tRPC Integration
- [ ] Context extracts session + role
- [ ] `publicProcedure` and `protectedProcedure` inherit shared error mapping + request logging
- [ ] Shared middleware maps `AppError.kind`; formatter sanitizes the public error shape
- [ ] Auth router with verification endpoints

### Next.js
- [ ] Proxy for session refresh (`proxy.ts`)
- [ ] Route protection works
- [ ] `/auth/confirm` route handler for PKCE
- [ ] `/auth/callback` route handler for OAuth

### Registration Flow
- [ ] Public self-signup always returns the same accepted response and does not expose account existence
- [ ] `CompleteSignupUseCase` provisions the local role idempotently after verification
- [ ] Authorization fails closed while the local role is missing
- [ ] Reconciliation retries failed post-verification provisioning
- [ ] Optional trusted managed-user provisioning tests provider compensation and failed-compensation repair
- [ ] Email confirmation flow works with PKCE

---

## Architecture Alignment

| Core Principle | Supabase Auth Implementation |
|----------------|------------------------------|
| **Repository pattern** | `AuthRepository` wraps Supabase Auth client |
| **Service layer** | `AuthService` adds business logic (redirect URLs) |
| **Domain errors** | Supabase errors mapped to `AppError` subclasses |
| **Request-scoped DI** | Factories accept `cookies` parameter |
| **Transaction ownership** | `UserRoleService` owns DB transaction |
| **Use case orchestration** | `CompleteSignupUseCase` provisions verified users; trusted managed provisioning uses compensation |
| **Kernel types** | `Session`, `UserRole`, `Permission` in kernel |
| **PKCE flow** | `verifyOtp` with `token_hash` for magic links |
