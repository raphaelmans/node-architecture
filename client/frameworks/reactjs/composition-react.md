# Composition (ReactJS)

> Coordinate high. Fetch low. Render dumb.

This repo's client architecture is feature-based and enforces a strict split between business logic and presentation.

Important clarification: **"Fetch low" means "fetch close to the UI that needs it" but always through feature hooks files**. We do not inline server-state hooks inside TSX components.

## Layer Boundaries (in this repo's terms)

| Layer | What it owns | What it must NOT own |
| --- | --- | --- |
| Provider layer | App coordination + infra wiring (QueryClient, theme, toasts) | Server data fetching, pagination, DTO mapping, cache logic |
| Business layer | Feature orchestration + form setup + loading/error wiring | Query wiring, DTO definitions, pure business rules |
| Presentation layer | Rendering + layout + UI interactions via props/context | Fetching, mutations, navigation, global state |

### Provider Layer (coordinate high)

Providers coordinate app-wide client concerns, not backend data.

Good examples:

- `TRPCProvider` + `QueryClientProvider` wiring
- Theme provider
- Toast provider

Anti-pattern:

- A provider that fetches "bootstrap" server data and pushes it into context

## File Separation Rules (team convention)

In `src/features/<feature>/`:

- `hooks.ts`: **all** TanStack Query / tRPC `useQuery` + `useMutation` hooks for the feature
- `types.ts`: shared feature TypeScript types (non-DTO); component prop types may stay local when truly component-only
- `schemas.ts`: Zod schemas + derived types + DTO-to-feature mapping helpers (schemas never live in TSX or `hooks.ts`)
- `domain.ts`: business rules (pure, deterministic)
- `helpers.ts`: small pure utilities (formatting, grouping, small transforms)

Colocation exception:

- Component-specific `useEffect` (DOM wiring, focus, local UI behavior) may stay in the component that owns it.

## Fetch Low (without colocation)

"Fetch low" means:

- keep providers orchestration-only
- keep queries/mutations in `src/features/<feature>/hooks.ts`
- keep business components small and section-scoped by calling feature hooks
- keep presentation dumb

## Mapping to the Feature Module Layout

| Responsibility | Put it here |
| --- | --- |
| Screen-level orchestration (compose sections, own navigation) | `src/features/<feature>/components/<feature>-view.tsx` or `<feature>-form.tsx` |
| Section business component (loading/error wiring) | `src/features/<feature>/components/<feature>-*.tsx` |
| Server state hooks (queries/mutations) | `src/features/<feature>/hooks.ts` |
| Schemas + mapping | `src/features/<feature>/schemas.ts` |
| Feature types (non-DTO) | `src/features/<feature>/types.ts` |
| Business rules | `src/features/<feature>/domain.ts` |
| Small pure utilities | `src/features/<feature>/helpers.ts` |
| Pure UI sections/fields/cards/lists | `src/features/<feature>/components/*-fields.tsx`, `*-card.tsx`, `*-list.tsx` |
| Client-only coordination state | `src/features/<feature>/stores/*` (Zustand) |

## Composition Recipes

### 1) Screen coordinator + leaf sections

Avoid a single "god component" that owns every concern. Instead:

- a coordinator composes sections and owns screen-level concerns
- each leaf section is a business component that calls feature hooks

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
```

```tsx
// src/features/settings/components/account-section.tsx
import { useQuerySettingsAccount } from '../hooks'

export function AccountSection() {
  const query = useQuerySettingsAccount()
  if (query.isLoading) return <AccountSectionSkeleton />
  if (query.isError) return <ErrorDisplay error={query.error} />
  return <AccountSectionView value={query.data} />
}
```

### 2) Domain hook to avoid hook spaghetti

If a business component starts coordinating many hooks, introduce a domain-level hook in `src/features/<feature>/hooks.ts`.

```ts
// src/features/chat/hooks.ts
export function useModChatSession(input: { sessionId: string }) {
  const messages = useQueryChatMessagesBySessionId(input.sessionId)
  const send = useMutChatSendMessage(input.sessionId)
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

## TanStack Query Notes

- Implement queries/mutations in `src/features/<feature>/hooks.ts`.
- Prefer `select` for UI shaping; call pure functions from `domain.ts` / `helpers.ts`.
- Use `enabled` for dependent queries.
- Prefer invalidation inside mutation hooks (so components don't duplicate cache logic).

## Anti-patterns (don't do these)

- Fetching in presentation components (`*-fields.tsx`, `*-card.tsx`, `*-list.tsx`).
- Inlining `useQuery()` / `useMutation()` inside TSX components.
- Mega providers that fetch and store server data.
- Duplicating server state in Zustand (store IDs + UI flags; derive server objects from queries).

## Testing & Fixtures

- Unit test presentation components with fixtures: render `*-fields.tsx` / `*-card.tsx` with props.
- Test business components by mocking feature hooks (`src/features/<feature>/hooks.ts`) rather than mocking network calls.
- Test `domain.ts` / `helpers.ts` as normal pure functions.

## Checklist

- Provider layer is infra/coordination only (no server data fetching).
- Queries/mutations live in `src/features/<feature>/hooks.ts` only.
- Schemas/mapping live in `schemas.ts`; shared feature types live in `types.ts`.
- Business rules live in `domain.ts`; small utilities live in `helpers.ts`.
- Business components wire loading/error and call feature hooks.
- Presentation components render from props/context only.
