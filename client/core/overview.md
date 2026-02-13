# Client Core Overview (Agnostic)

This folder contains **framework-agnostic** client architecture docs.

If you need React/Next.js specifics, use:

- ReactJS: `client/frameworks/reactjs/README.md`
- Next.js: `client/frameworks/reactjs/metaframeworks/nextjs/README.md`

## Core Index

| Document | Description |
| --- | --- |
| [Architecture](./architecture.md) | Core principles and boundaries |
| [Conventions](./conventions.md) | Layer responsibilities + file boundaries |
| [Client API Architecture](./client-api-architecture.md) | `clientApi -> featureApi -> query adapter` |
| [Zod Validation](./validation-zod.md) | Schema boundaries + normalization |
| [Server State](./server-state-tanstack-query.md) | TanStack Query core patterns |
| [State Management](./state-management.md) | Conceptual state decision guide |
| [Error Handling](./error-handling.md) | Error taxonomy + handling rules |
| [Folder Structure](./folder-structure.md) | Framework-agnostic directory conventions |

