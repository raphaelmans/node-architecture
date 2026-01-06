---
name: frontend-form
description: Implement forms using StandardForm components with Zod validation and react-hook-form in Next.js projects
---

# Form Implementation

Use this skill when creating forms with validation and submission handling.

## Pattern

```
Schema (Zod) → useForm + zodResolver → StandardFormProvider → StandardForm* fields
```

## Quick Start

```typescript
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import {
  StandardFormProvider,
  StandardFormError,
  StandardFormInput,
  StandardFormSelect,
} from '@/components/form'

// 1. Define schema
const formSchema = z.object({
  name: z.string().min(1, 'Required'),
  email: z.string().email('Invalid email'),
  role: z.enum(['admin', 'member']),
})

type FormValues = z.infer<typeof formSchema>

// 2. Create form
export function MyForm() {
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    mode: 'onChange',
    defaultValues: { name: '', email: '', role: 'member' },
  })

  const onSubmit = async (data: FormValues) => {
    console.log(data)
  }

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      <StandardFormError />
      <StandardFormInput<FormValues> name="name" label="Name" required />
      <StandardFormInput<FormValues> name="email" label="Email" type="email" required />
      <StandardFormSelect<FormValues>
        name="role"
        label="Role"
        options={[
          { label: 'Admin', value: 'admin' },
          { label: 'Member', value: 'member' },
        ]}
      />
      <Button type="submit" disabled={form.formState.isSubmitting}>
        Submit
      </Button>
    </StandardFormProvider>
  )
}
```

## Schema Patterns

### Compose from DTOs

```typescript
import { CreateUserSchema } from '@/lib/modules/user/dtos/create-user.dto'
import { ImageAssetSchema } from '@/lib/shared/kernel/dtos/common'

export const userFormSchema = CreateUserSchema.merge(
  z.object({
    confirmPassword: z.string(),
    imageAsset: ImageAssetSchema.optional(),
  })
).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords must match',
  path: ['confirmPassword'],
})
```

### Common Validations

```typescript
const schema = z.object({
  name: z.string().min(1, 'Required'),
  email: z.string().email('Invalid email'),
  password: z
    .string()
    .min(8, 'At least 8 characters')
    .regex(/[A-Z]/, 'At least one uppercase'),
  age: z.coerce.number().min(0).max(120),
  website: z.string().url().optional().or(z.literal('')),
  acceptTerms: z.boolean().refine((v) => v, 'Must accept terms'),
})
```

## StandardForm Components

### StandardFormProvider

```typescript
<StandardFormProvider
  form={form}
  onSubmit={handleSubmit}
  onError={handleValidationError} // Optional
  layout="vertical" // 'vertical' | 'horizontal'
  className="space-y-4"
>
  {children}
</StandardFormProvider>
```

### StandardFormInput

```typescript
<StandardFormInput<FormType>
  name="email"
  label="Email"
  placeholder="john@example.com"
  type="email" // 'text' | 'email' | 'password' | 'number'
  required
  disabled={isLoading}
  description="Your work email"
/>
```

### StandardFormSelect

```typescript
<StandardFormSelect<FormType>
  name="role"
  label="Role"
  placeholder="Select role"
  options={[
    { label: 'Admin', value: 'admin' },
    { label: 'Member', value: 'member' },
  ]}
  emptyOptionLabel="None" // Optional
  required
/>
```

### StandardFormTextarea

```typescript
<StandardFormTextarea<FormType>
  name="bio"
  label="Bio"
  placeholder="Tell us about yourself"
  rows={4}
/>
```

### StandardFormField (Custom)

```typescript
<StandardFormField<FormType> name="avatar" label="Avatar" description="Max 5MB">
  {({ field, disabled }) => (
    <FileUploader
      value={field.value}
      onChange={field.onChange}
      disabled={disabled}
      accept="image/*"
    />
  )}
</StandardFormField>
```

### StandardFormError

```typescript
<StandardFormError className="mb-4" />

// Set root error
form.setError('root', { message: 'Server error' })
```

## Form with Server Data

```typescript
export function EditForm({ entityId }: { entityId: string }) {
  const entityQuery = trpc.entity.getById.useQuery({ id: entityId })

  const form = useForm<FormHandler>({
    resolver: zodResolver(formSchema),
    mode: 'onChange',
    defaultValues: { name: '', description: '' },
  })

  const { reset } = form

  // Sync server data
  useEffect(() => {
    if (entityQuery.data) {
      reset({
        name: entityQuery.data.name ?? '',
        description: entityQuery.data.description ?? '',
      })
    }
  }, [entityQuery.data, reset])

  if (entityQuery.isLoading) {
    return <FormSkeleton />
  }

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      {/* fields */}
    </StandardFormProvider>
  )
}
```

## Form Submission

### With Error Toast

```typescript
const catchErrorToast = useCatchErrorToast()

const onSubmit = async (data: FormValues) => {
  return catchErrorToast(
    async () => {
      await mutation.mutateAsync(data)
      await trpcUtils.entity.invalidate()
      router.push(appRoutes.success)
    },
    { description: 'Saved successfully!' }
  )
}
```

### File Upload

```typescript
const onSubmit = async ({ imageAsset, ...data }: FormType) => {
  const result = await createMut.mutateAsync(data)

  if (imageAsset?.file) {
    const formData = new FormData()
    formData.append('entityId', result.id)
    formData.append('image', imageAsset.file)
    await uploadMut.mutateAsync(formData)
  }
}
```

## Button States

```typescript
const {
  formState: { isDirty, isSubmitting, isValid },
} = form

<Button type="submit" disabled={isSubmitting || !isDirty || !isValid}>
  {isSubmitting ? 'Saving...' : 'Save'}
</Button>
```

## Presentation Components

Separate form fields for reuse:

```typescript
// <feature>-form-fields.tsx
export function ProfileNameField() {
  return (
    <StandardFormInput<ProfileFormHandler>
      name="name"
      label="Name"
      placeholder="John Doe"
      required
    />
  )
}

// <feature>-form.tsx
<StandardFormProvider form={form} onSubmit={onSubmit}>
  <StandardFormError />
  <ProfileNameField />
  <Button type="submit">Save</Button>
</StandardFormProvider>
```

## Checklist

- [ ] Schema in `schemas.ts` (composes from DTOs)
- [ ] Form uses `zodResolver(schema)`
- [ ] Form wrapped in `StandardFormProvider`
- [ ] `StandardFormError` included
- [ ] Button disabled when `!isDirty || !isValid || isSubmitting`
- [ ] Loading shows skeleton
- [ ] Server data synced via `useEffect` + `reset`
- [ ] Mutations invalidate relevant queries
