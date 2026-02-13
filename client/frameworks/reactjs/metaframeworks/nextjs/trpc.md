# tRPC (Next.js)

> Next.js-specific tRPC conventions and how tRPC fits into the client API architecture.

## Where tRPC Fits

In this architecture, components never talk to transport directly. The canonical chain is:

`components -> query adapter -> featureApi -> clientApi -> network`

tRPC is an adapter choice for the **transport** layer. Depending on how you wire it, tRPC can act as:

- a `clientApi` implementation (typed transport calls + error normalization)
- a building block used by `featureApi` implementations

The sections below include the legacy “tRPC-first hooks” patterns for reference, but the preferred direction is to keep procedure calls behind `featureApi` interfaces so hooks can be tested with doubles.

## Query Keys + Cache Management (tRPC vs Non-tRPC)

This repo has **two** valid React Query cache patterns depending on how you call the backend:

### If you use tRPC procedures (`@trpc/react-query`)

- **Do not** define Query Key Factory keys for tRPC procedures.
- tRPC already generates stable query keys and utilities.
- Prefer cache invalidation via:
  - `const utils = trpc.useUtils()`
  - `await utils.<router>.<procedure>.invalidate(input?)`
- Use React Query directly (and `trpc.*.queryKey/queryFilter/pathFilter/queryOptions`) as an advanced/escape hatch only.

### If you use non-tRPC HTTP clients (e.g. `ky` calling Next.js `route.ts`)

- Use Query Key Factory (`@lukemorales/query-key-factory`) as the single source of truth for keys.
- Store keys in `src/common/query-keys/<feature>.ts` (so cross-feature components can invalidate/refetch without importing feature internals).

See:

- `./ky-fetch.md`
- `../../../../core/query-keys.md`

## Overview

Data fetching uses:

- **tRPC** for type-safe API calls
- **TanStack Query** for caching, background updates, and state management
- **superjson** for serialization (dates, Maps, Sets)

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

## Provider Setup

```typescript
// src/common/providers/trpc-provider.tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { httpBatchLink, httpLink, splitLink, isNonJsonSerializable } from '@trpc/client'
import { createTRPCReact } from '@trpc/react-query'
import superjson from 'superjson'
import type { AppRouter } from '@/lib/trpc'

export const trpc = createTRPCReact<AppRouter>()

// Singleton for browser
let clientQueryClientSingleton: QueryClient
function getQueryClient() {
  if (typeof window === 'undefined') return makeQueryClient()
  return (clientQueryClientSingleton ??= makeQueryClient())
}

export function TRPCProvider({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient()

  const [trpcClient] = useState(() =>
    trpc.createClient({
      links: [
        splitLink({
          condition: (op) => isNonJsonSerializable(op.input),
          true: httpLink({ url: '/api/trpc', transformer: formDataTransformer }),
          false: httpBatchLink({ url: '/api/trpc', transformer: superjson }),
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

## QueryClient Configuration

```typescript
// src/lib/trpc/query-client.ts

import {
  defaultShouldDehydrateQuery,
  QueryClient,
} from "@tanstack/react-query";
import superjson from "superjson";

export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30 * 1000, // 30 seconds
      },
      dehydrate: {
        serializeData: superjson.serialize,
        shouldDehydrateQuery: (query) =>
          defaultShouldDehydrateQuery(query) ||
          query.state.status === "pending",
      },
      hydrate: {
        deserializeData: superjson.deserialize,
      },
    },
  });
}
```

## Query Patterns

### Feature Hook Convention (Team Rule)

All TanStack Query / tRPC query + mutation hooks for a feature live in `src/features/<feature>/hooks.ts`.

- Components must not call `trpc.*.useQuery()` inline.
- Components import feature hooks and only wire loading/error/UI.

### Basic Query

```typescript
// src/features/profile/hooks.ts
export function useQueryProfileMe() {
  return trpc.profile.getByCurrentUser.useQuery()
}
```

```typescript
// src/features/profile/components/profile-card.tsx
const profileQuery = useQueryProfileMe()

