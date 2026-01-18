# Next.js Architecture Overview

> Next.js-specific conventions and routing patterns for this frontend architecture.

## Purpose

This section documents **Next.js App Router** patterns that sit on top of the general frontend architecture. It focuses on:

- Route structure and layout groups
- Server-side auth guarding using `proxy.ts`
- Type-safe route definitions and redirects
- Client data fetching with tRPC React Query hooks
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

## tRPC Client (React Query Hooks)

| Concern | Pattern | Location |
| --- | --- | --- |
| Client entrypoint | `createTRPCReact<AppRouter>()` export as `trpc` | `src/trpc/client.ts` |
| Provider wiring | `trpc.Provider` + `QueryClientProvider` | `src/components/providers.tsx` |
| Queries | `trpc.<router>.<procedure>.useQuery(input?, opts?)` | client components/hooks |
| Mutations | `trpc.<router>.<procedure>.useMutation({ onSuccess, onError })` | client components/hooks |
| Invalidation | `const utils = trpc.useUtils()` + `utils.<router>.<procedure>.invalidate()` | client components/hooks |

### Usage Guidelines

- Use `mutation.mutate(input)` or `await mutation.mutateAsync(input)` for writes.
- Prefer `trpc.useQueries((t) => [t.foo.bar(input), ...])` for parallel fetches.
- Use `select` to map API data into UI shapes.
- Avoid `useTRPC`, `useTRPCClient`, `queryOptions`, and `mutationOptions`.

## Forms & Validation

Use shared form conventions for consistent UX:

- Use `react-hook-form` + `zodResolver` for all forms.
- Prefer StandardForm components (see `client/references/09-standard-form-components.md`).
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
| [Auth + Routing Skill](./skills/nextjs-auth-routing/SKILL.md) | Type-safe routing + proxy-based auth guarding |

## Checklist for New Routes

- [ ] Add route to `app-routes.ts`
- [ ] Use `appRoutes` helpers for links and redirects
- [ ] Ensure `proxy.ts` covers access requirements
- [ ] Confirm layout guard for route group
