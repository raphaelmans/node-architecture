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
- Do not duplicate server state into client stores; store IDs/flags and derive server objects from query data.

### B) Client Coordination State

Use a store/provider when state is:

- client-derived (not from IO)
- shared across distant components
- interaction-heavy (toggles, modes, selections)

Store placement: co-locate stores inside the feature that owns them at `src/features/<feature>/stores/`. Promote to `src/common/` only when shared across multiple features.

### D) Complex Interaction State (State Machines)

Use XState state machines (`src/features/<feature>/machines/`) when:

- the interaction has multiple discrete states with defined transitions
- guards and actions need explicit modeling (e.g., booking cart, time slot selection)
- the state logic is complex enough that ad-hoc `useState` + conditionals become unreadable

Test machine guards and actions separately from the machine definition itself.

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
- XState: framework-agnostic state machine library (no dedicated guide yet — follow XState v5 docs)