if (profileQuery.isLoading) return <Skeleton />
if (profileQuery.isError) return <Error error={profileQuery.error} />
return <Profile data={profileQuery.data} />
```

### Query with Input

```typescript
// src/features/user/hooks.ts
export function useQueryUserById(userId: string) {
  return trpc.user.getById.useQuery({ id: userId })
}
```

### Query with Options

```typescript
// src/features/profile/hooks.ts
export function useQueryProfileMe() {
  return trpc.profile.getByCurrentUser.useQuery(
    { signedAssets: true },
    {
      retry: (attempt, error) => {
        if (isTRPCNotFoundError(error)) return false
        return attempt <= 3
      },
      staleTime: 60 * 1000, // 1 minute
    },
  )
}
```

### Dependent Queries

Use `enabled` to wait for dependencies:

```typescript
// src/features/settings/hooks.ts
export function useModSettings() {
  const profileQuery = useQueryProfileMe()

  const settingsQuery = trpc.settings.getByProfileId.useQuery(
    { profileId: profileQuery.data?.id ?? '' },
    { enabled: !!profileQuery.data?.id },
  )

  const preferencesQuery = trpc.preferences.get.useQuery(
    { settingsId: settingsQuery.data?.id ?? '' },
    { enabled: !!settingsQuery.data?.id },
  )

  return { profileQuery, settingsQuery, preferencesQuery }
}
```

### Parallel Queries

Independent queries run in parallel:

```typescript
// src/features/dashboard/hooks.ts
export function useModDashboard() {
  const profileQuery = trpc.profile.get.useQuery()
  const statsQuery = trpc.stats.get.useQuery()
  const notificationsQuery = trpc.notifications.list.useQuery()

  return { profileQuery, statsQuery, notificationsQuery }
}
```

## Mutation Patterns

### Basic Mutation

```typescript
// src/features/profile/hooks.ts
export function useMutProfileUpdate() {
  return trpc.profile.update.useMutation()
}
```

### Mutation with Cache Invalidation

```typescript
// src/features/profile/hooks.ts
export function useMutProfileUpdate() {
  const utils = trpc.useUtils()

  return trpc.profile.update.useMutation({
    onSuccess: async (result) => {
      await Promise.all([
        utils.profile.getByCurrentUser.invalidate(),
        utils.profile.getById.invalidate({ id: result.id }),
      ])
    },
  })
}
```

### Parallel Invalidation

```typescript
// src/features/dashboard/hooks.ts
export function useInvalidateDashboardCaches() {
  const utils = trpc.useUtils()

  return async () => {
    await Promise.all([
      utils.profile.invalidate(),
      utils.settings.invalidate(),
      utils.notifications.invalidate(),
    ])
  }
}
```

### Parallel Invalidation (Advanced: React Query Filters)

Use this when you specifically need to operate at the React Query layer (or you are bridging invalidation logic across adapters).

```typescript
// src/features/dashboard/hooks.ts
export function useInvalidateDashboardCachesAdvanced() {
  const trpc = useTRPC()
  const queryClient = useQueryClient()

  return async () => {
    await Promise.all([
      queryClient.invalidateQueries(trpc.profile.pathFilter()),
      queryClient.invalidateQueries(trpc.settings.pathFilter()),
      queryClient.invalidateQueries(trpc.notifications.pathFilter()),
    ])
  }
}
```

### Mutation with Navigation

```typescript
// src/features/items/hooks.ts
export function useMutItemsCreate() {
  const utils = trpc.useUtils()

  return trpc.items.create.useMutation({
    onSuccess: async () => {
      await utils.items.list.invalidate()
    },
  })
}

// src/features/items/components/item-form.tsx
const createMut = useMutItemsCreate()

const onSubmit = async (data: FormData) => {
  await createMut.mutateAsync(data)
  router.push(appRoutes.items.list)
}
```

### FormData Mutation (File Upload)

```typescript
// src/features/profile/hooks.ts
export function useMutProfileUploadImage(profileId: string) {
  const utils = trpc.useUtils()

  return trpc.profile.uploadImage.useMutation({
    onSuccess: async () => {
      await utils.profile.getById.invalidate({ id: profileId })
    },
  })
}

// src/features/profile/components/profile-image-uploader.tsx
const uploadMut = useMutProfileUploadImage(profileId)

