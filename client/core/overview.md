# Client Core Overview (Agnostic)

This folder contains **framework-agnostic** client architecture docs.

If you need React/Next.js specifics, use:

- ReactJS: [client/frameworks/reactjs/README.md](../frameworks/reactjs/README.md)
- Next.js: [client/frameworks/reactjs/metaframeworks/nextjs/README.md](../frameworks/reactjs/metaframeworks/nextjs/README.md)

## Key Decisions (Defaults)

These are the default conventions used throughout the client docs:

- Query keys are standardized with Query Key Factory; keys live in `src/common/query-keys/*`. See: `client/core/query-keys.md`.
- Error handling normalizes `unknown -> AppError`; UI branches only on `AppError.kind`. See: `client/core/error-handling.md`.
- Toast notifications are handled via a facade; feature code should not import a toast library directly. See: `client/frameworks/reactjs/error-handling.md`.
- Client logging uses `debug` via `src/common/logging/*` (dev-only by default, break-glass override available). See: `client/core/logging.md`.
- Domain transforms follow precedence: `src/lib/modules/<module>/shared/*` first, then `src/features/<feature>/*`. See: `client/core/domain-logic.md`.

## Core Index

| Document | Description |
| --- | --- |
| [Architecture](./architecture.md) | Core principles and boundaries |
| [Conventions](./conventions.md) | Layer responsibilities + file boundaries |
| [Client API Architecture](./client-api-architecture.md) | `clientApi -> featureApi -> query adapter` |
| [Zod Validation](./validation-zod.md) | Schema boundaries + normalization |
| [Domain Logic](./domain-logic.md) | Shared vs client-only transformations |
| [Server State](./server-state-tanstack-query.md) | TanStack Query core patterns |
| [Query Keys](./query-keys.md) | Query key conventions (Query Key Factory) |
| [State Management](./state-management.md) | Conceptual state decision guide |
| [Error Handling](./error-handling.md) | Error taxonomy + handling rules |
| [Logging](./logging.md) | Client logging conventions (`debug`) |
| [Folder Structure](./folder-structure.md) | Framework-agnostic directory conventions |
