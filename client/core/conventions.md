# Frontend Architecture Conventions

> Core architectural conventions defining layer responsibilities, component patterns, and the common module.

## Layer Responsibilities

### Pages (Route Components)

**Location:** `src/app/`

**Responsibilities:**

- Route entry points
- Layout composition
- Metadata (SEO, OpenGraph)
- Server-side data fetching (RSC)

**Rules:**

- Minimal logic
- Delegate to feature components
- Use route groups for organization (`(authenticated)/`, `(guest)/`)

```typescript
// src/app/(authenticated)/profile/page.tsx

import { ProfileForm } from '@/features/profile/components/profile-form'

export const metadata = {
  title: 'Profile Settings',
}

export default function ProfilePage() {
  return (
    <div className='container py-8'>
      <h1 className='text-2xl font-bold mb-6'>Profile Settings</h1>
      <ProfileForm />
    </div>
  )
}
```

### Feature Components (Business Layer)

**Location:** `src/features/<feature>/components/<feature>-form.tsx`

**Responsibilities:**

- Data fetching (queries, mutations)
- Form state management
- Business logic orchestration
- Cache invalidation
- Navigation

**Rules:**

- One feature component per major UI interaction
- Owns the form setup (`useForm`, `zodResolver`)
- Handles submission logic
- Delegates rendering to presentation components

```typescript
// src/features/profile/components/profile-form.tsx
'use client'

export default function ProfileForm() {
  // Data fetching
  const profileQuery = trpc.profile.getByCurrentUser.useQuery()

  // Form setup
  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
  })

  // Mutations
  const updateMut = trpc.profile.update.useMutation()
  const trpcUtils = trpc.useUtils()

  // Business logic
  const onSubmit = async (data: ProfileFormHandler) => {
    await updateMut.mutateAsync(data)
    await trpcUtils.profile.getByCurrentUser.invalidate()
    router.push(appRoutes.dashboard)
  }

  // Render with presentation components
  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      <ProfileFirstNameField />
      <ProfileLastNameField />
      <Button type='submit'>Save</Button>
    </StandardFormProvider>
  )
}
```

### Presentation Components (Display Layer)

**Location:** `src/features/<feature>/components/<feature>-form-fields.tsx`

**Responsibilities:**

- UI rendering
- Form context consumption
- Styling and layout
- User interaction handling (via callbacks)

**Rules:**

- No data fetching
- No direct API calls
- Use `useFormContext` for form state
- Pure rendering based on props/context

```typescript
// src/features/profile/components/profile-form-fields.tsx
'use client'

import { useFormContext } from 'react-hook-form'
import type { ProfileFormHandler } from '../schemas'

export function ProfileFirstNameField() {
  const { control } = useFormContext<ProfileFormHandler>()

  return (
    <StandardFormInput<ProfileFormHandler>
      name='firstName'
      label='First Name'
      placeholder='John'
      required
    />
  )
}
```

### UI Primitives (Component Library)

**Location:** `src/components/ui/`

**Responsibilities:**

- Atomic, generic components
- shadcn/ui implementations
- Radix UI wrappers

**Rules:**

- No business logic
- No feature-specific code
- Fully reusable across features
- Follow shadcn/ui conventions

```typescript
// src/components/ui/button.tsx
// Standard shadcn/ui component
```

### Feature Hooks

**Location:** `src/features/<feature>/hooks.ts`

**Responsibilities:**

- URL state management (nuqs)
- Feature-specific custom logic
- Derived state calculations

**Rules:**

- Reusable within the feature
- May use nuqs for URL state
- No direct data fetching (use tRPC hooks in components)

```typescript
// src/features/landing/hooks.ts

import { parseAsStringLiteral, useQueryState } from "nuqs";

const landingStates = ["login", "signup"] as const;

export const useQueryLandingState = () => {
  return useQueryState(
    "step",
    parseAsStringLiteral(landingStates).withOptions({ history: "push" }),
  );
};
```

## Decision Flows

### Component Type Decision

```
Does it fetch data or own form state?
├── Yes → Feature Component (business)
│   └── Create: <feature>-form.tsx or <feature>-view.tsx
└── No → Presentation Component
    └── Does it consume form context?
        ├── Yes → Create: <feature>-form-fields.tsx
        └── No → Props-based component
            └── Is it feature-specific?
                ├── Yes → features/<feature>/components/
                └── No → components/ui/ or components/custom-ui/
```

### Data Fetching Decision

```
Is data needed for this component?
├── No → Don't fetch, receive via props
└── Yes
    └── Is it server-side (RSC)?
        ├── Yes → Use tRPC caller in page
        └── No (client component)
            └── Is it dependent on other data?
                ├── Yes → Use enabled flag
                │   trpc.x.useQuery({ id }, { enabled: !!id })
                └── No → Direct query
                    trpc.x.useQuery()
```

### State Management Decision

```
What kind of state is this?
├── Server data → TanStack Query (via tRPC)
├── Form data → react-hook-form
├── URL state (shareable) → nuqs
├── Global UI state → Zustand (global store)
└── Local component tree state → Zustand (context store)
```

## Common Module

**Location:** `src/common/`

The common module contains app-wide shared code that doesn't belong to a specific feature.

### Structure

