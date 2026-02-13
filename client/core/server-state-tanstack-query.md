# Server State (TanStack Query)

TanStack Query is treated as **core infrastructure** for server/IO state.

## Core Rules

- Share async/IO data via the query cache, not via “big data providers”.
- Keep cache rules (query keys, invalidation, optimistic updates) in one dedicated layer.
- Components do not inline cache logic.

## Patterns

- Query key conventions must be stable and feature-scoped.
- Use dependent queries via `enabled`.
- Keep DTO mapping/normalization out of components.

React implementation guidance lives under `client/frameworks/reactjs/`.

