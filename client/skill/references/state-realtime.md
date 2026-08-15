# State and Realtime Slice

Use this slice for choosing state ownership, Zustand, URL state, state machines, TanStack Query cache synchronization, and provider-neutral realtime subscriptions.

## Contents

- [State decision](#state-decision)
- [Client coordination state](#client-coordination-state)
- [URL state](#url-state)
- [Realtime boundaries](#realtime-boundaries)
- [Cache and reconnection](#cache-and-reconnection)
- [Review checklist](#review-checklist)

## State Decision

Choose the narrowest correct owner:

1. Async or IO-backed data: TanStack Query.
2. Form input and validation: the framework form abstraction.
3. Shareable, bookmarkable, back-button-relevant state: URL state.
4. Explicit states, guarded transitions, or complex workflows: a state machine.
5. Cross-component client-only coordination: a feature-owned store/provider.
6. Local and disposable presentation state: component-local state.

Never duplicate server entities into Zustand as an alternative source of truth. Store IDs, selections, and UI flags, then derive server objects from query data.

## Client Coordination State

Keep stores under `src/features/<feature>/stores/` unless they are genuinely cross-feature. Use an application-scoped Zustand store for app-wide coordination and a context-backed vanilla store when each mounted subtree needs an isolated instance.

- Select primitives or narrow projections rather than the whole store.
- Use shallow comparison for multi-value projections when appropriate.
- Persist only an explicit allowlist with `partialize`.
- Do not render browser-storage state as authoritative before hydration in SSR applications.

Use a state machine when transitions, guards, and actions are the domain of the interaction rather than accumulating conditional `useState` branches.

## URL State

In Next.js, use typed nuqs parsers for user-visible filters, search, pagination, tabs, and modal state.

- Use `history: "replace"` for filters, search, and pagination.
- Use `history: "push"` for tabs or modals where back navigation matters.
- Centralize parameter names.
- Reset page state when result-changing filters change.
- Debounce free-text search before using it in a query key; do not debounce selects or toggles.
- Include every result-changing URL value in the query key.

## Realtime Boundaries

```text
provider transport
  -> feature realtime API
    -> framework lifecycle adapter
      -> cache strategy
```

- The transport owns provider channels, filters, status mapping, retry/backoff, and outer payload validation.
- The feature realtime API validates capability payloads and maps provider rows into domain events.
- The lifecycle adapter owns subscribe/unsubscribe and reconnect-gap bookkeeping.
- The cache strategy applies a safe immutable patch or invalidates the smallest known scope.

Provider SDK types, database rows, channel objects, and SDK errors must not escape into feature hooks or components.

## Cache and Reconnection

When an event carries enough state:

1. apply a pure immutable cache patch for immediate feedback;
2. invalidate the affected scope to reconcile with server truth.

When it only signals change, invalidate without fabricating a partial entity. Coalesce invalidation for bursty streams.

Reconnect policy:

- Initial connection does not imply a gap.
- After a connected subscription disconnects or errors, mark the scope potentially stale.
- On the next successful connection, invalidate affected scopes once.
- If ordering matters, carry a monotonic sequence/version and ignore stale events.

In React, subscribe inside an effect, return idempotent teardown, resolve a stable composition-root-owned realtime API, and keep non-rendering connection bookkeeping in refs. Test with a fake feature realtime API and a fresh QueryClient.

For Supabase, keep publication, replica identity, grants, and RLS in reviewed server/database migrations. Client setup code must not apply production SQL.

## Review Checklist

- Each piece of state has one authoritative owner.
- Server data is not duplicated into client stores.
- URL-visible state remains shareable and has intentional history behavior.
- Provider payloads are validated and mapped before feature use.
- Cache patches are pure, safe, and followed by reconciliation.
- Reconnection recovers missed events without invalidating on the initial connection.
- Unsubscribe is idempotent and always called during teardown.
- Realtime failures have one operational owner and do not become product analytics.

## Derivation Sources

Derived from the source repository's state-management, server-state, realtime, query-keys, React Zustand, React realtime, Next.js nuqs, and Supabase realtime documents. These paths are provenance only in an installed skill.
