# Client Core README (Agnostic)

This folder is the canonical client base.
Framework docs must implement these contracts, not replace them.

## Start Here (New Project)

Use this order for a new project or contributor onboarding:

1. `client/core/onboarding.md`
2. `client/core/scaffolding.md` when bootstrapping infrastructure or a feature
3. `client/core/architecture.md`
4. `client/core/conventions.md`
5. `client/core/folder-structure.md`
6. `client/core/composition-root.md`
7. `client/core/client-api-architecture.md`
8. `client/core/validation-zod.md`
9. `client/core/domain-logic.md`
10. `client/core/query-keys.md`
11. `client/core/server-state-tanstack-query.md`
12. `client/core/state-management.md`
13. `client/core/error-handling.md`
14. `client/core/logging.md`
15. `client/core/product-analytics.md`
16. `client/core/realtime.md`
17. `client/core/testing.md`
18. `client/core/testing-vitest.md`

Then read framework details:

- ReactJS: [client/frameworks/reactjs/README.md](../frameworks/reactjs/README.md)
- Next.js: [client/frameworks/reactjs/metaframeworks/nextjs/README.md](../frameworks/reactjs/metaframeworks/nextjs/README.md)

## Key Decisions (Defaults)

- Query keys follow an explicit split: direct tRPC hooks use generated `@trpc/react-query` keys/utils, `IFeatureApi` wrappers may use `buildTrpcQueryKey` for interop, and non-tRPC adapters use plain key objects in `src/common/query-keys/*`.
- Transport/provider failures normalize from `unknown` to `AppError`; known response-decoding failures become `kind: "contract"`, while `kind: "validation"` remains user-correctable input.
- Toast usage is facade-first; feature code should not import toast providers directly.
- Operational logging uses an OpenTelemetry-shaped `AppLogger`; `debug` is the local browser sink and Sentry is an optional filtered remote sink.
- Product analytics uses a separate typed `ProductAnalytics` port with consent-aware vendor adapters.
- Feature APIs use `I<Feature>Api` + `class <Feature>Api` + `create<Feature>Api` for testable boundaries.
- A client composition root owns `createAppLogger`, `createProductAnalytics`, `createClientApi`, and feature API factories plus their runtime lifetimes.
- Public request/response contracts have one Zod source in the resolved shared-contract boundary: `src/lib/modules/<module>/shared/contracts/` in the single-project topology or an activated contract package in the monorepo topology.
- Client form schemas compose shared input contracts; client feature models remain separate from wire DTOs and ORM entities.
- Domain transforms use ownership precedence: the module's isomorphic shared boundary first, then the client feature. In a monorepo, extract an optional domain package only for genuine cross-runtime/package reuse.

## Common Mistakes

- Putting HTTP or tRPC calls directly in presentation components.
- Mixing cache invalidation logic into route/presentation layers.
- Creating feature state stores for server data that should stay in query cache.
- Copying server request/response types into a client feature instead of importing the shared contract.
- Importing ORM entities or server-only `dtos/` into browser code.
- Importing `debug`, Sentry, or an analytics vendor directly inside feature code.
- Routing product analytics through operational logs or reporting the same error at multiple layers.
- Creating hidden singletons inside feature modules or injecting the complete runtime container.
- Copying patterns from `legacy/client/*` as if canonical.

Rule:

- New and modified files follow core contracts.
- Legacy files can migrate incrementally.

## Core Index

| Document | Description |
| --- | --- |
| [Onboarding](./onboarding.md) | New project + contributor startup checklist |
| [Scaffolding Contract](./scaffolding.md) | Framework-agnostic safety, evidence, atomicity, and boundary policy |
| [Architecture](./architecture.md) | Core principles and boundaries |
| [Conventions](./conventions.md) | Layer ownership + decision flows |
| [Folder Structure](./folder-structure.md) | Directory and feature starter contracts |
| [Composition Root](./composition-root.md) | Infrastructure factories, DI, browser/SSR lifetimes |
| [Configuration Boundaries](./configuration.md) | Browser build/runtime surfaces, schema authority, and narrow injection |
| [Client API Architecture](./client-api-architecture.md) | `components -> query adapter -> featureApi -> clientApi` call flow |
| [Zod Validation](./validation-zod.md) | Schema boundaries + normalization |
| [Domain Logic](./domain-logic.md) | Shared vs client-only transformations |
| [Server State](./server-state-tanstack-query.md) | TanStack Query playbook |
| [Query Keys](./query-keys.md) | Query key conventions (tRPC + non-tRPC) |
| [State Management](./state-management.md) | Conceptual state decision guide |
| [Permission-Aware UX](./access-control.md) | Safe scoped access state and server-authoritative decisions |
| [Error Handling](./error-handling.md) | Error taxonomy + handling rules |
| [Operational Logging](./logging.md) | Structured records, `debug` scoping, correlation, optional Sentry |
| [Product Analytics](./product-analytics.md) | Typed product events, consent, identity, vendor adapters |
| [Testing](./testing.md) | Unit testing standard: `__tests__` layout, AAA, test doubles |
| [Testing — Vitest Runner](./testing-vitest.md) | Vitest runner configuration, scripts, setup file |
| [Realtime Subscriptions](./realtime.md) | Client-side realtime event subscriptions, cache patching, reconnection |
