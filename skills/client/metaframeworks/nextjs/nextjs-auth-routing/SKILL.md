---
name: nextjs-auth-routing
description: Type-safe app routes + proxy-based auth guarding with server layouts in Next.js 16 (App Router)
---

# Next.js Auth + App Routes (Proxy + Server Layouts)

Use this skill when you need **type-safe routing**, a **single source of truth for route access**, and **server-side auth guarding** in Next.js 16+ using `proxy.ts`.

## Architecture / Overview

```
src/common/app-routes.ts              # route registry + helpers
src/proxy.ts                          # Next.js 16 proxy (replaces middleware)
src/shared/infra/auth/server-session.ts
src/app/(auth)/layout.tsx             # server guard using headers()
src/app/(owner)/layout.tsx            # role + org checks
src/app/(admin)/layout.tsx            # admin role guard
```

### Route Types
- `public` — accessible to everyone
- `guest` — only unauthenticated users
- `protected` — authenticated users
- `owner` — authenticated + owner checks
- `admin` — authenticated + admin role

---

## Step-by-Step

### 1) Create a Type-Safe Route Registry

Create `src/common/app-routes.ts`:

```ts
export type RouteType = "public" | "guest" | "protected" | "owner" | "admin";

export const appRoutes = {
  index: { base: "/", options: { type: "public" as const } },
  login: { base: "/login", options: { type: "guest" as const } },
  home: { base: "/home", options: { type: "protected" as const } },
  courts: {
    base: "/courts",
    options: { type: "public" as const },
    detail: (id: string) => `/courts/${id}`,
  },
  owner: {
    base: "/owner",
    options: { type: "owner" as const },
    onboarding: "/owner/onboarding",
  },
  admin: {
    base: "/admin",
    options: { type: "admin" as const },
  },
};

export function getRouteType(pathname: string): RouteType {
  // implement exact-or-child matching
}

export const isProtectedRoute = (pathname: string) => {
  const type = getRouteType(pathname);
  return type === "protected" || type === "owner" || type === "admin";
};
```

Include helper builders for dynamic routes and `login.from(path)` helpers.

---

### 2) Update `proxy.ts` (Next.js 16 replacement for middleware)

Use `proxy.ts` to refresh the session, enforce route access, and inject `x-pathname` for layouts:

```ts
import { appRoutes, isGuestRoute, isProtectedRoute } from "@/common/app-routes";

export async function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-pathname", path);

  let response = NextResponse.next({ request: { headers: requestHeaders } });

  const { data: { user } } = await supabase.auth.getUser();

  if (!user && isProtectedRoute(path)) {
    return NextResponse.redirect(new URL(appRoutes.login.from(path), request.url));
  }

  if (user && isGuestRoute(path)) {
    return NextResponse.redirect(new URL(appRoutes.home.base, request.url));
  }

  return response;
}
```

---

### 3) Add Server Session Helpers

Create `src/shared/infra/auth/server-session.ts` using server cookies + factory repos:

```ts
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { createClient } from "@/shared/infra/supabase/create-client";
import { makeUserRoleRepository } from "@/modules/user-role/factories/user-role.factory";
import { appRoutes } from "@/common/app-routes";

export async function getServerSession() { /* fetch user + role */ }
export async function requireSession(pathname: string) { /* redirect */ }
export async function requireAdminSession(pathname: string) { /* role check */ }
```

Use the factory/service layer (preferred) instead of client-only Supabase in layouts.

---

### 4) Server-Side Guarded Layouts

In `src/app/(auth)/layout.tsx` (server component):

```ts
import { headers } from "next/headers";
import { requireSession, requireAdminSession } from "@/shared/infra/auth/server-session";
import { appRoutes, getRouteType } from "@/common/app-routes";

export const dynamic = "force-dynamic";

export default async function AuthLayout({ children }) {
  const pathname = headers().get("x-pathname") ?? appRoutes.index.base;
  const routeType = getRouteType(pathname);

  if (routeType === "guest" || routeType === "public") {
    return <PublicShell>{children}</PublicShell>;
  }

  if (routeType === "admin") await requireAdminSession(pathname);
  else await requireSession(pathname);

  return <PlayerShell>{children}</PlayerShell>;
}
```

Role-specific layouts (`(owner)` and `(admin)`) can add extra checks (organization, role, etc.).

---

### 5) Replace Hardcoded Routes

Replace all literals with `appRoutes.*`:

- Nav items, links, `router.push`, redirects
- `PageHeader` breadcrumbs
- CTA links, empty states, footer links

---

## Checklist

- [ ] `app-routes.ts` defines all route bases + builders
- [ ] `proxy.ts` uses `appRoutes` + `x-pathname`
- [ ] Server session helper uses factories / repositories
- [ ] `(auth)` layout is server-side with `headers()`
- [ ] All literals replaced by `appRoutes`
- [ ] Guest and protected redirects verified
