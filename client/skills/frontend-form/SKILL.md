---
name: frontend-form
description: Implements forms using StandardForm components with Zod validation and react-hook-form. Use when creating forms, adding form fields, handling form submission, or when the user mentions "form", "input", "validation", "StandardForm".
---

# Form Implementation

## Overview

Forms use a standardized pattern with:
- **Zod** for schema validation
- **react-hook-form** for state management
- **StandardForm** components for consistent UI

```
Schema (Zod) → useForm + zodResolver → StandardFormProvider → StandardForm* fields
```

## Quick Start

### Basic Form Setup

```typescript
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import {
  StandardFormProvider,
  StandardFormError,
  StandardFormInput,
  StandardFormSelect,
} from '@/components/form';

// 1. Define schema
const formSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
  role: z.enum(['admin', 'member']),
});

type FormValues = z.infer<typeof formSchema>;

// 2. Create form component
export function MyForm() {
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    mode: 'onChange',
    defaultValues: {
      name: '',
      email: '',
      role: 'member',
    },
  });

  const onSubmit = async (data: FormValues) => {
    console.log(data);
  };

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      <StandardFormError />
      
      <StandardFormInput<FormValues>
        name="name"
        label="Name"
        placeholder="John Doe"
        required
      />
      
      <StandardFormInput<FormValues>
        name="email"
        label="Email"
        type="email"
        placeholder="john@example.com"
        required
      />
      
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
  );
}
```

## Schema Patterns

### Compose from DTOs

```typescript
// src/features/<feature>/schemas.ts
import { z } from 'zod';
import { CreateUserSchema } from '@/lib/modules/user/dtos/create-user.dto';
import { ImageAssetSchema } from '@/lib/shared/kernel/dtos/common';

// Extend DTO with UI fields
export const userFormSchema = CreateUserSchema.merge(
  z.object({
    confirmPassword: z.string(),
    imageAsset: ImageAssetSchema.optional(),
  })
).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords must match',
  path: ['confirmPassword'],
});

export type UserFormHandler = z.infer<typeof userFormSchema>;
```

### Common Validations

```typescript
const schema = z.object({
  // Required string
  name: z.string().min(1, 'Required'),
  
  // Email
  email: z.string().email('Invalid email'),
  
  // Password with requirements
  password: z.string()
    .min(8, 'At least 8 characters')
    .regex(/[A-Z]/, 'At least one uppercase letter')
    .regex(/[0-9]/, 'At least one number'),
  
  // Optional with default
  nickname: z.string().optional().default(''),
  
  // Enum
  status: z.enum(['active', 'inactive']),
  
  // Number
  age: z.coerce.number().min(0).max(120),
  
  // Date
  birthDate: z.coerce.date(),
  
  // URL
  website: z.string().url().optional().or(z.literal('')),
  
  // Boolean
  acceptTerms: z.boolean().refine((v) => v, 'Must accept terms'),
});
```

## StandardForm Components

### StandardFormProvider

Wraps the form and provides context:

```typescript
<StandardFormProvider
  form={form}                    // UseFormReturn from useForm
  onSubmit={handleSubmit}        // (data) => void | Promise
  onError={handleValidationError} // Optional: (errors) => void
  layout="vertical"              // 'vertical' | 'horizontal' | 'inline'
  className="space-y-4"          // Additional classes
>
  {children}
</StandardFormProvider>
```

### StandardFormError

Displays root-level errors:

```typescript
// Display
<StandardFormError className="mb-4" />

// Set error
form.setError('root', { message: 'Server error occurred' });
```

### StandardFormInput

Text input with all common options:

```typescript
<StandardFormInput<FormType>
  name="email"
  label="Email"
  placeholder="john@example.com"
  type="email"           // 'text' | 'email' | 'password' | 'number' | 'tel' | 'url'
  required               // Shows * indicator
  disabled={isLoading}
  description="Your work email"
  autoComplete="email"
  size="default"         // 'sm' | 'default' | 'lg'
  layout="vertical"      // Override provider layout
/>
```

### StandardFormSelect

Dropdown select:

```typescript
<StandardFormSelect<FormType>
  name="role"
  label="Role"
  placeholder="Select role"
  options={[
    { label: 'Admin', value: 'admin' },
    { label: 'Member', value: 'member' },
  ]}
  emptyOptionLabel="None"  // Optional empty option
  required
/>
```

### StandardFormTextarea

Multi-line text:

```typescript
<StandardFormTextarea<FormType>
  name="bio"
  label="Bio"
  placeholder="Tell us about yourself"
  rows={4}
/>
```

### StandardFormField (Custom Fields)

For custom/complex fields:

```typescript
<StandardFormField<FormType>
  name="avatar"
  label="Profile Picture"
  description="Max 5MB"
>
  {({ field, disabled }) => (
    <FileUploader
      value={field.value}
      onChange={field.onChange}
      disabled={disabled}
      accept="image/*"
      maxSize={5 * 1024 * 1024}
    />
  )}
</StandardFormField>
```

