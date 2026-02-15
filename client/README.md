# Frontend Architecture Documentation

> Feature-based client architecture with a framework-agnostic core and framework/metaframework-specific layers.

See [../README.md](../README.md) for the unified project folder structure and full documentation index.

## Overview

This documentation describes a **production-ready frontend architecture** that emphasizes:

- Feature-based organization
- A strict client API chain (`clientApi -> featureApi -> query adapter -> components`)
- Standardized form patterns
- Clear separation of business and presentation logic

```
┌─────────────────────────────────────────────────────────────┐
│                         Page (Route)                         │
│                    (Next.js App Router)                      │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│   Feature Component     │     │  Query Adapter Hook         │
│  (Business orchestration│     │  (useQuery/useMut/useMod,   │
│   + form wiring)        │     │   cache/invalidation)       │
└───────────┬─────────────┘     └─────────────────────────────┘
            │
            ▼
┌─────────────────────────┐
│ Presentation Component  │
│  (Form fields, cards)   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│     UI Primitives       │
│  (shadcn/ui, Radix)     │
└─────────────────────────┘
```

## Technology Stack

> **Note:** This documentation serves as an architectural reference. Always check `package.json` for actual package versions in your project.

| Concern       | Technology           |
| ------------- | -------------------- |
| Framework     | Next.js (App Router) |
| React         | React                |
| API Layer     | Adapter choice (tRPC / route handlers) |
| Server State  | TanStack Query       |
| Validation    | Zod                  |
| Forms         | react-hook-form      |
| URL State     | nuqs                 |
| Client State  | Zustand              |
| UI Components | shadcn/ui + Radix    |
| Styling       | Tailwind CSS         |

## Documentation Structure

### Core Documentation (Agnostic)

| Document | Description |
| --- | --- |
| [Onboarding](./core/onboarding.md) | New project + contributor startup checklist |
| [Core Index](./core/overview.md) | Core index + links |
| [Architecture](./core/architecture.md) | Core principles and boundaries |
| [Conventions](./core/conventions.md) | Layer responsibilities + file boundaries |
| [Client API Architecture](./core/client-api-architecture.md) | `clientApi -> featureApi -> query adapter` |
| [Zod Validation](./core/validation-zod.md) | Schema boundaries + normalization |
| [Domain Logic](./core/domain-logic.md) | Shared vs client-only transformations |
| [Server State](./core/server-state-tanstack-query.md) | TanStack Query core patterns |
| [Query Keys](./core/query-keys.md) | Query key conventions (Query Key Factory) |
| [State Management](./core/state-management.md) | Conceptual state decision guide |
| [Error Handling](./core/error-handling.md) | Error taxonomy + handling rules |
| [Logging](./core/logging.md) | Client logging conventions (`debug`) |
| [Folder Structure](./core/folder-structure.md) | Framework-agnostic directory conventions |

### Framework Documentation

| Document | Description |
| --- | --- |
| [Frameworks Index](./frameworks/README.md) | Framework-specific docs |
| [ReactJS Index](./frameworks/reactjs/README.md) | React-specific implementation |
| [Next.js Index](./frameworks/reactjs/metaframeworks/nextjs/README.md) | Next.js App Router + SSR/params + adapters |

### Drafts

The `drafts/` folder contains detailed implementation guides from an existing codebase.
These documents are **non-canonical** and may be outdated.

Start here: [Drafts Overview](./drafts/overview.md)

### Diagrams

ASCII diagrams for structure, data flow, and state management live in:

- [client/diagrams.md](./diagrams.md)

## Quick Start

Start with: [client/core/onboarding.md](./core/onboarding.md)

### Component Decision Flow

```
Does it fetch data or own form state?
├── Yes → Feature Component (business)
└── No → Presentation Component
    └── Does it consume form context?
        ├── Yes → useFormContext + StandardForm fields
        └── No → Props-based component
```

### Data Fetching

```typescript
// Preferred: follow the client API chain.
// components -> query adapter -> featureApi -> clientApi -> network
```

### Forms

```typescript
<StandardFormProvider form={form} onSubmit={onSubmit}>
  <StandardFormError />
  <StandardFormInput<FormType> name='email' label='Email' required />
  <Button type='submit'>Save</Button>
</StandardFormProvider>
```

### URL State

```typescript
const [tab, setTab] = useQueryState(
  "tab",
  parseAsStringLiteral(["overview", "settings"]).withDefault("overview"),
);
```

## Folder Structure

See [../README.md](../README.md) for the unified project folder structure that aligns client and server code.

For detailed frontend-specific folder conventions, see [./core/folder-structure.md](./core/folder-structure.md).

## Core Principles

| Principle                       | Description                                            |
| ------------------------------- | ------------------------------------------------------ |
| **Feature-based**               | Co-locate components, hooks, schemas by feature        |
| **Business/Presentation split** | Data in business components, rendering in presentation |
| **Type-safe data flow**         | Zod + typed APIs + TanStack Query → Components         |
| **URL as state**                | Use a metaframework URL-state adapter (Next.js: nuqs)  |
| **Standardized forms**          | StandardForm components for consistency                |

## Checklist for New Features

- [ ] Create `src/features/<feature>/` folder
- [ ] Define `api.ts` with `I<Feature>Api` + `class <Feature>Api` + `create<Feature>Api`
- [ ] Define schemas in `schemas.ts`
- [ ] Create business component for data/forms
- [ ] Create presentation components for fields
- [ ] Add URL state hooks in `hooks.ts` if needed
- [ ] Add tests: `api.test.ts` (mock deps), `domain/helpers` pure tests
- [ ] Add route to `app-routes.ts`
- [ ] Create page in the appropriate route group under `app/` (project-defined, e.g. `app/(protected)/<feature>/`)
