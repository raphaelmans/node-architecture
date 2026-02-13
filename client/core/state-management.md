# State Management (Agnostic)

> Conceptual decision guide for state. Library specifics live under `client/frameworks/...`.

## State Types

### A) Server/IO State (default)

Use a server-state cache (TanStack Query in this architecture) for async/IO data:

- loading/pending
- success (data)
- error
- stale/refreshing

Rule:

- Share server/IO state via the query cache and stable query keys, not via “big data providers”.

### B) Client Coordination State

Use a store/provider when state is:

- client-derived (not from IO)
- shared across distant components
- interaction-heavy (toggles, modes, selections)

### C) Local Ephemeral UI State

Use component-local state when:

- only one component needs it
- it can reset on unmount
- it is purely presentational

## Decision Cheatsheet (PR Review)

1. Is it async/IO data? Use server-state cache.
2. Is it shared coordination state? Use a store/provider.
3. Is it local and ephemeral? Use component-local state.

## Library-Specific Docs

- Server state: `client/core/server-state-tanstack-query.md`
- React client state (Zustand): `client/frameworks/reactjs/state-zustand.md`
- Next.js URL state (nuqs): `client/frameworks/reactjs/metaframeworks/nextjs/url-state-nuqs.md`
- React forms: `client/frameworks/reactjs/forms-react-hook-form.md`