const handleUpload = async (file: File) => {
  const formData = new FormData()
  formData.append('profileId', profileId)
  formData.append('image', file)
  await uploadMut.mutateAsync(formData)
}
```

## Cache Management

### Invalidation

```typescript
// src/features/profile/hooks.ts
export function useInvalidateProfileCaches() {
  const utils = trpc.useUtils()

  return {
    invalidateMe: () => utils.profile.getByCurrentUser.invalidate(),
    invalidateById: (id: string) => utils.profile.getById.invalidate({ id }),
    invalidateAll: () => utils.profile.invalidate(),
  }
}
```

### Optimistic Updates

```typescript
// src/features/posts/hooks.ts
export function useMutPostsLike() {
  const trpc = useTRPC()
  const queryClient = useQueryClient()

  return useMutation(
    trpc.post.like.mutationOptions({
      onMutate: async (newLike) => {
        await queryClient.cancelQueries(
          trpc.post.getById.queryFilter({ id: newLike.postId }),
        )

        const previousPost = queryClient.getQueryData(
          trpc.post.getById.queryKey({ id: newLike.postId }),
        )

        queryClient.setQueryData(
          trpc.post.getById.queryKey({ id: newLike.postId }),
          (old) => ({
            ...old!,
            likes: old!.likes + 1,
          }),
        )

        return { previousPost }
      },
      onError: (_err, newLike, context) => {
        queryClient.setQueryData(
          trpc.post.getById.queryKey({ id: newLike.postId }),
          context?.previousPost,
        )
      },
      onSettled: (_data, _err, newLike) => {
        queryClient.invalidateQueries(
          trpc.post.getById.queryFilter({ id: newLike.postId }),
        )
      },
    }),
  )
}
```

### Prefetching

```typescript
// src/features/user/hooks.ts
export function useModUserPrefetchById() {
  const trpc = useTRPC()
  const queryClient = useQueryClient()

  return (userId: string) =>
    queryClient.prefetchQuery(trpc.user.getById.queryOptions({ id: userId }))
}

// src/features/user/components/user-link.tsx
const prefetchUser = useModUserPrefetchById()
const handleMouseEnter = () => void prefetchUser(userId)
```

## Loading States

### Component Loading

```typescript
function ProfilePage() {
  const profileQuery = useQueryProfileMe()

  if (profileQuery.isLoading) {
    return <ProfileSkeleton />
  }

  if (profileQuery.isError) {
    return <ErrorDisplay error={profileQuery.error} />
  }

  return <ProfileContent data={profileQuery.data} />
}
```

### Combined Loading State

```typescript
function Dashboard() {
  const model = useModDashboard()
  const isLoading = model.profileQuery.isLoading || model.statsQuery.isLoading

  if (isLoading) return <DashboardSkeleton />

  return (
    <DashboardContent
      profile={model.profileQuery.data}
      stats={model.statsQuery.data}
    />
  )
}
```

### Skeleton Pattern

```typescript
export function ProfileFormSkeleton() {
  return (
    <div className='space-y-4'>
      {Array.from({ length: 5 }).map((_, i) => (
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

## Error Handling

### Query Error Handling

```typescript
// src/features/profile/hooks.ts
export function useQueryProfileMe() {
  return trpc.profile.get.useQuery(undefined, {
    retry: (attempt, error) => {
      // Don't retry on 404
      if (isTRPCNotFoundError(error)) return false
      return attempt <= 3
    },
  })
}
```

### Mutation Error Handling

```typescript
const catchErrorToast = useCatchErrorToast()
const mutation = useMutProfileUpdate()

const onSubmit = async (data: FormData) => {
  const result = await catchErrorToast(
    async () => {
      await mutation.mutateAsync(data)
      router.push(appRoutes.success)
    },
    { description: 'Profile updated successfully!' },
  )

  if (!result.ok) return
}
```

## Non-tRPC HTTP Clients

tRPC is the default for API calls, but some features use plain HTTP endpoints implemented via Next.js `route.ts`.

Conventions:

- Wrap requests with `ky` (Next.js-friendly Fetch wrapper)
- Decode `ApiResponse<T>` / `ApiErrorResponse` envelopes
- Define query keys with Query Key Factory (`@lukemorales/query-key-factory`) in `src/common/query-keys/<feature>.ts`
- Expose React Query hooks from a dedicated `hooks.ts` (feature hooks or shared client hooks)

See:

- `./ky-fetch.md`
- `../../../../core/query-keys.md`

## Best Practices

### Do

- Use `enabled` for dependent queries
- Invalidate related queries after mutations
- Prefer putting cache management in feature hooks (`hooks.ts`) so components don't duplicate invalidation logic
- Handle loading and error states
- Use skeletons for better UX

### Don't

- Don't fetch in presentation components
- Don't forget to invalidate after mutations
- Don't use `refetch()` when `invalidate()` is more appropriate
- Don't nest queries unnecessarily

## Checklist

- [ ] Query uses `enabled` flag for dependencies
- [ ] Mutation invalidates affected queries
- [ ] Loading state shows skeleton
- [ ] Error state handled gracefully
- [ ] tRPC client uses superjson transformer
- [ ] FormData mutations use splitLink
