# Frontend Architecture Overview

> High-level overview of the frontend architecture, linking to detailed documentation for each concern.

## Architecture Summary

This frontend follows a **feature-based architecture** with clear separation between business logic and presentation, type-safe data fetching, and standardized UI patterns.

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
│  (Form fields, cards,   │
│   lists - no fetching)  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│     UI Primitives       │
│  (shadcn/ui, Radix)     │
└─────────────────────────┘
```

## Core Principles

| Principle                          | Description                                                     |
| ---------------------------------- | --------------------------------------------------------------- |
| **Feature-based organization**     | Co-locate components, hooks, schemas by feature                 |
| **Business/Presentation split**    | Data fetching in business components, rendering in presentation |
| **Type-safe data flow**            | Zod schemas → tRPC → TanStack Query → Components                |
| **URL as state**                   | Use nuqs for shareable, bookmarkable UI state                   |
| **Standardized forms**             | StandardForm components reduce boilerplate                      |
| **Composition over configuration** | Compose small components, use children for flexibility          |

## Technology Stack

> **Note:** Version numbers below are reference points from when this documentation was created. Always check `package.json` for actual versions in your project.

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

## Server Code Location

All server-side code lives under `src/lib/`. When importing DTOs or schemas:

```typescript
// Shared DTOs (cross-module)
import { PaginationInputSchema } from "@/lib/shared/kernel/pagination";
import { ImageAssetSchema } from "@/lib/shared/kernel/dtos/common";

// Module-specific DTOs
import { CreateUserSchema } from "@/lib/modules/user/dtos/create-user.dto";
```

See [server documentation](../../server/README.md) for the full server architecture.

## Layer Responsibilities

| Layer                      | Responsibility                                 | Data Fetching          |
| -------------------------- | ---------------------------------------------- | ---------------------- |
| **Page**                   | Route entry, layout, metadata                  | Server components only |
| **Feature Component**      | Business logic, queries, mutations, form setup | Yes                    |
| **Presentation Component** | UI rendering, form fields, event handling      | No                     |
| **UI Primitive**           | Atomic, generic, reusable components           | No                     |

### Component Decision Flow

```
Does it fetch data or manage form state?
├── Yes → Feature Component (business)
│   └── Does it need URL state?
│       ├── Yes → Use nuqs hook
│       └── No → Use TanStack Query directly
└── No → Presentation Component
    └── Does it need form context?
        ├── Yes → Use useFormContext
        └── No → Pure props-based component
```

## Data Flow

### Schema Layers

| Layer               | Location                        | Purpose                          |
| ------------------- | ------------------------------- | -------------------------------- |
| **Database Schema** | `lib/core/schemas/`             | Entity definitions (drizzle-zod) |
| **DTO Schema**      | `lib/core/dtos/`                | API contracts, validation        |
| **Form Schema**     | `features/<feature>/schemas.ts` | UI-specific, composed from DTOs  |

### Request Flow

```
User Interaction
     │
     ▼
┌─────────────────┐
│  Feature Form   │ ─── Validates with Zod (Form Schema)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  tRPC Mutation  │ ─── Type-safe API call
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Server (tRPC)  │ ─── Validates with DTO Schema
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Database     │
└─────────────────┘
         │
         ▼
    Cache Invalidation
         │
         ▼
    UI Re-renders
```

## Documentation Index

| Document                                  | Description                              |
| ----------------------------------------- | ---------------------------------------- |
| [Conventions](./conventions.md)           | Layer responsibilities, decision flows   |
| [Data Fetching](./data-fetching.md)       | tRPC + TanStack Query patterns           |
| [Forms](./forms.md)                       | Zod + RHF + StandardForm conventions     |
| [State Management](./state-management.md) | URL state (nuqs), client state (Zustand) |
| [UI Patterns](./ui-patterns.md)           | shadcn/ui, component separation          |
| [Error Handling](./error-handling.md)     | Toast, form errors, boundaries           |
| [Folder Structure](./folder-structure.md) | Directory architecture                   |

## Quick Reference

### Data Fetching

```typescript
// Query
const { data, isLoading } = trpc.user.getById.useQuery({ id });

// Dependent query
const profileQuery = trpc.profile.get.useQuery();
const settingsQuery = trpc.settings.get.useQuery(
  { profileId: profileQuery.data?.id ?? "" },
  { enabled: !!profileQuery.data?.id },
);

// Mutation with cache invalidation
const trpcUtils = trpc.useUtils();
const mutation = trpc.user.update.useMutation();

await mutation.mutateAsync(data);
await trpcUtils.user.getById.invalidate({ id });
```

### Forms

```typescript
// Standard form setup
<StandardFormProvider form={form} onSubmit={onSubmit}>
  <StandardFormError />
  <StandardFormInput<FormType> name='email' label='Email' required />
  <StandardFormSelect<FormType> name='role' label='Role' options={options} />
  <Button type='submit'>Save</Button>
</StandardFormProvider>
```

### URL State

```typescript
// Type-safe URL state
const [tab, setTab] = useQueryState(
  "tab",
  parseAsStringLiteral(["overview", "settings"]).withDefault("overview"),
);
```

### Client State (Zustand)

```typescript
// Global store
const count = useCounterStore((state) => state.count);

// Context store (isolated)
const value = useStoreInContext((state) => state.value);
```

## Common Contracts

Located in `src/common/`:

| Contract        | Purpose                          |
| --------------- | -------------------------------- |
| `types.ts`      | Shared TypeScript types          |
| `constants.ts`  | App-wide constants, query params |
| `app-routes.ts` | Route path definitions           |
| `hooks.ts`      | Shared custom hooks              |

## Checklist for New Features

- [ ] Create feature folder under `src/features/<feature>/`
- [ ] Define Zod schema in `schemas.ts` (compose from DTOs)
- [ ] Create business component (`<feature>-form.tsx`)
- [ ] Create presentation components (`<feature>-form-fields.tsx`)
- [ ] Add feature-specific hooks in `hooks.ts`
- [ ] Use StandardForm components where applicable
- [ ] Handle loading and error states
- [ ] Invalidate relevant queries after mutations
