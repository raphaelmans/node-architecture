# Composition (ReactJS)

> Coordinate high. Fetch low. Render dumb.

This repo's client architecture is feature-based and enforces a strict split between business logic and presentation.

Important clarification: **"Fetch low" means "fetch close to the UI that needs it" but always through feature hooks files**. We do not inline server-state hooks inside TSX components.

## Layer Boundaries (in this repo's terms)

| Layer | What it owns | What it must NOT own |
| --- | --- | --- |
| Provider layer | App coordination + specific infra ports (QueryClient, theme, toasts, analytics) | Server data fetching, provider construction, runtime service locator |
| Business layer | Feature orchestration + form setup + loading/error wiring | Query wiring, DTO definitions, pure business rules |
| Presentation layer | Rendering + layout + UI interactions via props/context | Fetching, mutations, navigation, global state |

### Provider Layer (coordinate high)

Providers coordinate app-wide client concerns, not backend data.

Good examples:

- `TRPCProvider` + `QueryClientProvider` wiring
- Theme provider
- Toast provider
- Analytics provider receiving a composition-root-created `ProductAnalytics`

Anti-pattern:

- A provider that fetches "bootstrap" server data and pushes it into context
- A provider that constructs vendor SDKs or exposes the complete runtime container

## File Separation Rules (team convention)

In `src/features/<feature>/`:

- `hooks.ts`: **all** server-state hooks for the feature (`useQuery*`, `useMut*`, and optional `useMod*` composition hooks)
- `types.ts`: shared feature TypeScript types (non-DTO); component prop types may stay local when truly component-only
- `schemas.ts`: client-only form/UI schemas composed from shared input contracts (schemas never live in TSX or `hooks.ts`)
- `domain.ts`: business rules (pure, deterministic)
- `helpers.ts`: DTO-to-feature-model mapping and small pure utilities

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
| Typed mutation/workflow analytics | Owning `useMut*` / `useMod*` hook after success |
| Transport/contract operational logs | `clientApi` / `featureApi` through `AppLogger` |

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

Do not add a controller or workflow hook solely to emit telemetry. Add orchestration only when the UX flow itself has multiple coordinated steps.

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
- Prefer invalidation inside mutation hooks for reusable behavior.
- Component-coordinator invalidation is allowed for route-local orchestration.
- See `./server-state-patterns-react.md` for decision rules and cookbook scenarios.

## Anti-patterns (don't do these)

- Fetching in presentation components (`*-fields.tsx`, `*-card.tsx`, `*-list.tsx`).
- Inlining transport/query library hooks directly inside TSX components.
- Mega providers that fetch and store server data.
- Duplicating server state in Zustand (store IDs + UI flags; derive server objects from queries).

## Testing & Fixtures

- Unit test presentation components with fixtures: render `*-fields.tsx` / `*-card.tsx` with props.
- Test business components by mocking feature hooks (`src/features/<feature>/hooks.ts`) rather than mocking network calls.
- Test query hooks by mocking `I<Feature>Api` contracts, not transport providers.
- Test mutation analytics with a `ProductAnalytics` spy; completion events emit only after success.
- Test `api.ts` class implementations by mocking injected deps (`clientApi`, `toAppError`, logger when used).
- Test `domain.ts` / `helpers.ts` as pure functions (no mocks).

## Checklist

- Provider layer is infra/coordination only (no server data fetching).
- Queries/mutations live in `src/features/<feature>/hooks.ts` only.
- Schemas/mapping live in `schemas.ts`; shared feature types live in `types.ts`.
- Business rules live in `domain.ts`; small utilities live in `helpers.ts`.
- Business components wire loading/error and call feature hooks.
- Presentation components render from props/context only.
- Provider/vendor construction happens in the client composition root.
- Providers expose specific ports, never the complete runtime container.
