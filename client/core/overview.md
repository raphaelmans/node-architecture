# Client Core Overview (Agnostic)

This folder contains **framework-agnostic** client architecture docs.

If you need React/Next.js specifics, use:

- ReactJS: `client/frameworks/reactjs/README.md`
- Next.js: `client/frameworks/reactjs/metaframeworks/nextjs/README.md`

Core server-state keys are standardized with Query Key Factory (`@lukemorales/query-key-factory`).

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
