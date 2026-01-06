# Client-Side Architecture Analysis

This document provides an overview of the client-side architecture patterns used in this codebase. For detailed implementation guides, see the individual documents in the `guides/` directory.

---

## Detailed Guides

| Guide                                                                     | Description                                      |
| ------------------------------------------------------------------------- | ------------------------------------------------ |
| [01-zod-schema-architecture.md](./guides/01-zod-schema-architecture.md)   | Three-layer schema strategy (DB → DTO → Feature) |
| [02-react-hook-form-patterns.md](./guides/02-react-hook-form-patterns.md) | Form setup, field components, validation         |
| [03-tanstack-query-trpc.md](./guides/03-tanstack-query-trpc.md)           | Data fetching, mutations, cache management       |
| [04-shadcn-tailwind.md](./guides/04-shadcn-tailwind.md)                   | UI components, styling patterns                  |
| [05-component-separation.md](./guides/05-component-separation.md)         | Business vs presentation components              |
| [06-nuqs-url-state.md](./guides/06-nuqs-url-state.md)                     | URL query parameter state management             |
| [07-dev-tools.md](./guides/07-dev-tools.md)                               | Development tools configuration                  |
| [08-file-tree-architecture.md](./guides/08-file-tree-architecture.md)     | Directory structure and organization             |
| [09-standard-form-components.md](./guides/09-standard-form-components.md) | Standardized form component abstraction          |
| [10-zustand-state.md](./guides/10-zustand-state.md)                       | Client-side state management with Zustand        |
| [11-environment-variables.md](./guides/11-environment-variables.md)       | Type-safe env vars with @t3-oss/env-nextjs       |
| [12-date-handling.md](./guides/12-date-handling.md)                       | Date manipulation with date-fns                  |
| [13-file-upload.md](./guides/13-file-upload.md)                           | File uploads with tRPC + zod-form-data           |

> **Note:** The `src/lib/**` directory structure is **reference only** and most likely to change based on your backend architecture, ORM choice, and API layer preferences. The patterns within (DTOs, schemas, tRPC setup) are more important than the exact file locations.

---

## 1. Technology Stack Overview

| Category      | Technology                     | Version       | Purpose                 |
| ------------- | ------------------------------ | ------------- | ----------------------- |
| Framework     | Next.js                        | 15.1.4        | App Router, RSC         |
| React         | React                          | 19.0.0        | UI Library              |
| Validation    | Zod                            | 3.25.8        | Schema validation       |
| Forms         | react-hook-form                | 7.54.2        | Form state management   |
| Form Resolver | @hookform/resolvers            | 3.10.0        | Zod-RHF bridge          |
| Data Fetching | @tanstack/react-query          | 5.64.2        | Server state management |
| API Layer     | tRPC                           | 11.0.0-rc.708 | End-to-end typesafe API |
| URL State     | nuqs                           | 2.3.0         | URL query state         |
| UI Components | shadcn/ui + Radix              | various       | Component library       |
| Styling       | Tailwind CSS                   | 3.4.17        | Utility-first CSS       |
| Client State  | Zustand                        | 5.0.3         | Global client state     |
| Dev Tools     | @tanstack/react-query-devtools | 5.62.16       | Query debugging         |

---

## 2. Zod Schema Architecture

### 2.1 Schema Layering Strategy

The codebase uses a **three-layer schema architecture**:

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Database Schemas (Drizzle-Zod)               │
│  Location: src/lib/core/schemas/                        │
│  Purpose: Database table representations                │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 2: DTOs (Data Transfer Objects)                  │
│  Location: src/lib/core/dtos/                           │
│  Purpose: API contracts, validation at boundaries       │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Feature Schemas (Form Handlers)               │
│  Location: src/features/<feature>/schemas.ts            │
│  Purpose: UI-specific validation, form composition      │
└─────────────────────────────────────────────────────────┘
```

### 2.2 DTO Pattern (`src/lib/core/dtos/`)

DTOs define the contract between client and server:

```typescript
// src/lib/core/dtos/profile-dtos.ts
import { z } from 'zod'
import { zfd } from 'zod-form-data'

// Simple DTO for query params
export const getProfileByIdDto = z.object({
  id: z.string(),
})

// DTO with reusable schemas
export const updateProfileDtoSchema = z.object({
  firstName: nameSchema,
  lastName: nameSchema,
  email: z.string(),
  xHandle: handleSchema,
  linkedInUrl: personalLinkedInUrlSchema,
  bio: bioSchema,
}) satisfies z.ZodType<UpdateProfile> // Type assertion for safety

