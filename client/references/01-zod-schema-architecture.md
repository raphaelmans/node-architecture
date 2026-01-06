# Zod Schema Architecture

This guide covers the three-layer schema strategy used for type-safe validation across the stack.

---

## Overview

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

---

## Layer 1: Database Schemas

Generated from Drizzle ORM using `drizzle-zod`:

```typescript
// src/lib/core/schemas/profile.ts
import { createInsertSchema, createSelectSchema } from 'drizzle-zod'
import { profiles } from '@/lib/extern/db/schema'

export const insertProfileSchema = createInsertSchema(profiles)
export const selectProfileSchema = createSelectSchema(profiles)

export type InsertProfile = z.infer<typeof insertProfileSchema>
export type Profile = z.infer<typeof selectProfileSchema>
```

**Purpose:**

- Direct mapping to database tables
- Used in repositories and data layer
- Source of truth for entity shape

---

## Layer 2: DTOs (Data Transfer Objects)

DTOs define the API contract between client and server:

```typescript
// src/lib/core/dtos/profile-dtos.ts
import { z } from 'zod'
import { zfd } from 'zod-form-data'
import { insertProfileSchema } from '../schemas/profile'
import { nameSchema, handleSchema, personalLinkedInUrlSchema } from '../common-schemas'

// Query DTOs (input validation)
export const getProfileByIdDto = z.object({
  id: z.string(),
})

export const getProfileByEmailDto = z.object({
  email: z.string(),
  params: queryConfigParamsSchema.optional(),
})

// Mutation DTOs
export const updateProfileDtoSchema = z.object({
  firstName: nameSchema,
  lastName: nameSchema,
  email: z.string(),
  xHandle: handleSchema,
  instagramHandle: handleSchema,
  tiktokHandle: handleSchema,
  linkedInUrl: personalLinkedInUrlSchema,
  bio: bioSchema,
}) satisfies z.ZodType<UpdateProfile>

// FormData DTO (for file uploads)
export const profileImageUploadDtoSchema = zfd.formData({
  profileImage: zfd.file(),
  profileId: zfd.text(),
})

// Type exports
export type UpdateProfileDto = z.infer<typeof updateProfileDtoSchema>
export type ProfileImageUploadDto = z.infer<typeof profileImageUploadDtoSchema>
```

### DTO Best Practices

1. **Use `satisfies z.ZodType<T>`** for type safety:

```typescript
export const updateProfileDtoSchema = z.object({
  // ...
}) satisfies z.ZodType<UpdateProfile>
```

2. **Reuse primitive schemas**:

```typescript
// src/lib/core/common-schemas.ts
export const nameSchema = z.string().min(1).max(100)
export const handleSchema = z.string().max(50).optional()
export const bioSchema = z.string().max(1000, 'Bio must be less than 1000 characters')
```

3. **Use `zod-form-data` for file uploads**:

```typescript
import { zfd } from 'zod-form-data'

export const fileUploadDto = zfd.formData({
  file: zfd.file(),
  metadata: zfd.text(),
})
```

4. **Export both schema and type**:

```typescript
export const myDtoSchema = z.object({
  /* ... */
})
export type MyDto = z.infer<typeof myDtoSchema>
```

---

## Layer 3: Feature Schemas

Feature schemas compose DTOs with UI-specific concerns:

```typescript
// src/features/profile/schemas.ts
import z from 'zod'
import { updateProfileDtoSchema } from '@/lib/core/dtos/profile-dtos'
import { professionalProfileFormSchema } from '../professional-profile/schemas'
import { imageUploadSchema } from '@/lib/core/common-schemas'

// Compose multiple schemas
export const profileFormSchema = updateProfileDtoSchema
  .merge(professionalProfileFormSchema) // Cross-feature composition
  .merge(imageUploadSchema) // UI-specific (file handling)

export type ProfileFormHandler = z.infer<typeof profileFormSchema>
```

### Composition Patterns

**1. Schema Merging:**

```typescript
const formSchema = baseDtoSchema.merge(additionalFieldsSchema).merge(uiOnlyFieldsSchema)
```

**2. Schema Extension:**

```typescript
const extendedSchema = baseDtoSchema.extend({
  confirmPassword: z.string(),
  termsAccepted: z.boolean(),
})
```

**3. Schema Picking/Omitting:**

```typescript
const partialSchema = fullDtoSchema.pick({
  firstName: true,
  lastName: true,
})

const withoutIdSchema = fullDtoSchema.omit({
  id: true,
  createdAt: true,
})
```

**4. Cross-feature Composition:**

```typescript
// features/profile/schemas.ts
import { professionalProfileFormSchema } from '../professional-profile/schemas'

export const profileFormSchema = updateProfileDtoSchema.merge(professionalProfileFormSchema)
```

---

## Common Schema Patterns

### Enum Schemas

```typescript
export const profileStatuses = ['all', 'claimed', 'unclaimed'] as const
export type ProfileStatus = (typeof profileStatuses)[number]
export const profileStatusSchema = z.enum(profileStatuses)
```

### Filter Schemas

```typescript
export const profileFilters = z.object({
  status: profileStatusSchema.default('all'),
  search: z.string().optional(),
  page: z.number().default(1),
})

export type ProfileFilters = z.infer<typeof profileFilters>
```

### Nested Object Schemas

```typescript
export const imageAssetSchema = z.object({
  file: z.instanceof(File).optional(),
  url: z.string(),
})

export const imageUploadSchema = z.object({
  imageAsset: imageAssetSchema,
})
```

---

## Schema Validation Flow

```
User Input → Feature Schema → DTO Schema → Database Schema
     ↓              ↓              ↓              ↓
  Form UI      UI Validation   API Boundary   DB Insert
```

1. **Feature Schema**: Validates complete form (including UI-only fields)
2. **DTO Schema**: Validates API payload (strips UI-only fields)
3. **Database Schema**: Final validation before persistence

---

## File Structure

> **Note:** The `src/lib/core/` structure below is **reference only** and likely to change based on your backend architecture. The layering concept (DB → DTO → Feature) is the key pattern; exact locations may vary.

```
src/lib/core/                          # Reference structure - adapt as needed
├── schemas/                    # Layer 1: DB schemas
│   ├── profile.ts
│   ├── company.ts
│   └── index.ts
├── dtos/                       # Layer 2: DTOs
│   ├── profile-dtos.ts
│   ├── company-dtos.ts
│   └── index.ts
├── common-schemas.ts           # Shared primitives
└── constants.ts                # Validation constants

src/features/<feature>/                # Stable pattern
└── schemas.ts                  # Layer 3: Feature schemas
```
