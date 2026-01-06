# TanStack Query + tRPC Integration

This guide covers the data fetching architecture using TanStack Query with tRPC.

---

## Dependencies

```json
{
  "@tanstack/react-query": "^5.64.2",
  "@tanstack/react-query-devtools": "^5.62.16",
  "@trpc/client": "11.0.0-rc.708",
  "@trpc/react-query": "11.0.0-rc.708",
  "@trpc/server": "11.0.0-rc.708",
  "superjson": "^2.2.2"
}
```

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Component │────▶│   tRPC Client   │────▶│   tRPC Server   │
│                 │     │  (React Query)  │     │   (Procedures)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                      │                       │
         ▼                      ▼                       ▼
    useQuery/            QueryClient              Controllers
    useMutation          Cache + State            + Services
```

---

## tRPC Client Setup

### Provider Configuration

```typescript
// src/common/providers/trpc-provider.tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { httpBatchLink, httpLink, splitLink, isNonJsonSerializable } from '@trpc/client'
import { createTRPCReact } from '@trpc/react-query'
import { useState } from 'react'
import superjson from 'superjson'
import type { AppRouter } from '@/lib/trpc'
import { makeQueryClient } from '@/lib/trpc/query-client'
import { FormDataTransformer } from '@/lib/trpc/transformers'

// Create typed tRPC hooks
export const trpc = createTRPCReact<AppRouter>()

// Singleton pattern for browser
let clientQueryClientSingleton: QueryClient
function getQueryClient() {
  if (typeof window === 'undefined') {
    return makeQueryClient()  // Server: always new
  }
  return (clientQueryClientSingleton ??= makeQueryClient())  // Browser: singleton
}

function getUrl() {
  const base = (() => {
    if (typeof window !== 'undefined') return ''
    if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`
    return `http://localhost:${process.env.DEV_PORT}`
  })()
  return `${base}/api/trpc`
}

