# Client Core Overview (Agnostic)

This folder is the canonical client base.
Framework docs must implement these contracts, not replace them.

## Start Here (New Project)

Use this order for a new project or contributor onboarding:

1. `client/core/onboarding.md`
2. `client/core/architecture.md`
3. `client/core/conventions.md`
4. `client/core/folder-structure.md`
5. `client/core/client-api-architecture.md`
6. `client/core/server-state-tanstack-query.md`
7. `client/core/error-handling.md`
8. `client/core/logging.md`
9. `client/core/testing.md`

Then read framework details:

- ReactJS: [client/frameworks/reactjs/README.md](../frameworks/reactjs/README.md)
- Next.js: [client/frameworks/reactjs/metaframeworks/nextjs/README.md](../frameworks/reactjs/metaframeworks/nextjs/README.md)

## Key Decisions (Defaults)

- Query keys use Query Key Factory for non-tRPC adapters in `src/common/query-keys/*`; tRPC uses generated `@trpc/react-query` keys/utils.
- Errors normalize from `unknown` to `AppError`; UI branches on `AppError.kind`, not transport-specific shapes.
- Toast usage is facade-first; feature code should not import toast providers directly.
- Client logging uses `debug` through `src/common/logging/*` (dev default with break-glass override).
- Feature APIs use `I<Feature>Api` + `class <Feature>Api` + `create<Feature>Api` for testable boundaries.
- Domain transforms use precedence: `src/lib/modules/<module>/shared/*` first, then `src/features/<feature>/*`.

## Common Mistakes

- Putting HTTP or tRPC calls directly in presentation components.
- Mixing cache invalidation logic into route/presentation layers.
- Creating feature state stores for server data that should stay in query cache.
- Copying patterns from `client/drafts/*` as if canonical.

Rule:

- New and modified files follow core contracts.
- Legacy files can migrate incrementally.

## Core Index

| Document | Description |
| --- | --- |
| [Onboarding](./onboarding.md) | New project + contributor startup checklist |
| [Architecture](./architecture.md) | Core principles and boundaries |
| [Conventions](./conventions.md) | Layer ownership + decision flows |
| [Folder Structure](./folder-structure.md) | Directory and feature starter contracts |
| [Client API Architecture](./client-api-architecture.md) | `clientApi -> featureApi -> query adapter` |
| [Zod Validation](./validation-zod.md) | Schema boundaries + normalization |
| [Domain Logic](./domain-logic.md) | Shared vs client-only transformations |
| [Server State](./server-state-tanstack-query.md) | TanStack Query playbook |
| [Query Keys](./query-keys.md) | Query key conventions (Query Key Factory) |
| [State Management](./state-management.md) | Conceptual state decision guide |
| [Error Handling](./error-handling.md) | Error taxonomy + handling rules |
| [Logging](./logging.md) | Client logging conventions (`debug`) |
| [Testing](./testing.md) | Unit testing standard: `__tests__` layout, AAA, test doubles |
