# Forms

> Conventions for form handling using Zod, react-hook-form, and StandardForm components.

## Overview

Form handling uses:

- **Zod** for schema validation
- **react-hook-form** for form state management
- **@hookform/resolvers** for Zod integration
- **StandardForm** components for consistent UI

```
┌─────────────────────────────────────────────────────────────┐
│                      Form Schema (Zod)                       │
│                   features/<feature>/schemas.ts              │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     useForm + zodResolver                    │
│                    Feature Component                         │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   StandardFormProvider                       │
│              Provides form context + layout                  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  StandardForm* Components                    │
│           Input, Select, Textarea, Field, etc.              │
└─────────────────────────────────────────────────────────────┘
```

## Schema Architecture

### Three-Layer Schema Pattern

```
DTO Schema (API Contract)
       │
       ▼ .merge()
Form Schema (UI-specific)
       │
       ▼ z.infer<>
TypeScript Type
```

### Form Schema Definition

```typescript
// src/features/profile/schemas.ts

import { z } from "zod";
import { updateProfileDtoSchema } from "@/lib/core/dtos/profile-dtos";
import { imageUploadSchema } from "@/lib/core/common-schemas";

// Compose DTO with UI-specific fields
export const profileFormSchema =
  updateProfileDtoSchema.merge(imageUploadSchema);

export type ProfileFormHandler = z.infer<typeof profileFormSchema>;
```

### Common Schemas

```typescript
// src/lib/core/common-schemas.ts

import { z } from "zod";

// Image asset for file uploads
export const imageAssetSchema = z.object({
  file: z.instanceof(File).optional(),
  url: z.string(),
});

export const imageUploadSchema = z.object({
  imageAsset: imageAssetSchema,
});

export type ImageAsset = z.infer<typeof imageAssetSchema>;
```

## StandardForm Components

### Component Hierarchy

```
src/components/form/
├── StandardFormProvider.tsx    # Form wrapper with layout context
├── StandardFormError.tsx       # Root error display
├── fields/
│   ├── StandardFormInput.tsx   # Text inputs
│   ├── StandardFormSelect.tsx  # Select dropdowns
│   ├── StandardFormTextarea.tsx
│   ├── StandardFormCheckbox.tsx
│   └── StandardFormField.tsx   # Composition wrapper
├── context.tsx                 # Layout context
├── types.ts                    # Shared types
└── index.ts                    # Barrel export
```

### StandardFormProvider

```typescript
<StandardFormProvider
  form={form}
  onSubmit={onSubmit}
  onError={onError}        // Optional validation error handler
  layout='vertical'        // 'vertical' | 'horizontal' | 'inline'
  className='space-y-4'
>
  {children}
</StandardFormProvider>
```

### StandardFormInput

```typescript
<StandardFormInput<FormType>
  name='email'              // Type-safe field name
  label='Email'
  placeholder='john@example.com'
  type='email'              // 'text' | 'email' | 'password' | 'number' | 'tel' | 'url'
  required
  disabled={isSubmitting}
  description='Your work email'
  size='default'            // 'sm' | 'default' | 'lg'
  layout='vertical'         // Override provider layout
/>
```

### StandardFormSelect

```typescript
<StandardFormSelect<FormType>
  name='role'
  label='Role'
  placeholder='Select role'
  options={[
    { label: 'Admin', value: 'admin' },
    { label: 'Member', value: 'member' },
  ]}
  emptyOptionLabel='None'   // Optional empty option
  required
/>
```

### StandardFormField (Composition)

For custom/complex fields:

```typescript
<StandardFormField<FormType>
  name='avatar'
  label='Profile Picture'
  description='Max 5MB'
>
  {({ field, disabled }) => (
    <FileUploader
      value={field.value}
      onChange={field.onChange}
      disabled={disabled}
      accept='image/*'
      maxSize={5 * 1024 * 1024}
    />
  )}
</StandardFormField>
```

### StandardFormError

```typescript
// Displays form.formState.errors.root
<StandardFormError className='mb-4' />

// Set root error
form.setError('root', { message: 'Failed to save. Please try again.' })
```

## Form Setup Pattern

### Basic Form

```typescript
// src/features/profile/components/profile-form.tsx
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  StandardFormProvider,
  StandardFormError,
  StandardFormInput,
} from '@/components/form'
import { profileFormSchema, type ProfileFormHandler } from '../schemas'

export default function ProfileForm() {
  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
    mode: 'onChange',
    defaultValues: {
      firstName: '',
      lastName: '',
      email: '',
    },
  })

  const onSubmit = async (data: ProfileFormHandler) => {
    // Handle submission
  }

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      <StandardFormError />
      <StandardFormInput<ProfileFormHandler>
        name='firstName'
        label='First Name'
        required
      />
      <StandardFormInput<ProfileFormHandler>
        name='lastName'
        label='Last Name'
        required
      />
      <StandardFormInput<ProfileFormHandler>
        name='email'
        label='Email'
        type='email'
        required
      />
      <Button type='submit' disabled={form.formState.isSubmitting}>
        Save
      </Button>
    </StandardFormProvider>
  )
}
```

### Form with Server Data