// FormData DTO (for file uploads)
export const profileImageUploadDtoSchema = zfd.formData({
  profileImage: zfd.file(),
  profileId: zfd.text(),
})

// Type exports
export type UpdateProfileDto = z.infer<typeof updateProfileDtoSchema>
```

**Key Patterns:**

- Use `satisfies z.ZodType<T>` for type safety with existing types
- Use `zod-form-data` (`zfd`) for FormData payloads
- Export both schema and inferred type
- Reuse primitive schemas (`nameSchema`, `handleSchema`)

### 2.3 Feature Schema Composition (`src/features/<feature>/schemas.ts`)

Feature schemas compose DTOs with UI-specific additions:

```typescript
// src/features/profile/schemas.ts
import z from 'zod'
import { updateProfileDtoSchema } from '@/lib/core/dtos/profile-dtos'
import { professionalProfileFormSchema } from '../professional-profile/schemas'
import { imageUploadSchema } from '@/lib/core/common-schemas'

// Compose multiple schemas for form handling
export const profileFormSchema = updateProfileDtoSchema
  .merge(professionalProfileFormSchema) // Cross-feature composition
  .merge(imageUploadSchema) // UI-specific (file handling)

export type ProfileFormHandler = z.infer<typeof profileFormSchema>
```

**Key Pattern: Schema Composition**

- DTOs stay pure (API contract)
- Feature schemas add UI concerns (files, computed fields)
- Use `.merge()` to combine related schemas

---

## 3. React Hook Form Integration

### 3.1 Form Setup Pattern

```typescript
// src/features/profile/components/profile-form.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { profileFormSchema, type ProfileFormHandler } from '../schemas'

const form = useForm<ProfileFormHandler>({
  resolver: zodResolver(profileFormSchema),
  mode: 'onChange', // Validate on every change
  defaultValues: {
    firstName: '',
    lastName: '',
    // ... complete default values matching schema
  },
})
```

### 3.2 Form Context Provider Pattern

The form uses shadcn's `Form` component which wraps `FormProvider`:

```typescript
// src/components/ui/form.tsx
const Form = FormProvider  // Re-export for consistency

// Usage in feature component
import { Form } from '@/components/ui/form'

return (
  <Form {...form}>
    <form onSubmit={form.handleSubmit(onSubmit, onSubmitError)}>
      {/* Form fields use context */}
    </form>
  </Form>
)
```

### 3.3 Field Component Pattern

Field components are **presentation components** that consume form context:

```typescript
// src/features/profile/components/profile-form-fields.tsx
import { useFormContext } from 'react-hook-form'
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form'
import type { ProfileFormHandler } from '../schemas'

