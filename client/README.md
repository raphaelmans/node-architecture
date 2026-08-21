# Frontend Architecture Documentation

> Canonical frontend architecture for feature-based React/Next.js applications with a framework-agnostic core and framework-specific layers.

Client roles apply in both canonical repository topologies. Single-project examples use `src/*`; monorepo placement follows the shared [monorepo architecture](../monorepo/core/architecture.md) without changing client dependency direction.

See [../README.md](../README.md) for the source-repo overview and [../legacy/README.md](../legacy/README.md) for historical references.

Interactive companion: [Client Architecture Field Guide](../assets/client-architecture-guide.html).

Installable agent interface: [Client Architecture Skill](./skill/SKILL.md).

The documents under `core/` and `frameworks/` remain the authoring source of truth. The `$client` skill packages curated, composable derivatives of that guidance for progressive agent loading.

## Focus

This documentation emphasizes:

- Feature-based organization
- A strict client dependency stack: `components -> query adapter -> featureApi -> clientApi` for calls, with typed results returning in the opposite direction
- Clear separation of business and presentation logic
- One shared Zod wire contract across client and server
- Typed validation and normalized error handling
- Structured operational logging plus separate typed product analytics

## Technology Stack

| Concern | Technology |
| ------- | ---------- |
| Framework | Next.js (App Router) |
| React | React |
| API Layer | tRPC or route-handler HTTP adapters |
| Server State | TanStack Query |
| Validation | Zod |
| Forms | react-hook-form |
| URL State | nuqs |
| Client State | Zustand |
| UI | shadcn/ui + Radix |
| Styling | Tailwind CSS |
| Testing | Vitest |
| Local client logging | `debug` behind `AppLogger` |
| Production diagnostics | Optional Sentry adapter |

## Canonical Navigation

### Agent Skill

| Document | Description |
| -------- | ----------- |
| [Client Skill Router](./skill/SKILL.md) | Routes `$client` tasks through the smallest relevant architecture slices |
| [Scaffolding Slice](./skill/references/scaffolding.md) | Runs portable `$client scaffold` preflight and derives listed or unlisted stack integration from current evidence |
| [Workspace Slice](./skill/references/workspace.md) | Maps client roles across equal canonical single-project and monorepo topologies |
| [Skill References](./skill/references/) | Portable concern-based derivatives of the canonical client docs |

### Core

| Document | Description |
| -------- | ----------- |
| [Core Index](./core/README.md) | Core contracts and reading order |
| [Onboarding](./core/onboarding.md) | New project + contributor startup checklist |
| [Scaffolding Contract](./core/scaffolding.md) | Framework-agnostic safety, evidence, atomicity, and boundary contract |
| [Architecture](./core/architecture.md) | Core principles and boundaries |
| [Conventions](./core/conventions.md) | Layer responsibilities + file boundaries |
| [Composition Root](./core/composition-root.md) | Factories, dependency injection, runtime lifetimes |
| [Client API Architecture](./core/client-api-architecture.md) | `components -> query adapter -> featureApi -> clientApi` call flow |
| [Zod Validation](./core/validation-zod.md) | Schema boundaries + normalization |
| [Domain Logic](./core/domain-logic.md) | Shared vs client-only transformations |
| [Server State](./core/server-state-tanstack-query.md) | TanStack Query core patterns |
| [Query Keys](./core/query-keys.md) | Query key conventions |
| [State Management](./core/state-management.md) | State decision guide |
| [Error Handling](./core/error-handling.md) | Error taxonomy + handling rules |
| [Operational Logging](./core/logging.md) | Structured records, local `debug`, optional Sentry |
| [Product Analytics](./core/product-analytics.md) | Typed behavioral events and vendor adapters |
| [Testing](./core/testing.md) | Unit testing standard |
| [Testing — Vitest Runner](./core/testing-vitest.md) | Runner configuration and setup |
| [Realtime Subscriptions](./core/realtime.md) | Realtime cache patching and reconnection |
| [Folder Structure](./core/folder-structure.md) | Framework-agnostic directory conventions |

### Frameworks

| Document | Description |
| -------- | ----------- |
| [Frameworks Index](./frameworks/README.md) | Framework-specific docs |
| [ReactJS Index](./frameworks/reactjs/README.md) | React-specific implementation |
| [React Scaffolding](./frameworks/reactjs/scaffolding.md) | React implementation of the portable scaffolding contract |
| [Next.js Index](./frameworks/reactjs/metaframeworks/nextjs/README.md) | Next.js App Router + SSR/params + adapters |
| [Next.js Scaffolding](./frameworks/reactjs/metaframeworks/nextjs/scaffolding.md) | Next.js specialization for repository-aware generation |

### Supplemental

- [Client Architecture Field Guide](../assets/client-architecture-guide.html) for the standalone interactive system, flow, state, telemetry, runtime, testing, and structure guide
- [client/diagrams.md](./diagrams.md) for ASCII diagrams
- [Legacy Client Overview](../legacy/client/overview.md) for non-canonical historical references

## Quick Start

1. Start with [./core/onboarding.md](./core/onboarding.md).
2. Read [./core/README.md](./core/README.md) and [./core/conventions.md](./core/conventions.md).
3. Add a documented framework specialization when available; otherwise derive it from repository evidence and current official resources.
4. When the client lives in a workspace, resolve its app/package boundaries through [Monorepo Package Boundaries](../monorepo/core/package-boundaries.md).
5. Use [../legacy/client/overview.md](../legacy/client/overview.md) only for historical examples.

## Core Principles

| Principle | Description |
| --------- | ----------- |
| Feature-based | Co-locate components, hooks, schemas by feature |
| Business/presentation split | Business components own data/forms; presentation components render |
| Type-safe data flow | Shared Zod contracts + typed APIs + TanStack Query to components |
| URL as state | Prefer URL-state adapters where route state matters |
| Standardized forms | Shared form primitives for consistency |
| Separate telemetry ports | `AppLogger` for diagnostics; `ProductAnalytics` for behavior |
| Explicit infrastructure lifecycle | Factories assembled once in a client composition root |

## Feature Checklist

- [ ] Create the feature in the selected client application's feature boundary (`src/features/<feature>/` in the single-project mapping)
- [ ] Define public input/response schemas once in the resolved shared-contract boundary (`src/lib/modules/<module>/shared/contracts/` in one project or a contract package when cross-package)
- [ ] Define `api.ts` with `I<Feature>Api`, `<Feature>Api`, and `create<Feature>Api`
- [ ] Define client-only form/UI schemas in `schemas.ts` by composing shared inputs
- [ ] Keep transport and cache ownership out of presentation components
- [ ] Add tests in `src/__tests__/features/<feature>/`
- [ ] Add route registration in the project-defined route registry
