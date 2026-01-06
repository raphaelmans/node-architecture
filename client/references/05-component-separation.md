# Presentation vs Business Component Separation

This guide covers the component architecture pattern separating business logic from presentation.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Business Components                          │
│  - Data fetching (queries/mutations)                           │
│  - Form state management                                        │
│  - Business logic                                               │
│  - Navigation                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Presentation Components                        │
│  - UI rendering                                                 │
│  - Form field display                                           │
│  - Styling                                                      │
│  - User interaction handling (via props/context)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    UI Primitives (shadcn)                       │
│  - Atomic components                                            │
│  - No business logic                                            │
│  - Generic, reusable                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Types

| Type                        | Location                                                      | Responsibilities                 |
| --------------------------- | ------------------------------------------------------------- | -------------------------------- |
| **UI Primitives**           | `src/components/ui/`                                          | Atomic, stateless, generic       |
| **Custom UI**               | `src/components/custom-ui/`                                   | Composed primitives, app styling |
| **Business Components**     | `src/features/<feature>/components/<feature>-form.tsx`        | Data, mutations, logic           |
| **Presentation Components** | `src/features/<feature>/components/<feature>-form-fields.tsx` | Field rendering                  |

---

## Business Component Pattern

Business components handle:

- Data fetching
- Form initialization
- Mutations
- Cache invalidation
- Navigation
- Error handling

```typescript
// src/features/profile/components/profile-form.tsx
'use client'

import { useEffect } from 'react'
import { useForm, type FieldErrors } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from 'next/navigation'
import { Form } from '@/components/ui/form'
import { Button } from '@/components/ui/button'
import { trpc } from '@/lib/trpc/client'
import { useCatchErrorToast, useErrorToast } from '@/common/hooks'
import { profileFormSchema, type ProfileFormHandler } from '../schemas'
import appRoutes from '@/common/app-routes'

// Presentation components (imported)
import {
  ProfileFirstNameField,
  ProfileLastNameField,
  ProfileBioField,
  ProfileImageField,
} from './profile-form-fields'

export default function ProfileForm() {
  // ============================================
  // DATA FETCHING
  // ============================================
  const profileQuery = trpc.profile.getByCurrentUser.useQuery(
    { signedAssets: true },
    {
      retry: (attempt, error) => {
        if (utils.isTRPCNotFoundError(error)) return false
        return attempt <= 3
      },
    },
  )

  const professionalProfileQuery = trpc.professionalProfile.getByProfileId.useQuery(
    { profileId: profileQuery.data?.id ?? '' },
    { enabled: !!profileQuery.data?.id },
  )

  // ============================================
  // MUTATIONS
  // ============================================
  const profileMut = trpc.profile.upsertUserProfile.useMutation()
  const uploadImageMut = trpc.profile.uploadProfileImage.useMutation()
  const updateOnboardingStatusMut = trpc.profile.updateOnboardingStatus.useMutation()

  // ============================================
  // FORM SETUP
  // ============================================
  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
    mode: 'onChange',
    defaultValues: {
      firstName: '',
      lastName: '',
      bio: '',
      imageAsset: { file: undefined, url: '' },
    },
  })

  const {
    reset,
    formState: { isDirty, isSubmitting, isValid },
  } = form

  // ============================================
  // DATA SYNC (Server -> Form)
  // ============================================
  useEffect(() => {
    if (profileQuery.data) {
      reset({
        firstName: profileQuery.data.firstName ?? '',
        lastName: profileQuery.data.lastName ?? '',
        bio: profileQuery.data.bio ?? '',
        imageAsset: {
          file: undefined,
          url: profileQuery.data.profile_img ?? '',
        },
      })
    }
  }, [profileQuery.data, reset])

  // ============================================
  // SUBMISSION LOGIC
  // ============================================
  const router = useRouter()
  const trpcUtils = trpc.useUtils()
  const catchErrorToast = useCatchErrorToast()
  const errorToast = useErrorToast()

  const onSubmit = async ({ imageAsset, ...data }: ProfileFormHandler) => {
    return catchErrorToast(
      async () => {
        // 1. Update profile
        const profileResult = await profileMut.mutateAsync(data)

        // 2. Handle image upload
        if (imageAsset.file) {
          const formData = new FormData()
          formData.append('profileId', profileResult.id)
          formData.append('profileImage', imageAsset.file)
          await uploadImageMut.mutateAsync(formData)
        }

        // 3. Update onboarding status
        await updateOnboardingStatusMut.mutateAsync({ onboarded: true })

        // 4. Invalidate cache
        await trpcUtils.profile.getByCurrentUser.invalidate()

        // 5. Navigate
        router.push(appRoutes.dashboard)
      },
      { description: 'Profile updated successfully!' },
    )
  }

  const onSubmitError = (errors: FieldErrors<ProfileFormHandler>) => {
    errorToast({
      description: Object.values(errors).map(e => e.message).join(', '),
      variant: 'destructive',
    })
  }

  // ============================================
  // LOADING STATE
  // ============================================
  if (profileQuery.isLoading || professionalProfileQuery.isLoading) {
    return <ProfileFormSkeleton />
  }

  // ============================================
  // RENDER (Presentation Layer)
  // ============================================
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit, onSubmitError)} className='grid gap-4'>
        {/* Personal Details Section */}
        <section className='space-y-4'>
          <h4 className='text-2xl font-semibold'>Personal Details</h4>
          <ProfileImageField />
          <ProfileFirstNameField />
          <ProfileLastNameField />
          <ProfileBioField />
        </section>

        {/* Submit Button */}
        <Button
          type='submit'
          disabled={isSubmitting || !isDirty || !isValid}
          isLoading={isSubmitting}
        >
          Update Profile
        </Button>
      </form>
    </Form>
  )
}
```