```typescript
export default function ProfileForm() {
  const profileQuery = trpc.profile.getByCurrentUser.useQuery()

  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
    mode: 'onChange',
    defaultValues: {
      firstName: '',
      lastName: '',
    },
  })

  const { reset } = form

  // Sync server data to form
  useEffect(() => {
    if (profileQuery.data) {
      reset({
        firstName: profileQuery.data.firstName ?? '',
        lastName: profileQuery.data.lastName ?? '',
      })
    }
  }, [profileQuery.data, reset])

  if (profileQuery.isLoading) {
    return <ProfileFormSkeleton />
  }

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      {/* ... */}
    </StandardFormProvider>
  )
}
```

### Form with Mutation

```typescript
export default function ProfileForm() {
  const trpcUtils = trpc.useUtils()
  const updateMut = trpc.profile.update.useMutation()
  const router = useRouter()
  const catchErrorToast = useCatchErrorToast()

  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
  })

  const onSubmit = async (data: ProfileFormHandler) => {
    return catchErrorToast(
      async () => {
        await updateMut.mutateAsync(data)
        await trpcUtils.profile.getByCurrentUser.invalidate()
        router.push(appRoutes.dashboard)
      },
      { description: 'Profile updated successfully!' },
    )
  }

  const onError = (errors: FieldErrors<ProfileFormHandler>) => {
    // Handle validation errors (optional)
    console.error('Validation errors:', errors)
  }

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit} onError={onError}>
      {/* ... */}
    </StandardFormProvider>
  )
}
```

## Layout Patterns

### Vertical (Default)

```typescript
<StandardFormProvider form={form} onSubmit={onSubmit} layout='vertical'>
  <StandardFormInput name='name' label='Name' />
</StandardFormProvider>

// Renders:
// Label
// [  Input  ]
```

### Horizontal

```typescript
<StandardFormProvider form={form} onSubmit={onSubmit} layout='horizontal'>
  <StandardFormInput name='name' label='Name' />
</StandardFormProvider>

// Renders:
// Label     [  Input  ]
```

### Mixed Layout

```typescript
<StandardFormProvider form={form} onSubmit={onSubmit} layout='horizontal'>
  <StandardFormInput name='name' label='Name' />
  <StandardFormInput name='email' label='Email' />

  {/* Override to vertical for this field */}
  <StandardFormField name='bio' label='Bio' layout='vertical'>
    {({ field }) => <Textarea {...field} />}
  </StandardFormField>
</StandardFormProvider>
```

## Validation Modes

| Mode        | When Validates         | Use Case           |
| ----------- | ---------------------- | ------------------ |
| `onChange`  | Every keystroke        | Real-time feedback |
| `onBlur`    | On field blur          | Less aggressive    |
| `onSubmit`  | Only on submit         | Simple forms       |
| `onTouched` | On blur, then onChange | Balanced           |

```typescript
const form = useForm<FormType>({
  resolver: zodResolver(schema),
  mode: "onChange",
});
```

## Button State

```typescript
const {
  formState: { isDirty, isSubmitting, isValid },
} = form

<Button
  type='submit'
  disabled={isSubmitting || !isDirty || !isValid}
  isLoading={isSubmitting}
>
  Save
</Button>
```

## File Upload

```typescript
// Schema
export const formSchema = z.object({
  imageAsset: z.object({
    file: z.instanceof(File).optional(),
    url: z.string(),
  }),
})

// Form
<StandardFormField<FormType> name='imageAsset' label='Image'>
  {({ field }) => (
    <FileDropzone
      value={field.value}
      onChange={field.onChange}
      accept={{ 'image/*': ['.jpg', '.png'] }}
      maxSize={5 * 1024 * 1024}
    />
  )}
</StandardFormField>

// Submission
const onSubmit = async ({ imageAsset, ...data }: FormType) => {
  const result = await createMut.mutateAsync(data)

  if (imageAsset.file) {
    const formData = new FormData()
    formData.append('entityId', result.id)
    formData.append('image', imageAsset.file)
    await uploadMut.mutateAsync(formData)
  }
}
```

## Conventions Summary

| Convention         | Standard                                        |
| ------------------ | ----------------------------------------------- |
| Schema location    | `features/<feature>/schemas.ts`                 |
| Schema composition | DTO `.merge()` with UI schemas                  |
| Type inference     | `z.infer<typeof schema>`                        |
| Form wrapper       | `StandardFormProvider`                          |
| Field components   | `StandardFormInput`, `StandardFormSelect`, etc. |
| Complex fields     | `StandardFormField` with children               |
| Error display      | `StandardFormError` for root errors             |
| Layout             | Provider default + per-field override           |
| Validation mode    | `onChange` for real-time feedback               |

## Checklist

- [ ] Schema defined in `schemas.ts`, composed from DTOs
- [ ] Form uses `zodResolver(schema)`
- [ ] Form wrapped in `StandardFormProvider`
- [ ] `StandardFormError` included for API errors
- [ ] Button disabled when `!isDirty || !isValid || isSubmitting`
- [ ] Loading state shows skeleton
- [ ] Server data synced via `useEffect` + `reset`
- [ ] Mutations invalidate relevant queries
