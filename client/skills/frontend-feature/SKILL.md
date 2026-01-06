---
name: frontend-feature
description: Creates new frontend features with components, schemas, hooks, and page routes. Use when adding a new feature, creating a new page, building a new form, or when the user mentions "new feature", "add page", "create component", "frontend module".
---

# Creating a New Frontend Feature

## Overview

A feature encapsulates related UI functionality with clear separation between business and presentation logic:

```
src/features/<feature>/
├── components/
│   ├── <feature>-form.tsx           # Business component (data fetching, form state)
│   ├── <feature>-form-fields.tsx    # Presentation components (form fields)
│   ├── <feature>-list.tsx           # List view (if applicable)
│   └── <feature>-card.tsx           # Card component (if applicable)
├── stores/                          # Zustand stores (if needed)
│   └── <name>-store.ts
├── hooks.ts                         # URL state, feature hooks
└── schemas.ts                       # Zod form schemas
```

## Step-by-Step Process

### 1. Create Feature Folder Structure

```
src/features/<feature>/
├── components/
├── hooks.ts
└── schemas.ts
```

### 2. Define Form Schema

Compose from DTO schemas (from `lib/modules/`) with UI-specific fields:

```typescript
// src/features/<feature>/schemas.ts
import { z } from 'zod';
import { Create<Entity>Schema } from '@/lib/modules/<module>/dtos/create-<entity>.dto';
import { ImageAssetSchema } from '@/lib/shared/kernel/dtos/common';

// Compose DTO with UI-specific fields
export const <feature>FormSchema = Create<Entity>Schema.merge(
  z.object({
    // Add UI-only fields if needed
    imageAsset: ImageAssetSchema.optional(),
  })
);

export type <Feature>FormHandler = z.infer<typeof <feature>FormSchema>;
```

### 3. Create Feature Hooks (URL State)

```typescript
// src/features/<feature>/hooks.ts
import { parseAsStringLiteral, parseAsInteger, useQueryState } from 'nuqs';
import { appQueryParams } from '@/common/constants';

// Tab navigation
const tabs = ['details', 'settings', 'history'] as const;

export const useQuery<Feature>Tab = () => {
  return useQueryState(
    appQueryParams.tab,
    parseAsStringLiteral(tabs)
      .withDefault('details')
      .withOptions({ history: 'push' }),
  );
};

// Pagination
export const useQuery<Feature>Pagination = () => {
  const [page, setPage] = useQueryState(
    appQueryParams.page,
    parseAsInteger.withDefault(1).withOptions({ history: 'replace' }),
  );
  return { page, setPage };
};
```

### 4. Create Business Component (Form)

```typescript
// src/features/<feature>/components/<feature>-form.tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import {
  StandardFormProvider,
  StandardFormError,
} from '@/components/form';
import { trpc } from '@/lib/trpc/client';
import appRoutes from '@/common/app-routes';
import { useCatchErrorToast } from '@/common/hooks';
import {
  <Feature>NameField,
  <Feature>DescriptionField,
} from './<feature>-form-fields';
import { <feature>FormSchema, type <Feature>FormHandler } from '../schemas';
import { <Feature>FormSkeleton } from './<feature>-skeleton';

interface <Feature>FormProps {
  <entity>Id?: string; // For edit mode
}

export function <Feature>Form({ <entity>Id }: <Feature>FormProps) {
  const router = useRouter();
  const trpcUtils = trpc.useUtils();
  const catchErrorToast = useCatchErrorToast();

  // Data fetching (edit mode)
  const <entity>Query = trpc.<module>.getById.useQuery(
    { id: <entity>Id ?? '' },
    { enabled: !!<entity>Id },
  );

  // Mutations
  const createMut = trpc.<module>.create.useMutation();
  const updateMut = trpc.<module>.update.useMutation();

  // Form setup
  const form = useForm<<Feature>FormHandler>({
    resolver: zodResolver(<feature>FormSchema),
    mode: 'onChange',
    defaultValues: {
      name: '',
      description: '',
    },
  });

  const { reset } = form;

  // Sync server data to form (edit mode)
  useEffect(() => {
    if (<entity>Query.data) {
      reset({
        name: <entity>Query.data.name ?? '',
        description: <entity>Query.data.description ?? '',
      });
    }
  }, [<entity>Query.data, reset]);

  // Submit handler
  const onSubmit = async (data: <Feature>FormHandler) => {
    return catchErrorToast(
      async () => {
        if (<entity>Id) {
          await updateMut.mutateAsync({ id: <entity>Id, ...data });
          await trpcUtils.<module>.getById.invalidate({ id: <entity>Id });
        } else {
          await createMut.mutateAsync(data);
        }
        await trpcUtils.<module>.list.invalidate();
        router.push(appRoutes.<feature>.list);
      },
      { description: <entity>Id ? 'Updated successfully!' : 'Created successfully!' },
    );
  };

  // Loading state
  if (<entity>Id && <entity>Query.isLoading) {
    return <<Feature>FormSkeleton />;
  }

  const isSubmitting = createMut.isPending || updateMut.isPending;

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      <StandardFormError />
      
      <<Feature>NameField />
      <<Feature>DescriptionField />
      
      <div className="flex gap-4">
        <Button
          type="button"
          variant="outline"
          onClick={() => router.back()}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={isSubmitting || !form.formState.isDirty}
        >
          {isSubmitting ? 'Saving...' : <entity>Id ? 'Update' : 'Create'}
        </Button>
      </div>
    </StandardFormProvider>
  );
}
```

