# Next.js Architecture Overview

> Next.js-specific conventions and routing patterns for this frontend architecture.

## Purpose

This section documents **Next.js App Router** patterns that sit on top of the general frontend architecture. It focuses on:

- Route structure and layout groups
- Server-side auth guarding using `proxy.ts`
- Type-safe route definitions and redirects
- How backend IO adapters plug into the client API architecture (tRPC, route handlers)
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
| Route registry | `app-routes.ts` single source of truth | `src/common/app-routes.ts` |
| Auth guarding | `proxy.ts` (replaces middleware) | `src/proxy.ts` |
| Server auth checks | `server-session.ts` helpers | `src/shared/infra/auth/server-session.ts` |
| Layout groups | Route groups per access level | `src/app/(guest)/`, `src/app/(authenticated)/` |

## Backend IO in Next.js (Client Perspective)

Next.js typically owns:

- server routing + layouts (SSR/RSC)
- server-only integrations and secrets
- API surfaces (tRPC handlers, `route.ts`)

Client features consume backend data through the **client API architecture**:

- `client/core/client-api-architecture.md`

For the current Next.js adapters:

- tRPC strategy: `./trpc.md`
- HTTP route handler strategy: `./ky-fetch.md`

### Usage Guidelines

- Queries/mutations are defined in the query adapter layer (React: `src/features/<feature>/hooks.ts`).
- Components only wire loading/error/UI and never implement transport logic.
- Prefer typed, injected interfaces at each layer to enable testing doubles.

## Forms & Validation

Use shared form conventions for consistent UX:

- Use `react-hook-form` + `zodResolver` for all forms.
- Prefer StandardForm components (draft reference: `client/drafts/09-standard-form-components.md`).
- Use `mutateAsync` in submit handlers; avoid `mutate` in forms.
- Show server errors via toast only; never reset on error.
- Reset form on success to clear dirty state.

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
| [Auth + Routing Skill](../../../../../skills/client/metaframeworks/nextjs/nextjs-auth-routing/SKILL.md) | Type-safe routing + proxy-based auth guarding |

## Checklist for New Routes

- [ ] Add route to `app-routes.ts`
- [ ] Use `appRoutes` helpers for links and redirects
- [ ] Ensure `proxy.ts` covers access requirements
- [ ] Confirm layout guard for route group
