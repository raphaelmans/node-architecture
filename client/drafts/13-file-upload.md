# File Upload

This guide covers file upload patterns using tRPC with `zod-form-data` (zfd).

---

## Dependencies

```json
{
  "zod": "^3.25.8",
  "zod-form-data": "^2.0.7",
  "@trpc/client": "11.0.0-rc.708",
  "@trpc/server": "11.0.0-rc.708"
}
```

---

## Overview

File uploads use:

- **`zod-form-data`** - Parse and validate FormData
- **tRPC `splitLink`** - Route FormData to non-batched endpoint
- **FormData API** - Browser-native multipart encoding

---

## DTO Schema

```typescript
// src/lib/core/dtos/profile-dtos.ts
import { z } from 'zod'
import { zfd } from 'zod-form-data'

// File upload DTO
export const profileImageUploadDtoSchema = zfd.formData({
  profileImage: zfd.file(), // Required file
  profileId: zfd.text(), // Required text field
})

export type ProfileImageUploadDto = z.infer<typeof profileImageUploadDtoSchema>

// With optional file
export const documentUploadDtoSchema = zfd.formData({
  document: zfd.file().optional(), // Optional file
  title: zfd.text(),
  description: zfd.text().optional(),
})

// With file validation
export const imageUploadDtoSchema = zfd.formData({
  image: zfd
    .file()
    .refine(file => file.size <= 5 * 1024 * 1024, 'File must be less than 5MB')
    .refine(
      file => ['image/jpeg', 'image/png', 'image/webp'].includes(file.type),
      'File must be JPEG, PNG, or WebP',
    ),
  entityId: zfd.text(),
})
```

---

## tRPC Client Configuration

The client must route FormData requests to a non-batched endpoint:

```typescript
// src/common/providers/trpc-provider.tsx
import { httpBatchLink, httpLink, splitLink, isNonJsonSerializable } from '@trpc/client'
import { FormDataTransformer } from '@/lib/trpc/transformers'

const trpcClient = trpc.createClient({
  links: [
    splitLink({
      // Check if input is FormData
      condition: op => isNonJsonSerializable(op.input),
      // Use non-batched link with FormData transformer
      true: httpLink({
        url: getUrl(),
        transformer: new FormDataTransformer(),
      }),
      // Use batched link for regular JSON
      false: httpBatchLink({
        url: getUrl(),
        transformer: superjson,
      }),
    }),
  ],
})
```

---

## FormData Transformer

```typescript
// src/lib/trpc/transformers.ts
import type { DataTransformer } from '@trpc/server/unstable-core-do-not-import'

export class FormDataTransformer implements DataTransformer {
  serialize(data: unknown): FormData {
    if (data instanceof FormData) {
      return data
    }
    throw new Error('Expected FormData')
  }

  deserialize(data: unknown): unknown {
    return data
  }
}
```

---

## tRPC Router

```typescript
// src/lib/trpc/routers/profile.ts
import { protectedProcedure, router } from '../init'
import { profileImageUploadDtoSchema } from '@/lib/core/dtos/profile-dtos'

export const profileRouter = router({
  uploadProfileImage: protectedProcedure
    .input(profileImageUploadDtoSchema)
    .mutation(async ({ ctx, input }) => {
      const { profileImage, profileId } = input

      // profileImage is a File object
      // Upload to storage (Supabase, S3, etc.)
      const url = await ctx.controllers.profile.uploadImage(profileId, profileImage)

      return { url }
    }),
})
```

---

## Client Usage

### In Form Component

```typescript
// src/features/profile/components/profile-form.tsx
const uploadImageMut = trpc.profile.uploadProfileImage.useMutation()

const onSubmit = async (data: ProfileFormHandler) => {
  const profileResult = await profileMut.mutateAsync(data)

  // Handle file upload
  if (data.imageAsset.file) {
    const formData = new FormData()
    formData.append('profileId', profileResult.id)
    formData.append('profileImage', data.imageAsset.file)

    await uploadImageMut.mutateAsync(formData)
  }
}
```

### Standalone Upload