### 5. Create Presentation Components (Form Fields)

```typescript
// src/features/<feature>/components/<feature>-form-fields.tsx
'use client';

import { StandardFormInput, StandardFormTextarea } from '@/components/form';
import type { <Feature>FormHandler } from '../schemas';

export function <Feature>NameField() {
  return (
    <StandardFormInput<<Feature>FormHandler>
      name="name"
      label="Name"
      placeholder="Enter name"
      required
    />
  );
}

export function <Feature>DescriptionField() {
  return (
    <StandardFormTextarea<<Feature>FormHandler>
      name="description"
      label="Description"
      placeholder="Enter description"
    />
  );
}
```

### 6. Create Skeleton Component

```typescript
// src/features/<feature>/components/<feature>-skeleton.tsx
import { Skeleton } from '@/components/ui/skeleton';

export function <Feature>FormSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <div className="space-y-2" key={i}>
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-10 w-full" />
        </div>
      ))}
      <Skeleton className="h-10 w-32" />
    </div>
  );
}
```

### 7. Create Page Route

```typescript
// src/app/(authenticated)/<feature>/page.tsx
import { <Feature>List } from '@/features/<feature>/components/<feature>-list';

export const metadata = {
  title: '<Feature>s',
};

export default function <Feature>Page() {
  return (
    <div className="container py-8">
      <h1 className="text-2xl font-bold mb-6"><Feature>s</h1>
      <<Feature>List />
    </div>
  );
}
```

```typescript
// src/app/(authenticated)/<feature>/new/page.tsx
import { <Feature>Form } from '@/features/<feature>/components/<feature>-form';

export const metadata = {
  title: 'New <Feature>',
};

export default function New<Feature>Page() {
  return (
    <div className="container py-8">
      <h1 className="text-2xl font-bold mb-6">New <Feature></h1>
      <<Feature>Form />
    </div>
  );
}
```

```typescript
// src/app/(authenticated)/<feature>/[id]/edit/page.tsx
import { <Feature>Form } from '@/features/<feature>/components/<feature>-form';

export const metadata = {
  title: 'Edit <Feature>',
};

export default function Edit<Feature>Page({
  params,
}: {
  params: { id: string };
}) {
  return (
    <div className="container py-8">
      <h1 className="text-2xl font-bold mb-6">Edit <Feature></h1>
      <<Feature>Form <entity>Id={params.id} />
    </div>
  );
}
```

### 8. Add Routes to app-routes.ts

```typescript
// src/common/app-routes.ts
const appRoutes = {
  // ... existing routes
  <feature>: {
    list: '/<feature>',
    new: '/<feature>/new',
    edit: (id: string) => `/<feature>/${id}/edit`,
    view: (id: string) => `/<feature>/${id}`,
  },
} as const;
```

## Component Decision Flow

```
Does it fetch data or own form state?
├── Yes → Business Component (<feature>-form.tsx)
│   └── Owns useForm, handles mutations, navigation
└── No → Presentation Component
    └── Does it consume form context?
        ├── Yes → <feature>-form-fields.tsx (uses useFormContext)
        └── No → Props-based component (<feature>-card.tsx)
```

## Key Rules

| Rule | Description |
|------|-------------|
| Business components own data | Queries, mutations, form state |
| Presentation components render | No fetching, use useFormContext or props |
| Schemas compose from DTOs | Form schema = DTO + UI-specific fields |
| URL state via nuqs | Shareable, bookmarkable state |
| Invalidate after mutations | Always invalidate affected queries |

See [references/feature-patterns.md](references/feature-patterns.md) for more patterns.
