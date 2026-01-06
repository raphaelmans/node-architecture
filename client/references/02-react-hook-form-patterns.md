# React Hook Form Patterns

This guide covers form implementation patterns using react-hook-form with Zod validation.

> **Note:** For new forms, prefer using the [Standard Form Components](./09-standard-form-components.md) which provide a cleaner abstraction over these patterns.

---

## Dependencies

```json
{
  "react-hook-form": "^7.54.2",
  "@hookform/resolvers": "^3.10.0",
  "zod": "^3.25.8"
}
```

---

## Basic Form Setup

```typescript
// src/features/profile/components/profile-form.tsx
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Form } from '@/components/ui/form'
import { profileFormSchema, type ProfileFormHandler } from '../schemas'

export default function ProfileForm() {
  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
    mode: 'onChange',  // Validation strategy
    defaultValues: {
      firstName: '',
      lastName: '',
      email: '',
      bio: '',
      // Always provide complete default values
    },
  })

  const {
    reset,
    formState: { isDirty, isSubmitting, isValid },
  } = form

  const onSubmit = async (data: ProfileFormHandler) => {
    // Handle submission
  }

  const onSubmitError = (errors: FieldErrors<ProfileFormHandler>) => {
    // Handle validation errors
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit, onSubmitError)}>
        {/* Form fields */}
        <Button
          type='submit'
          disabled={isSubmitting || !isDirty || !isValid}
          isLoading={isSubmitting}
        >
          Submit
        </Button>
      </form>
    </Form>
  )
}
```

---

## Validation Modes

| Mode        | Description                      | Use Case           |
| ----------- | -------------------------------- | ------------------ |
| `onChange`  | Validate on every change         | Real-time feedback |
| `onBlur`    | Validate when field loses focus  | Less aggressive UX |
| `onSubmit`  | Validate only on submit          | Simple forms       |
| `onTouched` | Validate on blur, then on change | Balanced approach  |
| `all`       | Validate on blur and change      | Maximum feedback   |

```typescript
const form = useForm<FormType>({
  resolver: zodResolver(schema),
  mode: 'onChange', // When to validate
  reValidateMode: 'onChange', // When to re-validate after error
})
```

---

## Form Context Provider Pattern

The `Form` component wraps `FormProvider` to share form state:

```typescript
// src/components/ui/form.tsx
import { FormProvider } from 'react-hook-form'

const Form = FormProvider  // Re-export

// Usage
<Form {...form}>
  <form onSubmit={form.handleSubmit(onSubmit)}>
    <ChildFieldComponent />  {/* Can access form via useFormContext */}
  </form>
</Form>
```

---

## Field Component Pattern

### Basic Field Component

```typescript
// src/features/profile/components/profile-form-fields.tsx
import { useFormContext } from 'react-hook-form'
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import type { ProfileFormHandler } from '../schemas'

export function ProfileFirstNameField() {
  const { control } = useFormContext<ProfileFormHandler>()

  return (
    <FormField
      control={control}
      name='firstName'  // Type-safe, autocompleted
      render={({ field }) => (
        <FormItem>
          <FormLabel>First Name</FormLabel>
          <FormControl>
            <Input placeholder='John' {...field} />
          </FormControl>
          <FormMessage />  {/* Auto-displays validation errors */}
        </FormItem>
      )}
    />
  )
}
```

### Field with Description

```typescript
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
          <FormDescription>
            Maximum 1000 characters
          </FormDescription>
          <FormMessage />
        </FormItem>
      )}
    />
  )
}
```

### Read-only Field

