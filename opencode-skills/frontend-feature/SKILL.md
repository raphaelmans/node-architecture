---
name: frontend-feature
description: Create new frontend features with components, schemas, hooks, and page routes in Next.js App Router projects with tRPC and react-hook-form
---

# Creating a New Frontend Feature

Use this skill when adding a new feature, creating a new page, or building UI functionality.

## Architecture

```
src/features/<feature>/
├── components/
│   ├── <feature>-form.tsx           # Business component (data, mutations)
│   ├── <feature>-form-fields.tsx    # Presentation (form fields)
│   ├── <feature>-list.tsx           # List view
│   └── <feature>-skeleton.tsx       # Loading state
├── stores/                          # Zustand stores (if needed)
├── hooks.ts                         # URL state hooks (nuqs)
└── schemas.ts                       # Zod form schemas
```

## Step-by-Step

### 1. Create Schema

```typescript
// src/features/<feature>/schemas.ts
import { z } from 'zod'
import { CreateEntitySchema } from '@/lib/modules/<module>/dtos/create-entity.dto'
import { ImageAssetSchema } from '@/lib/shared/kernel/dtos/common'

// Compose DTO with UI-specific fields
export const featureFormSchema = CreateEntitySchema.merge(
  z.object({
    imageAsset: ImageAssetSchema.optional(),
  })
)

export type FeatureFormHandler = z.infer<typeof featureFormSchema>
```

### 2. Create URL State Hooks

```typescript
// src/features/<feature>/hooks.ts
import { parseAsStringLiteral, parseAsInteger, useQueryState } from 'nuqs'

const tabs = ['details', 'settings', 'history'] as const

export const useQueryFeatureTab = () => {
  return useQueryState(
    'tab',
    parseAsStringLiteral(tabs).withDefault('details').withOptions({ history: 'push' })
  )
}

export const useQueryFeaturePagination = () => {
  const [page, setPage] = useQueryState(
    'page',
    parseAsInteger.withDefault(1).withOptions({ history: 'replace' })
  )
  return { page, setPage }
}
```

### 3. Create Business Component (Form)

```typescript
// src/features/<feature>/components/<feature>-form.tsx
'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { StandardFormProvider, StandardFormError } from '@/components/form'
import { trpc } from '@/lib/trpc/client'
import appRoutes from '@/common/app-routes'
import { useCatchErrorToast } from '@/common/hooks'
import { FeatureNameField, FeatureDescriptionField } from './<feature>-form-fields'
import { featureFormSchema, type FeatureFormHandler } from '../schemas'
import { FeatureFormSkeleton } from './<feature>-skeleton'

interface FeatureFormProps {
  entityId?: string // For edit mode
}

export function FeatureForm({ entityId }: FeatureFormProps) {
  const router = useRouter()
  const trpcUtils = trpc.useUtils()
  const catchErrorToast = useCatchErrorToast()

  // Data fetching (edit mode)
  const entityQuery = trpc.module.getById.useQuery(
    { id: entityId ?? '' },
    { enabled: !!entityId }
  )

  // Mutations
  const createMut = trpc.module.create.useMutation()
  const updateMut = trpc.module.update.useMutation()

  // Form setup
  const form = useForm<FeatureFormHandler>({
    resolver: zodResolver(featureFormSchema),
    mode: 'onChange',
    defaultValues: {
      name: '',
      description: '',
    },
  })

  const { reset } = form

  // Sync server data to form (edit mode)
  useEffect(() => {
    if (entityQuery.data) {
      reset({
        name: entityQuery.data.name ?? '',
        description: entityQuery.data.description ?? '',
      })
    }
  }, [entityQuery.data, reset])

  // Submit handler
  const onSubmit = async (data: FeatureFormHandler) => {
    return catchErrorToast(
      async () => {
        if (entityId) {
          await updateMut.mutateAsync({ id: entityId, ...data })
          await trpcUtils.module.getById.invalidate({ id: entityId })
        } else {
          await createMut.mutateAsync(data)
        }
        await trpcUtils.module.list.invalidate()
        router.push(appRoutes.feature.list)
      },
      { description: entityId ? 'Updated!' : 'Created!' }
    )
  }

  if (entityId && entityQuery.isLoading) {
    return <FeatureFormSkeleton />
  }

  const isSubmitting = createMut.isPending || updateMut.isPending

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      <StandardFormError />
      <FeatureNameField />
      <FeatureDescriptionField />
      <div className="flex gap-4">
        <Button type="button" variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting || !form.formState.isDirty}>
          {isSubmitting ? 'Saving...' : entityId ? 'Update' : 'Create'}
        </Button>
      </div>
    </StandardFormProvider>
  )
}
```

### 4. Create Presentation Components (Form Fields)

```typescript
// src/features/<feature>/components/<feature>-form-fields.tsx
'use client'

import { StandardFormInput, StandardFormTextarea } from '@/components/form'
import type { FeatureFormHandler } from '../schemas'

export function FeatureNameField() {
  return (
    <StandardFormInput<FeatureFormHandler>
      name="name"
      label="Name"
      placeholder="Enter name"
      required
    />
  )
}

export function FeatureDescriptionField() {
  return (
    <StandardFormTextarea<FeatureFormHandler>
      name="description"
      label="Description"
      placeholder="Enter description"
    />
  )
}
```

### 5. Create Skeleton

```typescript
// src/features/<feature>/components/<feature>-skeleton.tsx
import { Skeleton } from '@/components/ui/skeleton'

export function FeatureFormSkeleton() {
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
  )
}
```

### 6. Create Pages

```typescript
// src/app/(authenticated)/<feature>/page.tsx
import { FeatureList } from '@/features/<feature>/components/<feature>-list'

export const metadata = { title: 'Features' }

export default function FeaturePage() {
  return (
    <div className="container py-8">
      <h1 className="text-2xl font-bold mb-6">Features</h1>
      <FeatureList />
    </div>
  )
}
```

```typescript
// src/app/(authenticated)/<feature>/new/page.tsx
import { FeatureForm } from '@/features/<feature>/components/<feature>-form'

export const metadata = { title: 'New Feature' }

export default function NewFeaturePage() {
  return (
    <div className="container py-8">
      <h1 className="text-2xl font-bold mb-6">New Feature</h1>
      <FeatureForm />
    </div>
  )
}
```

```typescript
// src/app/(authenticated)/<feature>/[id]/edit/page.tsx
import { FeatureForm } from '@/features/<feature>/components/<feature>-form'

export default function EditFeaturePage({ params }: { params: { id: string } }) {
  return (
    <div className="container py-8">
      <h1 className="text-2xl font-bold mb-6">Edit Feature</h1>
      <FeatureForm entityId={params.id} />
    </div>
  )
}
```

### 7. Add Routes

```typescript
// src/common/app-routes.ts
const appRoutes = {
  // ... existing
  feature: {
    list: '/feature',
    new: '/feature/new',
    edit: (id: string) => `/feature/${id}/edit`,
    view: (id: string) => `/feature/${id}`,
  },
} as const
```

## Component Decision Flow

```
Does it fetch data or own form state?
├── Yes → Business Component (owns useForm, mutations)
└── No → Presentation Component
    └── Uses form context? → Form field component
    └── Props only? → Card/display component
```

## Checklist

- [ ] Schema in `schemas.ts` (composes from DTOs)
- [ ] URL state hooks in `hooks.ts`
- [ ] Business component owns useForm + mutations
- [ ] Presentation components are stateless
- [ ] Skeleton component for loading
- [ ] Pages created in app router
- [ ] Routes added to app-routes.ts
- [ ] Mutations invalidate affected queries