## Layout Options

### Vertical (Default)

```typescript
<StandardFormProvider form={form} onSubmit={onSubmit} layout="vertical">
  <StandardFormInput name="name" label="Name" />
</StandardFormProvider>

// Renders:
// Label
// [  Input  ]
```

### Horizontal

```typescript
<StandardFormProvider form={form} onSubmit={onSubmit} layout="horizontal">
  <StandardFormInput name="name" label="Name" />
</StandardFormProvider>

// Renders:
// Label     [  Input  ]
```

### Mixed Layout

```typescript
<StandardFormProvider form={form} onSubmit={onSubmit} layout="horizontal">
  <StandardFormInput name="name" label="Name" />
  
  {/* Override to vertical */}
  <StandardFormTextarea name="bio" label="Bio" layout="vertical" />
</StandardFormProvider>
```

## Form with Server Data

```typescript
export function EditProfileForm({ profileId }: { profileId: string }) {
  const profileQuery = trpc.profile.getById.useQuery({ id: profileId });

  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
    mode: 'onChange',
    defaultValues: {
      firstName: '',
      lastName: '',
      bio: '',
    },
  });

  const { reset } = form;

  // Sync server data to form
  useEffect(() => {
    if (profileQuery.data) {
      reset({
        firstName: profileQuery.data.firstName ?? '',
        lastName: profileQuery.data.lastName ?? '',
        bio: profileQuery.data.bio ?? '',
      });
    }
  }, [profileQuery.data, reset]);

  if (profileQuery.isLoading) {
    return <FormSkeleton />;
  }

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      {/* fields */}
    </StandardFormProvider>
  );
}
```

## Form Submission

### With Error Toast

```typescript
const catchErrorToast = useCatchErrorToast();

const onSubmit = async (data: FormValues) => {
  return catchErrorToast(
    async () => {
      await mutation.mutateAsync(data);
      await trpcUtils.entity.invalidate();
      router.push(appRoutes.success);
    },
    { description: 'Saved successfully!' },
  );
};
```

### With Form Root Error

```typescript
const onSubmit = async (data: FormValues) => {
  try {
    await mutation.mutateAsync(data);
    toast({ description: 'Success!' });
  } catch (error) {
    if (error instanceof TRPCClientError) {
      form.setError('root', { message: error.message });
    } else {
      toast({ description: 'An error occurred', variant: 'destructive' });
    }
  }
};
```

## Button States

```typescript
const { formState: { isDirty, isSubmitting, isValid } } = form;

<Button
  type="submit"
  disabled={isSubmitting || !isDirty || !isValid}
>
  {isSubmitting ? 'Saving...' : 'Save'}
</Button>
```

## Validation Modes

| Mode | When Validates | Use Case |
|------|----------------|----------|
| `onChange` | Every keystroke | Real-time feedback |
| `onBlur` | On field blur | Less aggressive |
| `onSubmit` | Only on submit | Simple forms |
| `onTouched` | On blur, then onChange | Balanced |

```typescript
const form = useForm<FormType>({
  resolver: zodResolver(schema),
  mode: 'onChange', // Recommended
});
```

## Presentation Components (Form Fields)

Separate form fields into presentation components:

```typescript
// src/features/<feature>/components/<feature>-form-fields.tsx
'use client';

import { StandardFormInput, StandardFormSelect } from '@/components/form';
import type { ProfileFormHandler } from '../schemas';

export function ProfileNameField() {
  return (
    <StandardFormInput<ProfileFormHandler>
      name="name"
      label="Full Name"
      placeholder="John Doe"
      required
    />
  );
}

export function ProfileRoleField() {
  return (
    <StandardFormSelect<ProfileFormHandler>
      name="role"
      label="Role"
      options={[
        { label: 'Admin', value: 'admin' },
        { label: 'Member', value: 'member' },
      ]}
    />
  );
}
```

Then use in business component:

```typescript
// src/features/<feature>/components/<feature>-form.tsx
import { ProfileNameField, ProfileRoleField } from './<feature>-form-fields';

<StandardFormProvider form={form} onSubmit={onSubmit}>
  <StandardFormError />
  <ProfileNameField />
  <ProfileRoleField />
  <Button type="submit">Save</Button>
</StandardFormProvider>
```

## Checklist

- [ ] Schema defined in `schemas.ts`
- [ ] Schema composes from DTOs
- [ ] Form uses `zodResolver(schema)`
- [ ] Form wrapped in `StandardFormProvider`
- [ ] `StandardFormError` included
- [ ] Button disabled when `!isDirty || !isValid || isSubmitting`
- [ ] Loading state shows skeleton
- [ ] Server data synced via `useEffect` + `reset`
- [ ] Mutations invalidate relevant queries

See [references/form-patterns.md](references/form-patterns.md) for advanced patterns.
