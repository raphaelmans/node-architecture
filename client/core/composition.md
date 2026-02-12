# Composition + Server State (TanStack Query)

> Coordinate high. Fetch low. Render dumb.

This repo’s client architecture is already feature-based and split into business vs presentation components. This doc adds the missing “composition-first + React Query colocation” rule set so features stay portable, re-render surfaces stay small, and tests stay easy.

Important clarification: **“Fetch low” means “fetch in the business layer close to where data is consumed”**. It does **not** mean fetching inside presentation components.

## Layer Boundaries (in this repo’s terms)

| Layer | What it owns | What it must NOT own |
| --- | --- | --- |
| Provider layer | App coordination + infra wiring (QueryClient/tRPC, theme, toasts) | Server data fetching, pagination, DTO mapping, cache logic |
| Business layer | Feature orchestration + data access (queries/mutations) + form setup | UI primitives, styling-only concerns |
| Presentation layer | Rendering + layout + UI interactions via props/context | Fetching, mutations, navigation, global state access |

### Provider Layer (coordinate high)

Providers should coordinate app-wide client concerns, not act as backend aggregators.

Good examples:

- `TRPCProvider` + `QueryClientProvider` wiring
- Theme provider
- Toast provider
- URL-state adapter (nuqs)

Anti-pattern:

- A provider that fetches “bootstrap” server data and pushes it into context

## React Query Colocation (fetch low)

Keep server state in **TanStack Query** (tRPC hooks by default) and colocate queries in the smallest business component that needs the data.

Benefits:

- Smaller re-render scope (only the consuming subtree updates)
- Better feature portability (move a section without rewiring a “data parent”)
- Cleaner dependency flow (each section owns its data contract)

## Colocation Ladder

Use this as the default decision flow:

1) **Inline in a business component (default)**

- Use `trpc.<router>.<procedure>.useQuery()` / `useMutation()` inside the feature component that renders the section.

2) **Extract to `src/features/<feature>/hooks.ts` (when it buys you reuse or clarity)**

- If multiple business components need the same query/mutation wiring, expose a small stable feature API:

```ts
// src/features/profile/hooks.ts
export function useProfile() {
  return trpc.profile.getByCurrentUser.useQuery(undefined, {
    select: (dto) => normalizeProfile(dto),
  })
}
```

3) **Move shaping into `helpers.ts` + React Query `select` (derived data lives off-TSX)**

- Prefer pure transforms:

```ts
// src/features/profile/helpers.ts
export function normalizeProfile(dto: unknown) {
  // deterministic mapping here
}
```

4) **Promote to shared client code (rare)**

- If multiple features truly share a non-tRPC HTTP client, place it under `src/shared/lib/clients/<client>/` and expose React Query hooks there.

## Mapping to the Feature Module Layout

This maps the “coordinate high / fetch low / render dumb” model onto the documented file structure.

| Responsibility | Put it here |
| --- | --- |
| Screen-level orchestration (compose sections, own navigation) | `src/features/<feature>/components/<feature>-view.tsx` or `<feature>-form.tsx` |
| Section-level data (one query/mutation slice) | `src/features/<feature>/components/<feature>-*.tsx` (business) |
| Pure UI sections/fields/cards/lists | `src/features/<feature>/components/*-fields.tsx`, `*-card.tsx`, `*-list.tsx` |
| Reusable feature logic | `src/features/<feature>/hooks.ts` |
| Pure transforms (normalize/sort/group) | `src/features/<feature>/helpers.ts` |
| URL state | `src/features/<feature>/hooks.ts` (nuqs) |
| Client-only coordination state | `src/features/<feature>/stores/*` (Zustand) |

## Composition Recipes

### 1) Screen coordinator + leaf sections

Avoid a single “god component” that owns every query and every mutation on a screen. Instead:

- a coordinator composes sections and owns screen-level concerns
- each leaf business section fetches its own data and renders a dumb view

```tsx
// src/features/settings/components/settings-view.tsx
export function SettingsView() {
  return (
    <div className='grid gap-8'>
      <AccountSection />
      <BillingSection />
      <NotificationsSection />
    </div>
  )
}

function AccountSection() {
  const query = trpc.account.get.useQuery()
  if (query.isLoading) return <AccountSectionSkeleton />
  if (query.isError) return <ErrorDisplay error={query.error} />
  return <AccountSectionView value={query.data} />
}
```

### 2) Domain hook to avoid hook spaghetti

If a business component starts coordinating many hooks, introduce a single “domain hook” to make the orchestration explicit.

```ts
// src/features/chat/hooks.ts
export function useChatSessionModel(input: { sessionId: string }) {
  const messages = trpc.messages.list.useQuery({ sessionId: input.sessionId })
  const send = trpc.messages.send.useMutation()

  return { messages, send }
}
```

### 3) Slot-based presentation (render dumb, stay flexible)

Instead of boolean prop explosions, pass explicit slots (React nodes) into a view.

```tsx
export function SectionView(props: {
  title: string
  actions?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section className='grid gap-3'>
      <header className='flex items-center justify-between'>
        <h2 className='text-lg font-semibold'>{props.title}</h2>
        {props.actions}
      </header>
      {props.children}
    </section>
  )
}
```

## TanStack Query Notes (tRPC-first)

- Default: use `trpc.<router>.<procedure>.useQuery/useMutation` in feature components/hooks.
- Prefer `select` for UI shaping; move non-trivial transforms into `helpers.ts`.
- Use `enabled` for dependent queries.
- Invalidate after mutations using either:
  - `const utils = trpc.useUtils()` + `utils.<router>.<procedure>.invalidate()`
  - `queryClient.invalidateQueries(trpc.<router>.<procedure>.queryFilter(...))`

Advanced (deliberate opt-in): use `useTRPC()` + `queryOptions/mutationOptions/queryKey/queryFilter` when you need TanStack primitives (prefetching, custom `useMutation`, optimistic updates).

## Anti-patterns (don’t do these)

- Fetching in presentation components (`*-fields.tsx`, `*-card.tsx`, `*-list.tsx`).
- Mega providers that fetch and store server data.
- Lifting server data “too high” (fetching everything in a page and prop drilling into deep leaves).
- Duplicating server state in Zustand (store IDs + UI flags; derive server objects from queries).

## Testing & Fixtures

Two fast testing styles follow naturally:

- Unit test presentation components with fixtures: render `*-fields.tsx` / `*-card.tsx` with props (no providers, no QueryClient).
- Test business components by mocking feature hooks (`src/features/<feature>/hooks.ts`) rather than mocking network calls.

## Checklist

- Provider layer is infra/coordination only (no server data fetching).
- Queries/mutations live in business components/hooks, colocated to the consuming section.
- Presentation components render from props/context only.
- Non-trivial shaping lives in `helpers.ts` and is applied via `select`.
- Zustand stores hold coordination state (IDs, toggles), not fetched server objects.
