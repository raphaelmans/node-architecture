# Forms (react-hook-form + StandardForm)

> React-specific conventions for implementing forms using `react-hook-form` and StandardForm components.

Zod validation conventions live in `client/core/validation-zod.md`.
Server-state ownership patterns live in `client/frameworks/reactjs/server-state-patterns-react.md`.

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

## Form State Subscriptions

React Hook Form uses a Proxy-based subscription model for `formState`. Read every state value needed by the render unconditionally so React Hook Form can subscribe to it. Destructuring is the preferred style because it makes those subscriptions visible:

- ✅ `const { isSubmitting } = form.formState`
- ✅ `disabled={form.formState.isSubmitting}` when it is read unconditionally during render
- ❌ `condition && form.formState.isValid` when `isValid` is not read on every render

**Convention:** Destructure form helpers for readable dependencies and stable effect dependency lists.

- ✅ `const { setValue, reset } = form`
- ❌ `form.setValue(...)`

Helper methods such as `setValue` and `reset` are not Proxy subscriptions; destructuring them is a readability convention, not a correctness requirement.

## Schema Architecture

Examples target Zod 4. `safeExtend` preserves refinements from the shared input schema and prevents incompatible field overwrites.

### Three-Layer Schema Pattern

```
Shared Input Contract
       │
       ▼ .safeExtend(UIOnlySchema.shape)
Form Schema (UI-specific)
       │
       ▼ z.infer<>
TypeScript Type
```

### Form Schema Definition

```typescript
// src/features/profile/schemas.ts

import { z } from "zod";
import {
  UpdateProfileInputSchema,
  type UpdateProfileInput,
} from "@/lib/modules/profile/shared/contracts";
import { ImageUploadSchema } from "@/features/profile/image-upload.schema";

// Compose the shared wire input with UI-only fields.
export const ProfileFormSchema =
  UpdateProfileInputSchema.safeExtend(ImageUploadSchema.shape);

export type ProfileFormShape = z.infer<typeof ProfileFormSchema>;

// UI-only fields never cross the feature API boundary.
export function toUpdateProfileInput({
  imageAsset: _imageAsset,
  ...candidate
}: ProfileFormShape): UpdateProfileInput {
  return UpdateProfileInputSchema.parse(candidate);
}
```

### UI-Only Schema

```typescript
// src/features/profile/image-upload.schema.ts

import { z } from "zod";

// Image asset for file uploads
export const ImageAssetSchema = z.object({
  file: z.instanceof(File).optional(),
  url: z.string(),
});

export const ImageUploadSchema = z.object({
  imageAsset: ImageAssetSchema,
});

export type ImageAsset = z.infer<typeof ImageAssetSchema>;
```

### Cleared Inputs ("" -> undefined)

Controlled inputs often emit an empty string (`""`) when a user clears a field.
If the backend treats the field as optional, normalize `""` to `undefined` at the schema boundary.

**Convention:**

- Use `emptyToUndefined(...)` for optional fields where `""` should mean “not provided”.
- Use `allowEmptyString(...)` only when `""` is a valid *value* (rare).

```typescript
import { z } from "zod";
import { emptyToUndefined, S } from "@/path/to/shared/schemas";

export const ProfileContactFormSchema = z.object({
  displayName: S.profile.displayName,

  // Input might be "" while editing; submit should send undefined
  phoneNumber: emptyToUndefined(S.common.phone.optional()),
});

export type ProfileContactFormShape = z.infer<typeof ProfileContactFormSchema>; // phoneNumber: string | undefined
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
import { ProfileFormSchema, type ProfileFormShape } from '../schemas'

export default function ProfileForm() {
  const form = useForm<ProfileFormShape>({
    resolver: zodResolver(ProfileFormSchema),
    mode: 'onSubmit',
    defaultValues: {
      firstName: '',
      lastName: '',
      email: '',
    },
  })

  const { isSubmitting } = form.formState

  const onSubmit = async (data: ProfileFormShape) => {
    // Handle submission
  }

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      <StandardFormError />
      <StandardFormInput<ProfileFormShape>
        name='firstName'
        label='First Name'
        required
      />
      <StandardFormInput<ProfileFormShape>
        name='lastName'
        label='Last Name'
        required
      />
      <StandardFormInput<ProfileFormShape>
        name='email'
        label='Email'
        type='email'
        required
      />
      <Button type='submit' disabled={isSubmitting}>
        Save
      </Button>
    </StandardFormProvider>
  )
}
```

### Form with Server Data