---

## Presentation Component Pattern

Presentation components handle:

- UI rendering
- Form context consumption
- Styling
- User interaction (delegated to form)

```typescript
// src/features/profile/components/profile-form-fields.tsx
import { useFormContext } from 'react-hook-form'
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import type { ProfileFormHandler } from '../schemas'

// ============================================
// SIMPLE FIELD COMPONENT
// ============================================
export function ProfileFirstNameField() {
  const { control } = useFormContext<ProfileFormHandler>()

  return (
    <FormField
      control={control}
      name='firstName'
      render={({ field }) => (
        <FormItem>
          <FormLabel>First Name</FormLabel>
          <FormControl>
            <Input placeholder='John' {...field} />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  )
}

export function ProfileLastNameField() {
  const { control } = useFormContext<ProfileFormHandler>()

  return (
    <FormField
      control={control}
      name='lastName'
      render={({ field }) => (
        <FormItem>
          <FormLabel>Last Name</FormLabel>
          <FormControl>
            <Input placeholder='Doe' {...field} />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  )
}

export function ProfileBioField() {
  const { control } = useFormContext<ProfileFormHandler>()

  return (
    <FormField
      control={control}
      name='bio'
      render={({ field }) => (
        <FormItem>
          <FormLabel>Bio</FormLabel>
          <FormControl>
            <Textarea placeholder='Tell us about yourself...' {...field} />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  )
}
```

---

## Complex Presentation Component

For fields with internal logic (file upload, etc.):

```typescript
// src/features/profile/components/profile-form-fields.tsx
import { useCallback } from 'react'
import { useFormContext } from 'react-hook-form'
import { useDropzone } from 'react-dropzone'
import type { ProfileFormHandler } from '../schemas'

export function ProfileImageField() {
  const { control, watch, setValue } = useFormContext<ProfileFormHandler>()
  const currentImageUrl = watch('imageAsset.url')
  const errorToast = useErrorToast()

  // Internal presentation logic (not business logic)
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      if (!validateFileSize(file, FILE_SIZE_LIMITS.PROFILE_IMAGE)) {
        errorToast({ description: 'File too large' })
        return
      }
      setValue('imageAsset.file', file, {
        shouldDirty: true,
        shouldTouch: true,
        shouldValidate: true,
      })
      setValue('imageAsset.url', URL.createObjectURL(file), {
        shouldDirty: true,
        shouldTouch: true,
        shouldValidate: true,
      })
    }
  }, [setValue, errorToast])

  const removeImage = useCallback(() => {
    setValue('imageAsset.file', undefined, { shouldDirty: true })
    setValue('imageAsset.url', '', { shouldDirty: true })
  }, [setValue])

  const { getRootProps, getInputProps, open } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxFiles: 1,
  })

  return (
    <FormField
      control={control}
      name='imageAsset.url'
      render={() => (
        <FormItem>
          <FormLabel>Profile Picture</FormLabel>
          <FormControl>
            <div {...getRootProps()} className='flex items-center gap-4'>
              <input {...getInputProps()} />
              <Avatar>
                <AvatarImage src={currentImageUrl} />
                <AvatarFallback><ImageIcon /></AvatarFallback>
              </Avatar>
              {currentImageUrl && (
                <Button type='button' variant='ghost' onClick={removeImage}>
                  <X />
                </Button>
              )}
              <Button type='button' onClick={open}>
                Upload
              </Button>
            </div>
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  )
}
```

---

## Skeleton Components

```typescript
// In the same file as the business component
export function ProfileFormSkeleton() {
  return (
    <div className='space-y-4'>
      {Array.from({ length: 7 }).map((_, i) => (
        <div className='space-y-2' key={i}>
          <Skeleton className='h-4 w-20' />
          <Skeleton className='h-10 w-full' />
        </div>
      ))}
      <Skeleton className='h-10 w-32' />
    </div>
  )
}
```

---

## Cross-Feature Field Reuse

Fields can be imported from other features:

```typescript
// src/features/profile/components/profile-form-fields.tsx

// Re-export from another feature
export { ProfessionalProfileTitleField } from '@/features/professional-profile/components/professional-profile-form-fields'
```

```typescript
// src/features/profile/components/profile-form.tsx
import {
  ProfileFirstNameField,
  ProfileLastNameField,
  ProfessionalProfileTitleField, // From professional-profile feature
} from './profile-form-fields'
```

---

## Benefits of This Pattern

| Benefit                    | Description                                   |
| -------------------------- | --------------------------------------------- |
| **Separation of Concerns** | Business logic isolated from presentation     |
| **Testability**            | Fields can be tested independently            |
| **Reusability**            | Fields work in any form with matching schema  |
| **Maintainability**        | Changes to UI don't affect business logic     |
| **Type Safety**            | Generic type ensures field names match schema |

---

## File Structure

```
src/features/<feature>/
├── components/
│   ├── <feature>-form.tsx           # Business component
│   │   - Data fetching
│   │   - Form setup
│   │   - Mutations
│   │   - Submission logic
│   │   - Skeleton export
│   │
│   └── <feature>-form-fields.tsx    # Presentation components
│       - Field components
│       - useFormContext consumption
│       - UI rendering
│
├── hooks.ts                         # Feature-specific hooks
└── schemas.ts                       # Zod schemas + types
```

---

## Decision Guide

| Question                     | Business Component | Presentation Component |
| ---------------------------- | ------------------ | ---------------------- |
| Does it fetch data?          | Yes                | No                     |
| Does it call mutations?      | Yes                | No                     |
| Does it manage form state?   | Yes                | Consumes via context   |
| Does it navigate?            | Yes                | No                     |
| Does it render UI?           | Delegates          | Yes                    |
| Is it reusable across forms? | No                 | Yes                    |