export function TRPCProvider({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient()

  const [trpcClient] = useState(() =>
    trpc.createClient({
      links: [
        // Split link: FormData vs JSON
        splitLink({
          condition: op => isNonJsonSerializable(op.input),
          true: httpLink({
            url: getUrl(),
            transformer: new FormDataTransformer(),
          }),
          false: httpBatchLink({
            url: getUrl(),
            transformer: superjson,
          }),
        }),
      ],
    }),
  )

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

### QueryClient Factory

```typescript
// src/lib/trpc/query-client.ts
import { defaultShouldDehydrateQuery, QueryClient } from '@tanstack/react-query'
import superjson from 'superjson'

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

---

## Query Patterns

### Basic Query

```typescript
const profileQuery = trpc.profile.getByCurrentUser.useQuery({
  signedAssets: true,
})

// Access data
if (profileQuery.isLoading) return <Skeleton />
if (profileQuery.isError) return <Error error={profileQuery.error} />
return <Profile data={profileQuery.data} />
```

### Query with Custom Retry Logic

```typescript
const profileQuery = trpc.profile.getByCurrentUser.useQuery(
  { signedAssets: true },
  {
    retry: (attempt, error) => {
      // Don't retry on 404
      if (utils.isTRPCNotFoundError(error)) {
        return false
      }
      return attempt <= 3
    },
  },
)
```

### Dependent Queries

```typescript
// First query
const profileQuery = trpc.profile.getByCurrentUser.useQuery()

// Second query depends on first
const professionalProfileQuery = trpc.professionalProfile.getByProfileId.useQuery(
  { profileId: profileQuery.data?.id ?? '' },
  { enabled: !!profileQuery.data?.id }, // Only run when profileId exists
)

// Third query depends on second
const industryTagsQuery = trpc.industryTags.getByProfessionalProfileId.useQuery(
  { professionalProfileId: professionalProfileQuery.data?.id ?? '' },
  { enabled: !!professionalProfileQuery.data?.id },
)
```

### Parallel Queries

```typescript
// These run in parallel (no dependencies)
const profileQuery = trpc.profile.getByCurrentUser.useQuery()
const companiesQuery = trpc.company.list.useQuery()
const tagsQuery = trpc.tags.list.useQuery()
```

---

## Mutation Patterns

### Basic Mutation

```typescript
const profileMut = trpc.profile.upsertUserProfile.useMutation()

const onSubmit = async (data: ProfileFormHandler) => {
  const result = await profileMut.mutateAsync(data)
  // Handle success
}
```

### Mutation with Cache Invalidation

```typescript
const trpcUtils = trpc.useUtils()

const onSubmit = async (data: ProfileFormHandler) => {
  const result = await profileMut.mutateAsync(data)

  // Invalidate affected queries
  await Promise.all([
    trpcUtils.profile.getByCurrentUser.invalidate(),
    trpcUtils.professionalProfile.getByProfileId.invalidate({
      profileId: result.id,
    }),
    trpcUtils.industryTags.getByProfessionalProfileId.invalidate({
      professionalProfileId: result.professionalProfileId,
    }),
  ])
}
```

### FormData Mutation (File Upload)

```typescript
const uploadImageMut = trpc.profile.uploadProfileImage.useMutation()

const handleUpload = async (file: File, profileId: string) => {
  const formData = new FormData()
  formData.append('profileId', profileId)
  formData.append('profileImage', file)

  await uploadImageMut.mutateAsync(formData)
}
```

### Chained Mutations

```typescript
const onSubmit = async (data: ProfileFormHandler) => {
  // 1. Update profile
  const profileResult = await profileMut.mutateAsync(data)

  // 2. Update or create professional profile
  let professionalProfileId: string
  if (existingProfessionalProfile?.id) {
    await updateMut.mutateAsync({
      profileId: existingProfessionalProfile.id,
      ...professionalData,
    })
    professionalProfileId = existingProfessionalProfile.id
  } else {
    const createResult = await createMut.mutateAsync({
      profileId: profileResult.id,
      ...professionalData,
    })
    professionalProfileId = createResult.id
  }

  // 3. Handle file upload
  if (data.imageAsset.file) {
    const formData = new FormData()
    formData.append('profileId', profileResult.id)
    formData.append('profileImage', data.imageAsset.file)
    await uploadImageMut.mutateAsync(formData)
  }

  // 4. Invalidate cache
  await trpcUtils.profile.getByCurrentUser.invalidate()
}
```

---

## Cache Management

### Invalidation Strategies

```typescript
const trpcUtils = trpc.useUtils()

// Invalidate single query
await trpcUtils.profile.getByCurrentUser.invalidate()

// Invalidate with params
await trpcUtils.profile.getById.invalidate({ id: profileId })

// Invalidate all queries for a procedure
await trpcUtils.profile.invalidate()

// Parallel invalidation
await Promise.all([trpcUtils.profile.invalidate(), trpcUtils.company.invalidate()])
```

### Optimistic Updates

```typescript
const likeMutation = trpc.post.like.useMutation({
  onMutate: async newLike => {
    // Cancel outgoing refetches
    await trpcUtils.post.getById.cancel({ id: newLike.postId })

    // Snapshot previous value
    const previousPost = trpcUtils.post.getById.getData({ id: newLike.postId })

    // Optimistically update
    trpcUtils.post.getById.setData({ id: newLike.postId }, old => ({
      ...old!,
      likes: old!.likes + 1,
    }))

    return { previousPost }
  },
  onError: (err, newLike, context) => {
    // Rollback on error
    trpcUtils.post.getById.setData({ id: newLike.postId }, context?.previousPost)
  },
  onSettled: () => {
    // Refetch after mutation
    trpcUtils.post.getById.invalidate()
  },
})
```

---

## Loading States

### Component-level Loading

```typescript
function ProfilePage() {
  const profileQuery = trpc.profile.getByCurrentUser.useQuery()
  const professionalQuery = trpc.professionalProfile.getByProfileId.useQuery(
    { profileId: profileQuery.data?.id ?? '' },
    { enabled: !!profileQuery.data?.id }
  )

  // Combined loading state
  if (profileQuery.isLoading || professionalQuery.isLoading) {
    return <ProfileSkeleton />
  }

  return <ProfileContent data={profileQuery.data} />
}
```

### Skeleton Component Pattern

```typescript
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

## Error Handling

### Query Error Handling

```typescript
const profileQuery = trpc.profile.getByCurrentUser.useQuery(
  { signedAssets: true },
  {
    retry: (attempt, error) => {
      if (utils.isTRPCNotFoundError(error)) return false
      return attempt <= 3
    },
  },
)

if (profileQuery.isError) {
  return <ErrorDisplay error={profileQuery.error} />
}
```

### Mutation Error Handling

```typescript
const catchErrorToast = useCatchErrorToast()

const onSubmit = async (data: FormData) => {
  return catchErrorToast(
    async () => {
      await mutation.mutateAsync(data)
      router.push(appRoutes.success)
    },
    {
      description: 'Operation completed successfully!',
    },
  )
}
```

---

## tRPC Client Export

```typescript
// src/lib/trpc/client.ts
export { trpc } from '@/common/providers/trpc-provider'

// Usage in components
import { trpc } from '@/lib/trpc/client'
```

---

## File Structure

> **Note:** The `src/lib/trpc/` structure is **reference only**. The tRPC setup patterns are transferable, but exact file organization may vary based on your project needs.

```
src/
├── common/providers/
│   └── trpc-provider.tsx    # Provider + client setup (stable)
├── lib/trpc/                        # Reference structure - adapt as needed
│   ├── init.ts              # Server-side tRPC setup
│   ├── client.ts            # Client export
│   ├── query-client.ts      # QueryClient factory
│   └── transformers.ts      # Custom transformers (FormData)
```
