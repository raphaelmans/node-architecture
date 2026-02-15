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
| Server auth checks | `server-session.ts`-style helpers | project-specific server layer (for example `src/lib/shared/infra/auth/server-session.ts`) |
| Layout groups | Route groups per access level | `src/app/(<group>)/...` |

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
- Query adapters should depend on `I<Feature>Api` contracts, not transport clients.
- Feature APIs are class-based (`class <Feature>Api implements I<Feature>Api`) and created via factories.
- Components only wire loading/error/UI and never implement transport logic.
- Invalidation ownership may be hook-owned (preferred) or component-coordinator (allowed) based on route/form orchestration needs.
- Prefer typed, injected interfaces at each layer to enable testing doubles.

Decision matrix and scenarios:

- `client/frameworks/reactjs/server-state-patterns-react.md`

## Forms & Validation

Use shared form conventions for consistent UX:

- Use `react-hook-form` + `zodResolver` for all forms.
- Prefer StandardForm components (`client/frameworks/reactjs/forms-react-hook-form.md`).
- Use `mutateAsync` in submit handlers; avoid `mutate` in forms.
- Normalize submit errors to `AppError`.
- Map validation errors to form fields/root; use toast for non-validation errors.
- Never reset on error; reset on success only when the flow requires it.

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

## Request Metadata Flow

At metaframework boundaries, you may propagate request metadata for guards and diagnostics.

Common examples:

- `x-pathname` for layout/route guard context
- `x-request-id` for cross-layer error/log correlation

Treat header names and exact mechanics as implementation details; the architecture rule is to keep this at boundaries, not in presentation components.

## Next.js-Specific Docs

| Document | Description |
| --- | --- |
| [React Server-State Cookbook](../../server-state-patterns-react.md) | Mixed invalidation ownership patterns and scenario matrix |
| [Auth + Routing Skill](../../../../../skills/client/metaframeworks/nextjs/nextjs-auth-routing/SKILL.md) | Type-safe routing + proxy-based auth guarding |

## Checklist for New Routes

- [ ] Add route to `app-routes.ts`
- [ ] Use `appRoutes` helpers for links and redirects
- [ ] Ensure `proxy.ts` covers access requirements
- [ ] Confirm layout guard for route group
