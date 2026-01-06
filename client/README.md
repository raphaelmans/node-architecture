# Frontend Architecture Documentation

> Feature-based architecture for React frontends with Next.js, tRPC, TanStack Query, and TypeScript.

See [../README.md](../README.md) for the unified project folder structure and full documentation index.

## Overview

This documentation describes a **production-ready frontend architecture** that emphasizes:

- Feature-based organization
- Type-safe data fetching with tRPC
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
│   Feature Component     │     │      Feature Hook           │
│  (Business logic,       │     │  (URL state, custom logic)  │
│   data fetching)        │     │                             │
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
| API Layer     | tRPC                 |
| Server State  | TanStack Query       |
| Validation    | Zod                  |
| Forms         | react-hook-form      |
| URL State     | nuqs                 |
| Client State  | Zustand              |
| UI Components | shadcn/ui + Radix    |
| Styling       | Tailwind CSS         |

## Documentation Structure

### Core Documentation

| Document                                       | Description                                           |
| ---------------------------------------------- | ----------------------------------------------------- |
| [Overview](./core/overview.md)                 | Architecture summary, principles, quick reference     |
| [Conventions](./core/conventions.md)           | Layer responsibilities, decision flows, common module |
| [Data Fetching](./core/data-fetching.md)       | tRPC + TanStack Query patterns                        |
| [Forms](./core/forms.md)                       | Zod + react-hook-form + StandardForm                  |
| [State Management](./core/state-management.md) | URL state (nuqs), client state (Zustand)              |
| [UI Patterns](./core/ui-patterns.md)           | shadcn/ui, component separation                       |
| [Error Handling](./core/error-handling.md)     | Toast, form errors, error boundaries                  |
| [Environment](./core/environment.md)           | Type-safe environment variables (@t3-oss/env-nextjs)  |
| [Folder Structure](./core/folder-structure.md) | Directory architecture                                |

### References

The `references/` folder contains detailed implementation guides from an existing codebase.

## Quick Start

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
// Query
const { data, isLoading } = trpc.user.getById.useQuery({ id });

// Mutation with cache invalidation
const trpcUtils = trpc.useUtils();
await mutation.mutateAsync(data);
await trpcUtils.user.invalidate();
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
| **Type-safe data flow**         | Zod → tRPC → TanStack Query → Components               |
| **URL as state**                | Use nuqs for shareable UI state                        |
| **Standardized forms**          | StandardForm components for consistency                |

## Checklist for New Features

- [ ] Create `src/features/<feature>/` folder
- [ ] Define schemas in `schemas.ts`
- [ ] Create business component for data/forms
- [ ] Create presentation components for fields
- [ ] Add URL state hooks in `hooks.ts` if needed
- [ ] Add route to `app-routes.ts`
- [ ] Create page in `app/(authenticated)/<feature>/`