export function ProfileFirstNameField() {
  const { control } = useFormContext<ProfileFormHandler>()

  return (
    <FormField
      control={control}
      name='firstName'  // Type-safe from ProfileFormHandler
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

**Key Benefits:**

- Fields are decoupled from form logic
- Type-safe field names via generic
- Reusable across forms with same schema
- Validation messages are automatic

### 3.4 Complex Field Pattern (File Upload)

```typescript
export function ProfileImageField() {
  const { control, watch, setValue } = useFormContext<ProfileFormHandler>()
  const currentImageUrl = watch('imageAsset.url')

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (file) {
        // Manual setValue with validation triggers
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
    },
    [setValue],
  )

  // ... dropzone integration
}
```

### 3.5 Form Data Reset from Server

```typescript
useEffect(() => {
  if (profileQuery.data) {
    reset({
      firstName: profileQuery.data.firstName ?? profileQuery.data.name,
      email: profileQuery.data.email,
      // ... map server data to form shape
    })
  }
}, [profileQuery.data, reset])
```

---

## 4. TanStack Query + tRPC Integration

### 4.1 tRPC Client Setup

```typescript
// src/common/providers/trpc-provider.tsx
import { createTRPCReact } from '@trpc/react-query'
import { httpBatchLink, splitLink, isNonJsonSerializable } from '@trpc/client'
import type { AppRouter } from '@/lib/trpc'

export const trpc = createTRPCReact<AppRouter>()

// Singleton pattern for QueryClient
let clientQueryClientSingleton: QueryClient
function getQueryClient() {
  if (typeof window === 'undefined') return makeQueryClient()
  return (clientQueryClientSingleton ??= makeQueryClient())
}

// Split link for FormData vs JSON
const trpcClient = trpc.createClient({
  links: [
    splitLink({
      condition: op => isNonJsonSerializable(op.input),
      true: httpLink({ transformer: new FormDataTransformer() }),
      false: httpBatchLink({ transformer: superjson }),
    }),
  ],
})
```

### 4.2 Query Client Configuration

```typescript
// src/lib/trpc/query-client.ts
export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30 * 1000, // 30 seconds
      },
      dehydrate: {
        serializeData: superjson.serialize,
        shouldDehydrateQuery: query =>
          defaultShouldDehydrateQuery(query) || query.state.status === 'pending',
      },
      hydrate: {
        deserializeData: superjson.deserialize,
      },
    },
  })
}
```

### 4.3 Query Patterns in Components

```typescript
// Dependent queries with enabled flag
const profileQuery = trpc.profile.getByCurrentUser.useQuery(
  {
    signedAssets: true,
  },
  {
    retry: (attempt, error) => {
      if (utils.isTRPCNotFoundError(error)) return false
      return attempt <= 3
    },
  },
)

const professionalProfileQuery = trpc.professionalProfile.getByProfileId.useQuery(
  { profileId: profileQuery.data?.id ?? '' },
  { enabled: !!profileQuery.data?.id }, // Wait for profile
)
```

### 4.4 Mutation with Cache Invalidation

```typescript
const trpcUtils = trpc.useUtils()

const onSubmit = async (data: ProfileFormHandler) => {
  const result = await profileMut.mutateAsync(data)

  // Invalidate related queries
  await Promise.all([
    trpcUtils.profile.getByCurrentUser.invalidate(),
    trpcUtils.professionalProfile.getByProfileId.invalidate({
      profileId: result.id,
    }),
  ])
}
```

---

## 5. shadcn/ui + Tailwind Architecture

### 5.1 Component Hierarchy

```
src/components/
├── ui/                    # Primitive components (shadcn)
│   ├── button.tsx
│   ├── input.tsx
│   ├── form.tsx          # RHF integration
│   └── ...
└── custom-ui/            # Composite business components
    └── ...
```

### 5.2 Form Component Structure (shadcn)

```typescript
// src/components/ui/form.tsx
// Provides: Form, FormField, FormItem, FormLabel, FormControl, FormMessage

// FormField wraps RHF Controller
const FormField = <TFieldValues, TName>({ ...props }: ControllerProps) => (
  <FormFieldContext.Provider value={{ name: props.name }}>
    <Controller {...props} />
  </FormFieldContext.Provider>
)

// useFormField hook for accessing field state
const useFormField = () => {
  const fieldContext = useContext(FormFieldContext)
  const { getFieldState, formState } = useFormContext()
  return {
    name: fieldContext.name,
    ...getFieldState(fieldContext.name, formState),
  }
}
```

---

## 6. Presentation vs Business Component Separation

### 6.1 Component Types

| Type                   | Location                             | Responsibility                            |
| ---------------------- | ------------------------------------ | ----------------------------------------- |
| **UI Primitives**      | `src/components/ui/`                 | Atomic, stateless, generic                |
| **Custom UI**          | `src/components/custom-ui/`          | Composed primitives, app-specific styling |
| **Feature Components** | `src/features/<feature>/components/` | Business logic, data fetching             |
| **Field Components**   | `*-form-fields.tsx`                  | Form context consumers, presentation      |

### 6.2 Feature Component Structure

```
src/features/profile/
├── components/
│   ├── profile-form.tsx           # Business: queries, mutations, logic
│   └── profile-form-fields.tsx    # Presentation: field rendering
├── hooks.ts                       # Custom hooks
└── schemas.ts                     # Zod schemas
```

### 6.3 Business Component Example

```typescript
// profile-form.tsx (Business)
export default function ProfileForm() {
  // Data fetching
  const profileQuery = trpc.profile.getByCurrentUser.useQuery()

  // Form setup with schema
  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
  })

  // Mutations
  const profileMut = trpc.profile.upsertUserProfile.useMutation()

  // Business logic
  const onSubmit = async (data) => { /* ... */ }

  // Render with presentation components
  return (
    <Form {...form}>
      <ProfileFirstNameField />  {/* Presentation */}
      <ProfileLastNameField />   {/* Presentation */}
    </Form>
  )
}
```

### 6.4 Presentation Component Example

```typescript
// profile-form-fields.tsx (Presentation)
export function ProfileFirstNameField() {
  const { control } = useFormContext<ProfileFormHandler>()

  // Pure rendering, no business logic
  return (
    <FormField
      control={control}
      name='firstName'
      render={({ field }) => (
        <FormItem>
          <FormLabel>First Name</FormLabel>
          <FormControl>
            <Input {...field} />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  )
}
```

---

## 7. nuqs URL State Management

### 7.1 Parser Pattern

```typescript
// src/features/landing/hooks.ts
import { parseAsStringLiteral, useQueryState } from 'nuqs'

const landingStates = ['login', 'signup'] as const
type LandingState = (typeof landingStates)[number]

export const useQueryLandingState = () => {
  return useQueryState(
    'step', // URL param name
    parseAsStringLiteral(landingStates).withOptions({
      history: 'push', // or 'replace'
    }),
  )
}
```

### 7.2 Centralized Query Params

```typescript
// src/common/constants.ts
export const appQueryParams = {
  error: 'error',
  step: 'step',
  // ... other param names
}
```

### 7.3 Usage Pattern

```typescript
const [landingState, setLandingState] = useQueryLandingState()

// Read: landingState is 'login' | 'signup' | null
// Write: setLandingState('signup') updates URL to ?step=signup
```

---

## 8. Dev Tools Configuration

### 8.1 React Query DevTools

```typescript
// src/common/providers/trpc-provider.tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

export function TRPCProvider({ children }) {
  return (
    <trpc.Provider client={trpcClient} queryClient={queryClient}>
      <QueryClientProvider client={queryClient}>
        {children}
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </trpc.Provider>
  )
}
```

### 8.2 Future: React Scan / React Grab

When adding render performance tools:

```typescript
// Recommended setup for react-scan or similar
if (process.env.NODE_ENV === 'development') {
  // Dynamic import to avoid production bundle
  import('react-scan').then(({ scan }) => {
    scan({ enabled: true })
  })
}
```

---

## 9. File Tree Architecture

```
src/
├── app/                          # Next.js App Router
│   ├── (api)/                    # API routes
│   │   └── api/trpc/[...trpc]/   # tRPC handler
│   ├── (authenticated)/          # Protected routes
│   │   └── <route>/page.tsx
│   └── (guest)/                  # Public routes
│       └── <route>/page.tsx
│
├── common/                       # App-wide shared code
│   ├── providers/                # React context providers
│   │   └── trpc-provider.tsx
│   ├── hooks.ts                  # Shared hooks
│   ├── constants.ts              # Global constants
│   ├── app-routes.ts             # Route definitions
│   ├── utils.ts                  # Utility functions
│   └── types.ts                  # Shared types
│
├── components/                   # Shared UI components
│   ├── ui/                       # shadcn primitives
│   │   ├── button.tsx
│   │   ├── form.tsx              # RHF integration
│   │   └── ...
│   └── custom-ui/                # Composed components
│
├── features/                     # Feature modules
│   └── <feature>/
│       ├── components/
│       │   ├── <feature>-form.tsx         # Business component
│       │   └── <feature>-form-fields.tsx  # Presentation fields
│       ├── hooks.ts              # Feature-specific hooks
│       └── schemas.ts            # Zod form schemas
│
├── hooks/                        # Global React hooks
│   └── use-toast.ts
│
└── lib/                          # Core logic & external integrations
    ├── core/
    │   ├── dtos/                 # Data Transfer Objects
    │   │   └── <entity>-dtos.ts
    │   ├── schemas/              # Database/entity schemas
    │   ├── common-schemas.ts     # Reusable schema primitives
    │   └── constants.ts
    │
    ├── trpc/
    │   ├── init.ts               # tRPC server setup
    │   ├── client.ts             # tRPC client export
    │   ├── query-client.ts       # QueryClient factory
    │   └── transformers.ts       # Custom transformers
    │
    ├── env/                      # Environment config
    └── utils.ts
```

---

## 10. Key Architectural Decisions Summary

| Decision                         | Rationale                             |
| -------------------------------- | ------------------------------------- |
| **3-layer schemas**              | Separation of concerns: DB → API → UI |
| **DTO consumption in forms**     | Single source of truth for validation |
| **Field components via context** | Reusable, decoupled presentation      |
| **tRPC + React Query**           | End-to-end type safety, caching       |
| **nuqs for URL state**           | Type-safe URL params, SSR-friendly    |
| **shadcn/ui**                    | Composable, unstyled primitives       |
| **Feature-based structure**      | Co-location of related code           |

---

## 11. Checklist for New Repository

- [ ] Set up Zod with `@hookform/resolvers`
- [ ] Configure tRPC with `superjson` transformer
- [ ] Set up QueryClient with appropriate `staleTime`
- [ ] Install shadcn/ui with `form.tsx` component
- [ ] Create `src/lib/core/dtos/` structure
- [ ] Create `src/features/` structure
- [ ] Set up `nuqs` provider
- [ ] Configure React Query DevTools (dev only)
- [ ] Add `FormData` transformer for file uploads
- [ ] Set up Tailwind with shadcn configuration