```typescript
// src/features/profile/components/profile-form.tsx
type UseProfileFormSyncFromQueryDataArgs = {
  data: Profile | undefined;
  reset: UseFormReset<ProfileFormShape>;
};

function useProfileFormSyncFromQueryData({
  data,
  reset,
}: UseProfileFormSyncFromQueryDataArgs) {
  useEffect(() => {
    if (!data) return;

    reset({
      firstName: data.firstName ?? "",
      lastName: data.lastName ?? "",
    });
  }, [data, reset]);
}

export default function ProfileForm() {
  const profileQuery = useQueryProfileCurrent();

  const form = useForm<ProfileFormShape>({
    resolver: zodResolver(ProfileFormSchema),
    mode: "onSubmit",
    defaultValues: {
      firstName: "",
      lastName: "",
    },
  });

  const { isSubmitting } = form.formState;
  const { reset } = form;

  useProfileFormSyncFromQueryData({
    data: profileQuery.data,
    reset,
  });

  if (profileQuery.isLoading) {
    return <ProfileFormSkeleton />;
  }

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      {/* ... */}
    </StandardFormProvider>
  );
}
```

Why this pattern:

- single responsibility: sync logic is isolated in one hook
- testability: `useProfileFormSyncFromQueryData` can be unit tested independently
- explicit sequencing: external data (`query.data`) is the source of truth for edit/update defaults

RHF note (Context7 refs):

- `useForm` supports `values`/`resetOptions`, but this architecture standardizes explicit `reset(...)` on external data changes for clearer submit/refetch sequencing in edit/update forms.

### Async Options + Select Defaults

If a select depends on async options (e.g. provinces/cities) and the record data is also async, do not mount the form until both inputs are ready. Mount a child form with resolved defaults so no render occurs between data readiness and an effect-driven `reset`.

```typescript
function EditScreen() {
  if (!record || !options) return <FormSkeleton />

  return (
    <HydratedForm
      key={record.id}
      defaultValues={resolveDefaults(record, options)}
    />
  )
}

function HydratedForm({ defaultValues }: { defaultValues: FormValues }) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  })

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      {/* ... */}
    </StandardFormProvider>
  )
}
```

If the same mounted form must react continuously to external values, use React Hook Form's reactive `values` option with deliberate `resetOptions`, or retain the dedicated `reset` synchronization hook. Choose one hydration strategy per form.

### Form with Mutation

Two orchestration patterns are valid:

- Hook-owned invalidation (preferred default)
- Component-coordinator sequencing through a named `useMod*Sync` operation (allowed for route-local orchestration)

#### Variant A: Hook-Owned Invalidation (Preferred)

```typescript
// src/features/profile/hooks.ts
export function useMutProfileUpdate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateProfile,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: profileQueryKeys.current() }),
      ]);
    },
  });
}
```

```typescript
// src/features/profile/components/profile-form.tsx
const catchErrorToast = useCatchErrorToast();
const updateMut = useMutProfileUpdate();

const onSubmit = async (data: ProfileFormShape) => {
  const result = await catchErrorToast(
    async () => {
      await updateMut.mutateAsync(toUpdateProfileInput(data));
      router.push(appRoutes.dashboard);
    },
    { description: "Profile updated successfully!" },
  );

  if (!result.ok) return;
};
```

Note:

- If this edit/update form stays on the page, await invalidation of its active query and re-sync defaults when refreshed `query.data` arrives.

#### Variant B: Component-Coordinator Sequencing (Allowed)

```typescript
// src/features/profile/sync.ts
export function useModProfileSync() {
  const queryClient = useQueryClient();

  return {
    invalidateAfterUpdate: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: profileQueryKeys.current() }),
      ]),
  };
}

// src/features/profile/components/profile-form.tsx
export default function ProfileForm() {
  const router = useRouter();
  const catchErrorToast = useCatchErrorToast();

  const profileQuery = useQueryProfileCurrent();
  const updateMut = useMutProfileUpdate();
  const profileSync = useModProfileSync();

  const form = useForm<ProfileFormShape>({
    resolver: zodResolver(ProfileFormSchema),
    mode: "onSubmit",
  });
  const { reset } = form;

  useProfileFormSyncFromQueryData({
    data: profileQuery.data,
    reset,
  });

  const onSubmit = async (data: ProfileFormShape) => {
    const result = await catchErrorToast(
      async () => {
        await updateMut.mutateAsync(toUpdateProfileInput(data));
        await profileSync.invalidateAfterUpdate();
        // Optional route transition:
        // router.push(appRoutes.dashboard);
      },
      { description: "Profile updated successfully!" },
    );

    if (!result.ok) return;
  };

  const onError = (errors: FieldErrors<ProfileFormShape>) => {
    // Optional: show a toast summarizing validation errors.
    // Usually, field-level messages + StandardFormError are enough.
  };

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit} onError={onError}>
      {/* ... */}
    </StandardFormProvider>
  );
}
```

### Edit/Update Success Re-Sync (Recommended Standard)

For edit/update forms that read external data:

