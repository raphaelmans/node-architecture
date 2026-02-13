# ReactJS Conventions

> React-specific conventions layered on top of the core client architecture.

## Component Layers (React)

- Pages/routes are owned by the metaframework (e.g. Next.js App Router). React components should treat “page params” and SSR behavior as a metaframework concern.
- Business components orchestrate data + form state and compose sections.
- Presentation components render-only and consume props and/or form context.

## Server State (React Query Adapter)

React-specific rule:

- Define server-state hooks in `src/features/<feature>/hooks.ts`.
- Components do not inline server-state calls.

Where the hooks get data from is an adapter choice:

- Next.js + tRPC: see `client/frameworks/reactjs/metaframeworks/nextjs/trpc.md`
- Next.js + route handlers (HTTP): see `client/frameworks/reactjs/metaframeworks/nextjs/ky-fetch.md`

## Hook Naming (Server-State Only)

These conventions apply to **server-state hooks** (TanStack Query wrappers) defined in `src/features/<feature>/hooks.ts`.

### Queries (SRP)

- Prefix: `useQuery`
- Pattern: `useQuery<Feature><Noun><Qualifier?>`
- Single responsibility: one hook = one queryKey + one fetcher.

Examples:

- `useQueryProfileMe()`
- `useQueryUserById(userId)`
- `useQueryPostsList(filters)`
- `useQueryOrdersInfinite(params)`

### Mutations (SRP)

- Prefix: `useMut`
- Pattern: `useMut<Feature><Verb><Object?>`
- Single responsibility: one hook = one mutationFn.

Examples:

- `useMutProfileCreate()`
- `useMutProfileUpdate()`
- `useMutProfileUploadImage(profileId)`
- `useMutPostsLike()`

### Composed Hooks (Multiple Queries/Mutations)

When you need to combine `useQueryX1()` + `useQueryX2()` (and optionally `useMut*`), create a composed hook:

- Prefix: `useMod`
- Pattern: `useMod<Descriptive>`

Examples:

- `useModDashboard()` returns `{ profileQuery, statsQuery, notificationsQuery, ...derived }`
- `useModSettings()` returns `{ profileQuery, settingsQuery, preferencesQuery, ... }`

## Forms

All form implementation details live in:

- `client/frameworks/reactjs/forms-react-hook-form.md`
