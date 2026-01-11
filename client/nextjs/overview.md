# Next.js Architecture Overview

> Next.js-specific conventions and routing patterns for this frontend architecture.

## Purpose

This section documents **Next.js App Router** patterns that sit on top of the general frontend architecture. It focuses on:

- Route structure and layout groups
- Server-side auth guarding using `proxy.ts`
- Type-safe route definitions and redirects
- Where server-only code lives in the app

## Next.js Routing Model

```
┌─────────────────────────────────────────────────────────────┐
│                         App Router                          │
│                    (app/ directory)                         │
└─────────────────────────────┬───────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│        Layouts          │     │         Pages               │
│  (route groups,         │     │  (server components)        │
│   guards, shells)       │     │                             │
└───────────┬─────────────┘     └─────────────────────────────┘
            │
            ▼
┌─────────────────────────┐
│   Feature Components    │
│  (business + data)      │
└─────────────────────────┘
```

## Core Patterns

| Concern | Pattern | Location |
| --- | --- | --- |
| Route registry | `app-routes.ts` single source of truth | `src/shared/lib/app-routes.ts` |
| Auth guarding | `proxy.ts` (replaces middleware) | `src/proxy.ts` |
| Server auth checks | `server-session.ts` helpers | `src/shared/infra/auth/server-session.ts` |
| Layout groups | Route groups per access level | `src/app/(auth)/`, `src/app/(owner)/`, `src/app/(admin)/` |

## Route Types

Use route types to drive access control across the app:

- `public` — accessible to everyone
- `guest` — only unauthenticated users
- `protected` — authenticated users
- `owner` — authenticated + owner checks
- `admin` — authenticated + admin role

## Auth Guarding Flow

```
Request
  │
  ▼
proxy.ts
  │  ├─ refresh session
  │  ├─ set x-pathname header
  │  └─ redirect based on route type
  ▼
Layouts
  │  ├─ requireSession / requireAdminSession
  │  └─ render appropriate shell
  ▼
Pages + Features
```

## Next.js-Specific Docs

| Document | Description |
| --- | --- |
| [Auth + Routing Skill](./skills/nextjs-auth-routing/SKILL.md) | Type-safe routing + proxy-based auth guarding |

## Checklist for New Routes

- [ ] Add route to `app-routes.ts`
- [ ] Use `appRoutes` helpers for links and redirects
- [ ] Ensure `proxy.ts` covers access requirements
- [ ] Confirm layout guard for route group