```typescript
function ImageUploader({ entityId }: { entityId: string }) {
  const uploadMut = trpc.entity.uploadImage.useMutation()

  const handleUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('entityId', entityId)
    formData.append('image', file)

    const result = await uploadMut.mutateAsync(formData)
    return result.url
  }

  return (
    <input
      type="file"
      accept="image/*"
      onChange={(e) => {
        const file = e.target.files?.[0]
        if (file) handleUpload(file)
      }}
    />
  )
}
```

---

## Form Schema for File Fields

```typescript
// src/lib/core/common-schemas.ts
import { z } from 'zod'

// Schema for form state (not DTO)
export const imageAssetSchema = z.object({
  file: z.instanceof(File).optional(), // New file to upload
  url: z.string(), // Current/preview URL
})

export const imageUploadSchema = z.object({
  imageAsset: imageAssetSchema,
})

export type ImageAsset = z.infer<typeof imageAssetSchema>
```

```typescript
// src/features/profile/schemas.ts
import { updateProfileDtoSchema } from '@/lib/core/dtos/profile-dtos'
import { imageUploadSchema } from '@/lib/core/common-schemas'

export const profileFormSchema = updateProfileDtoSchema.merge(imageUploadSchema) // Add imageAsset field for form

export type ProfileFormHandler = z.infer<typeof profileFormSchema>
```

---

## File Validation

### Client-side (before upload)

```typescript
// src/lib/core/constants.ts
export const FILE_SIZE_LIMITS = {
  PROFILE_IMAGE: 5 * 1024 * 1024, // 5MB
  DOCUMENT: 10 * 1024 * 1024, // 10MB
  VIDEO: 100 * 1024 * 1024, // 100MB
} as const

export const FILE_SIZE_LIMITS_READABLE = {
  PROFILE_IMAGE: '5MB',
  DOCUMENT: '10MB',
  VIDEO: '100MB',
} as const

export function validateFileSize(file: File, maxSize: number): boolean {
  return file.size <= maxSize
}

export function validateFileType(file: File, allowedTypes: string[]): boolean {
  return allowedTypes.includes(file.type)
}
```

### Usage with react-dropzone

```typescript
const onDrop = useCallback((acceptedFiles: File[]) => {
  const file = acceptedFiles[0]
  if (!file) return

  if (!validateFileSize(file, FILE_SIZE_LIMITS.PROFILE_IMAGE)) {
    toast.error(`File must be less than ${FILE_SIZE_LIMITS_READABLE.PROFILE_IMAGE}`)
    return
  }

  // Process file...
}, [])

const { getRootProps, getInputProps } = useDropzone({
  onDrop,
  accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
  maxSize: FILE_SIZE_LIMITS.PROFILE_IMAGE,
  maxFiles: 1,
})
```

### Server-side (in DTO)

```typescript
export const imageUploadDtoSchema = zfd.formData({
  image: zfd
    .file()
    .refine(file => file.size <= 5 * 1024 * 1024, 'Max 5MB')
    .refine(
      file => ['image/jpeg', 'image/png', 'image/webp'].includes(file.type),
      'Invalid file type',
    ),
})
```

---

## StandardFormField for File Upload

Using composition pattern:

```typescript
<StandardFormField<ProfileFormHandler>
  name='imageAsset'
  label='Profile Picture'
  description='Max 5MB, JPG/PNG/WebP'
>
  {({ field }) => (
    <FileDropzone
      value={field.value}
      onChange={field.onChange}
      accept={{ 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] }}
      maxSize={FILE_SIZE_LIMITS.PROFILE_IMAGE}
    />
  )}
</StandardFormField>
```

---

## Best Practices

1. **Validate on both sides** - Client for UX, server for security

2. **Use splitLink** - FormData cannot be batched

3. **Separate upload from form** - Upload file, then save URL

   ```typescript
   // 1. Create entity
   const entity = await createMut.mutateAsync(data)
   // 2. Upload file with entity ID
   await uploadMut.mutateAsync(formData)
   ```

4. **Handle upload errors** - Show progress, retry failed uploads

5. **Clean up on failure** - Delete uploaded files if entity creation fails
