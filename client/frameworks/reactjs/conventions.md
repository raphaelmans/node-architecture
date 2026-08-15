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
- Cookbook (mixed ownership patterns): `client/frameworks/reactjs/server-state-patterns-react.md`

Feature API contract for hook dependencies:

- query hooks should depend on `I<Feature>Api` contracts
- feature API implementations stay in `src/features/<feature>/api.ts` as `class <Feature>Api implements I<Feature>Api`

### Invalidation Ownership (Mixed, Explicit)

Two patterns are valid:

- Preferred default: hook-owned invalidation (reusable mutation behavior).
- Allowed: component-coordinator sequencing through a named query/cache-sync operation (route/form-local orchestration).

Choose component-coordinator sequencing when `submit -> sync -> navigate` is specific to one screen flow. Keep `queryClient`, tRPC utilities, and concrete query keys inside `hooks.ts`/`sync.ts`; the component calls the named sync operation.

## Operational Logging and Product Analytics

React implements the core telemetry ports without introducing a controller layer:

- `clientApi` owns transport logs and response `requestId` correlation.
- `featureApi` logs only contract/mapping failures it owns.
- reusable mutation hooks emit typed completion analytics after success when they own the action.
- business components emit only UI/workflow events they uniquely own.
- the framework error boundary owns unhandled render/runtime exceptions.
- presentation components do not import `debug`, Sentry, or analytics vendors.

Do not re-report a lower-boundary error in QueryClient defaults, hooks, and components.

## Composition and Lifetimes

- Create logger, analytics, transport, and feature APIs through named factories.
- Assemble browser instances once in the client composition root.
- Providers expose specific ports such as `ProductAnalytics`, never a complete runtime container.
- Feature runtime modules reference composition-root-owned instances; they do not create hidden singletons.
- Tests use the same factories with spies/fakes/no-op adapters.

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

## Testing Conventions (React)

- Query hook tests: mock `I<Feature>Api` methods, assert query keys/invalidation behavior.
- Mutation/workflow tests: use a `ProductAnalytics` spy and assert success-only typed events.
- Business component tests: mock feature hooks from `src/features/<feature>/hooks.ts`.
- Presentation component tests: render with props/fixtures only.
- Avoid transport-library mocks in component tests (`fetch`, `axios`, `trpc.*`).

## Forms

All form implementation details live in:

- `client/frameworks/reactjs/forms-react-hook-form.md`

## Migration Status (Known Drift)

These naming and SRP rules are canonical targets.
Existing codebases may still contain legacy names or mixed-responsibility hooks.

- New hooks and modified hooks should follow `useQuery*` / `useMut*` / `useMod*`.
- Legacy hooks migrate incrementally as files are touched.
- See `client/core/README.md` for the current drift summary.
