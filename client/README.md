# Frontend Architecture Documentation

> Canonical frontend architecture for feature-based React/Next.js applications with a framework-agnostic core and framework-specific layers.

See [../README.md](../README.md) for the source-repo overview and [../legacy/README.md](../legacy/README.md) for historical references.

## Focus

This documentation emphasizes:

- Feature-based organization
- A strict client API chain: `clientApi -> featureApi -> query adapter -> components`
- Clear separation of business and presentation logic
- Typed validation and normalized error handling

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

## Canonical Navigation

### Core

| Document | Description |
| -------- | ----------- |
| [Core Index](./core/README.md) | Core contracts and reading order |
| [Onboarding](./core/onboarding.md) | New project + contributor startup checklist |
| [Architecture](./core/architecture.md) | Core principles and boundaries |
| [Conventions](./core/conventions.md) | Layer responsibilities + file boundaries |
| [Client API Architecture](./core/client-api-architecture.md) | `clientApi -> featureApi -> query adapter` |
| [Zod Validation](./core/validation-zod.md) | Schema boundaries + normalization |
| [Domain Logic](./core/domain-logic.md) | Shared vs client-only transformations |
| [Server State](./core/server-state-tanstack-query.md) | TanStack Query core patterns |
| [Query Keys](./core/query-keys.md) | Query key conventions |
| [State Management](./core/state-management.md) | State decision guide |
| [Error Handling](./core/error-handling.md) | Error taxonomy + handling rules |
| [Logging](./core/logging.md) | Client logging conventions |
| [Testing](./core/testing.md) | Unit testing standard |
| [Testing — Vitest Runner](./core/testing-vitest.md) | Runner configuration and setup |
| [Realtime Subscriptions](./core/realtime.md) | Realtime cache patching and reconnection |
| [Folder Structure](./core/folder-structure.md) | Framework-agnostic directory conventions |

### Frameworks

| Document | Description |
| -------- | ----------- |
| [Frameworks Index](./frameworks/README.md) | Framework-specific docs |
| [ReactJS Index](./frameworks/reactjs/README.md) | React-specific implementation |
| [Next.js Index](./frameworks/reactjs/metaframeworks/nextjs/README.md) | Next.js App Router + SSR/params + adapters |

### Supplemental

- [client/diagrams.md](./diagrams.md) for ASCII diagrams
- [Legacy Client Overview](../legacy/client/overview.md) for non-canonical historical references

## Quick Start

1. Start with [./core/onboarding.md](./core/onboarding.md).
2. Read [./core/README.md](./core/README.md) and [./core/conventions.md](./core/conventions.md).
3. Add framework details from [./frameworks/reactjs/README.md](./frameworks/reactjs/README.md) and [./frameworks/reactjs/metaframeworks/nextjs/README.md](./frameworks/reactjs/metaframeworks/nextjs/README.md) only when they apply.
4. Use [../legacy/client/overview.md](../legacy/client/overview.md) only for historical examples.

## Core Principles

| Principle | Description |
| --------- | ----------- |
| Feature-based | Co-locate components, hooks, schemas by feature |
| Business/presentation split | Business components own data/forms; presentation components render |
| Type-safe data flow | Zod + typed APIs + TanStack Query to components |
| URL as state | Prefer URL-state adapters where route state matters |
| Standardized forms | Shared form primitives for consistency |

## Feature Checklist

- [ ] Create `src/features/<feature>/`
- [ ] Define `api.ts` with `I<Feature>Api`, `<Feature>Api`, and `create<Feature>Api`
- [ ] Define schemas in `schemas.ts`
- [ ] Keep transport and cache ownership out of presentation components
- [ ] Add tests in `src/__tests__/features/<feature>/`
- [ ] Add route registration in the project-defined route registry