```typescript
export function ProfileEmailField() {
  const { control } = useFormContext<ProfileFormHandler>()

  return (
    <FormField
      control={control}
      name='email'
      render={({ field }) => (
        <FormItem>
          <FormLabel>Email</FormLabel>
          <FormControl>
            <div className='relative flex items-center'>
              <Lock className='absolute left-2 h-4 w-4 text-muted-foreground' />
              <Input readOnly {...field} className='pl-8' />
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

## Complex Field Patterns

### File Upload Field

```typescript
export function ProfileImageField() {
  const { control, watch, setValue } = useFormContext<ProfileFormHandler>()
  const currentImageUrl = watch('imageAsset.url')
  const errorToast = useErrorToast()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      // Validate file size
      if (!validateFileSize(file, FILE_SIZE_LIMITS.PROFILE_IMAGE)) {
        errorToast({ description: 'File too large' })
        return
      }

      // Update form with file
      setValue('imageAsset.file', file, {
        shouldDirty: true,
        shouldTouch: true,
        shouldValidate: true,
      })

      // Create preview URL
      setValue('imageAsset.url', URL.createObjectURL(file), {
        shouldDirty: true,
        shouldTouch: true,
        shouldValidate: true,
      })
    }
  }, [setValue, errorToast])

  const { getRootProps, getInputProps, open } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxFiles: 1,
    maxSize: FILE_SIZE_LIMITS.PROFILE_IMAGE,
  })

  const removeImage = useCallback(() => {
    setValue('imageAsset.file', undefined, {
      shouldDirty: true,
      shouldTouch: true,
      shouldValidate: true,
    })
    setValue('imageAsset.url', '', {
      shouldDirty: true,
      shouldTouch: true,
      shouldValidate: true,
    })
  }, [setValue])

  return (
    <FormField
      control={control}
      name='imageAsset.url'
      render={() => (
        <FormItem>
          <FormLabel>Profile Picture</FormLabel>
          <FormControl>
            <div {...getRootProps()}>
              <input {...getInputProps()} />
              <Avatar>
                <AvatarImage src={currentImageUrl} />
                <AvatarFallback><ImageIcon /></AvatarFallback>
              </Avatar>
              {currentImageUrl && (
                <Button type='button' onClick={removeImage}>
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

### Select Field with Remote Data

```typescript
export function ProfileCompanyField() {
  const { control, watch } = useFormContext<ProfileFormHandler>()
  const companyId = watch('companyId')

  const companyQuery = trpc.company.getById.useQuery(
    { id: companyId ?? '' },
    { enabled: !!companyId }
  )

  return (
    <FormField
      control={control}
      name='companyId'
      render={() => (
        <FormItem>
          <FormLabel>Company</FormLabel>
          <FormControl>
            <div className='flex items-center'>
              {companyQuery.isPending && <Skeleton />}
              {companyQuery.isSuccess && (
                <Link href={appRoutes.company.base}>
                  {companyQuery.data?.name}
                </Link>
              )}
              {companyQuery.isError && (
                <span className='text-red-500'>Error</span>
              )}
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

## Form Data Reset from Server

```typescript
const profileQuery = trpc.profile.getByCurrentUser.useQuery()

useEffect(() => {
  if (profileQuery.data) {
    reset({
      firstName: profileQuery.data.firstName ?? '',
      lastName: profileQuery.data.lastName ?? '',
      email: profileQuery.data.email,
      bio: profileQuery.data.bio ?? '',
      // Map server data to form shape
      imageAsset: {
        file: undefined,
        url: profileQuery.data.profile_img ?? '',
      },
    })
  }
}, [profileQuery.data, reset])
```

---

## Error Handling

### Form-level Error Handler

```typescript
const errorToast = useErrorToast()

const onSubmitError = (errors: FieldErrors<ProfileFormHandler>) => {
  errorToast({
    description: Object.values(errors)
      .map(error => error.message)
      .join(', '),
    variant: 'destructive',
  })
}

<form onSubmit={form.handleSubmit(onSubmit, onSubmitError)}>
```

### Submission Error Handling

```typescript
const catchErrorToast = useCatchErrorToast()

const onSubmit = async (data: ProfileFormHandler) => {
  return catchErrorToast(
    async () => {
      await mutation.mutateAsync(data)
      // Success handling
    },
    {
      description: 'Profile updated successfully!',
    },
  )
}
```

---

## Button State Management

```typescript
const {
  formState: { isDirty, isSubmitting, isValid },
} = form

// Disable when:
// - Currently submitting
// - No changes made (not dirty)
// - Form is invalid
const isSubmitBtnDisabled = isSubmitting || !isDirty || !isValid
const isSubmitBtnLoading = isSubmitting

<Button
  type='submit'
  disabled={isSubmitBtnDisabled}
  isLoading={isSubmitBtnLoading}
>
  Update Profile
</Button>
```

---

## setValue Options

When manually setting values, always trigger validation:

```typescript
setValue('fieldName', value, {
  shouldDirty: true, // Mark form as dirty
  shouldTouch: true, // Mark field as touched
  shouldValidate: true, // Trigger validation
})
```

---

## File Structure

```
src/features/<feature>/
├── components/
│   ├── <feature>-form.tsx         # Form container (business logic)
│   └── <feature>-form-fields.tsx  # Field components (presentation)
└── schemas.ts                     # Zod schemas + types
```

---

## Standard Form Components (Recommended)

For new forms, use the standardized components for less boilerplate:

```typescript
import {
  StandardFormProvider,
  StandardFormError,
  StandardFormInput,
  StandardFormSelect,
} from '@/components/form'

export default function ProfileForm() {
  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
  })

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      <StandardFormError />
      <StandardFormInput<ProfileFormHandler> name='firstName' label='First Name' required />
      <StandardFormSelect<ProfileFormHandler> name='status' label='Status' options={statusOptions} />
      <Button type='submit'>Submit</Button>
    </StandardFormProvider>
  )
}
```

See [09-standard-form-components.md](./09-standard-form-components.md) for full documentation.