1. submit mutation
2. await the named cache-sync operation, which invalidates the active current/detail query
3. let the form-sync hook reset from refreshed `query.data`
4. success toast comes from `useCatchErrorToast` after the async submit pipeline resolves

Rule:

- Do not reset edit/update forms to `EMPTY_DEFAULTS` on success.
- Reset to refreshed external data so UI equals post-refresh server truth.
- Do not call `query.refetch()` after normal active-query invalidation; invalidation already refetches active matches.
- Use explicit `query.refetch()` only when invalidation was configured not to refetch, the target query is disabled/inactive but must refresh immediately, or the flow intentionally skips invalidation.

#### Variant C: Hybrid

Use shared default invalidation in the mutation hook, then expose route-local additions through a named cache-sync hook that the form component sequences.

```typescript
// hook (shared defaults)
export function useMutProfileUpdate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateProfile,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: profileQueryKeys.current() });
    },
  });
}

// sync.ts (route-local cache operation)
export function useModDashboardSync() {
  const queryClient = useQueryClient();
  return {
    invalidateSummary: () =>
      queryClient.invalidateQueries({ queryKey: dashboardQueryKeys.summary() }),
  };
}

// component (route-local sequencing)
const dashboardSync = useModDashboardSync();

const onSubmit = async (data: ProfileFormShape) => {
  await updateMut.mutateAsync(toUpdateProfileInput(data));
  await dashboardSync.invalidateSummary();
  router.push(appRoutes.dashboard);
};
```

#### Scenario Cookbook (Forms)

- Create form: usually Variant A.
- Edit form: Variant A or B depending on route-local orchestration complexity.
- Upload + follow-up mutation: Variant C is often the cleanest split.
- Multi-panel settings screen: coordinator can call multiple `useMut*` hooks and batch invalidation in one place.

### Form Telemetry Ownership

- Reusable completion analytics belong in the successful mutation hook.
- Route/form-specific flow analytics may emit after the complete submit/cache-sync sequence succeeds.
- Validation failures remain UI/form concerns and are not operational errors by default.
- Transport and contract failures are already logged by `clientApi`/`featureApi`; forms must not report them again.
- Forms never import `debug`, Sentry, or analytics vendor SDKs.
- Telemetry delivery never blocks the submit pipeline, toast, reset, or navigation.

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
  mode: "onSubmit",
});
```

## Button State

```typescript
const {
  formState: { isSubmitting },
} = form

<Button
  type='submit'
  disabled={isSubmitting}
  isLoading={isSubmitting}
>
  Save
</Button>
```

### Edit/Update Form Exception (Optional)

For edit/update forms, it can be reasonable to prevent a no-op submit:

```typescript
const {
  formState: { isDirty, isSubmitting },
} = form

<Button type='submit' disabled={isSubmitting || !isDirty} isLoading={isSubmitting}>
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

This two-step flow can partially succeed: the entity may be created even if the upload fails. Make that state explicit in the UX and retry model. If create-plus-upload must be atomic from the user's perspective, expose one server-owned workflow endpoint instead of coordinating two mutations only in the browser.

## Conventions Summary

| Convention         | Standard                                        |
| ------------------ | ----------------------------------------------- |
| Schema location    | `features/<feature>/schemas.ts`                 |
| Schema composition | Shared input `.safeExtend(UIOnlySchema.shape)` + explicit form-to-wire mapper |
| Type inference     | `z.infer<typeof schema>`                        |
| Form wrapper       | `StandardFormProvider`                          |
| Field components   | `StandardFormInput`, `StandardFormSelect`, etc. |
| Complex fields     | `StandardFormField` with children               |
| Error display      | `StandardFormError` for root errors             |
| Layout             | Provider default + per-field override           |
| Validation mode    | `onSubmit` by default                           |

## Checklist

- [ ] Form schema defined in `schemas.ts`, composed from a shared input contract
- [ ] Form uses `zodResolver(schema)`
- [ ] Form wrapped in `StandardFormProvider`
- [ ] `StandardFormError` included for API errors
- [ ] Button disabled only when `isSubmitting` (default)
- [ ] Edit/update forms may add `!isDirty` only for no-op prevention (optional exception)
- [ ] Edit/update submit flow awaits active-query invalidation; explicit refetch is used only for a documented exception
- [ ] Edit/update defaults are re-synced from refreshed `query.data` via a dedicated sync hook
- [ ] UI-only form fields are removed by an explicit form-to-wire mapper before calling the mutation
- [ ] Loading state shows skeleton
- [ ] Server data sync logic is isolated (for example `useProfileFormSyncFromQueryData`)
- [ ] Mutation invalidation strategy chosen (hook-owned, coordinator sequencing through `useMod*Sync`, or hybrid)
- [ ] Multi-key invalidation batched with `Promise.all(...)`