```
src/common/
├── providers/          # React context providers
│   ├── trpc-provider.tsx
│   ├── theme-provider.tsx
│   └── index.tsx
├── hooks.ts            # Shared custom hooks
├── constants.ts        # Global constants, query params
├── app-routes.ts       # Route path definitions
├── types.ts            # Shared TypeScript types
└── utils.ts            # Utility functions
```

### app-routes.ts

Centralized route definitions:

```typescript
// src/common/app-routes.ts

const appRoutes = {
  home: "/",
  auth: {
    login: "/login",
    signup: "/signup",
    forgotPassword: "/forgot-password",
  },
  dashboard: "/dashboard",
  profile: {
    base: "/profile",
    edit: "/profile/edit",
  },
  settings: {
    base: "/settings",
    billing: "/settings/billing",
  },
} as const;

export default appRoutes;
```

### constants.ts

Global constants including URL query params:

```typescript
// src/common/constants.ts

export const appQueryParams = {
  error: "error",
  step: "step",
  tab: "tab",
  page: "page",
  search: "q",
} as const;

export const FILE_SIZE_LIMITS = {
  PROFILE_IMAGE: 5 * 1024 * 1024,
  DOCUMENT: 10 * 1024 * 1024,
} as const;
```

### types.ts

Shared TypeScript types:

```typescript
// src/common/types.ts

export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;

export interface PaginationParams {
  page: number;
  limit: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}
```

### hooks.ts

Shared custom hooks:

```typescript
// src/common/hooks.ts

export function useCatchErrorToast() {
  const { toast } = useToast();

  return async <T>(
    fn: () => Promise<T>,
    options?: { description?: string },
  ): Promise<T | undefined> => {
    try {
      const result = await fn();
      if (options?.description) {
        toast({ description: options.description });
      }
      return result;
    } catch (error) {
      toast({
        description:
          error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
      return undefined;
    }
  };
}

export function useErrorToast() {
  const { toast } = useToast();
  return (options: { description: string; variant?: "destructive" }) => {
    toast(options);
  };
}
```

## Schema Conventions

### Three-Layer Schema Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Database Schemas (drizzle-zod)               │
│  Location: src/lib/shared/infra/db/schema.ts           │
│  Owner: Backend                                         │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 2: DTOs (API Contracts)                          │
│  Shared: src/lib/shared/kernel/dtos/                    │
│  Module: src/lib/modules/<module>/dtos/                 │
│  Owner: Shared (Backend defines, Frontend consumes)     │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Form Schemas                                  │
│  Location: src/features/<feature>/schemas.ts            │
│  Owner: Frontend                                        │
└─────────────────────────────────────────────────────────┘
```

### Form Schema Pattern

```typescript
// src/features/profile/schemas.ts

import { z } from "zod";
import { UpdateProfileInputSchema } from "@/lib/modules/profile/dtos/update-profile.dto";
import { ImageAssetSchema } from "@/lib/shared/kernel/dtos/common";

// Compose DTO with UI-specific fields
export const profileFormSchema =
  UpdateProfileInputSchema.merge(ImageAssetSchema); // Add file handling

export type ProfileFormHandler = z.infer<typeof profileFormSchema>;
```

## Naming Conventions

### Files

| Type                | Convention                  | Example                   |
| ------------------- | --------------------------- | ------------------------- |
| Feature component   | `<feature>-<type>.tsx`      | `profile-form.tsx`        |
| Presentation fields | `<feature>-form-fields.tsx` | `profile-form-fields.tsx` |
| Feature hooks       | `hooks.ts`                  | `hooks.ts`                |
| Feature schemas     | `schemas.ts`                | `schemas.ts`              |
| UI primitive        | `<component>.tsx`           | `button.tsx`              |

### Components

| Type               | Convention           | Example                 |
| ------------------ | -------------------- | ----------------------- |
| Feature component  | `PascalCase`         | `ProfileForm`           |
| Presentation field | `PascalCase + Field` | `ProfileFirstNameField` |
| UI primitive       | `PascalCase`         | `Button`                |

### Hooks

| Type           | Convention             | Example                |
| -------------- | ---------------------- | ---------------------- |
| URL state hook | `useQuery<Name>State`  | `useQueryLandingState` |
| Feature hook   | `use<Feature><Action>` | `useProfileUpdate`     |
| Shared hook    | `use<Action>`          | `useCatchErrorToast`   |

## Import Order

```typescript
// 1. React/Next
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

// 2. External libraries
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

// 3. Internal - UI components
import { Button } from "@/components/ui/button";
import { StandardFormProvider } from "@/components/form";

// 4. Internal - common/lib
import { trpc } from "@/lib/trpc/client";
import appRoutes from "@/common/app-routes";

// 5. Internal - feature (relative)
import { ProfileFirstNameField } from "./profile-form-fields";
import { profileFormSchema, type ProfileFormHandler } from "../schemas";
```

## Checklist

- [ ] Feature folder created under `src/features/<feature>/`
- [ ] Schema defined in `schemas.ts`, composed from DTOs
- [ ] Business component handles data fetching and form state
- [ ] Presentation components use `useFormContext`, no fetching
- [ ] URL state uses nuqs with centralized param names
- [ ] Mutations invalidate relevant queries
- [ ] Loading and error states handled
- [ ] Routes added to `app-routes.ts`
