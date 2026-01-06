# Data Fetching

> Patterns for data fetching using tRPC with TanStack Query.

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

### Basic Query

```typescript
const profileQuery = trpc.profile.getByCurrentUser.useQuery()

if (profileQuery.isLoading) return <Skeleton />
if (profileQuery.isError) return <Error error={profileQuery.error} />
return <Profile data={profileQuery.data} />
```

### Query with Input

```typescript
const userQuery = trpc.user.getById.useQuery({ id: userId });
```

### Query with Options

```typescript
const profileQuery = trpc.profile.getByCurrentUser.useQuery(
  { signedAssets: true },
  {
    retry: (attempt, error) => {
      if (isTRPCNotFoundError(error)) return false;
      return attempt <= 3;
    },
    staleTime: 60 * 1000, // 1 minute
  },
);
```

### Dependent Queries

Use `enabled` to wait for dependencies:

```typescript
// First query
const profileQuery = trpc.profile.getByCurrentUser.useQuery();

// Second query depends on first
const settingsQuery = trpc.settings.getByProfileId.useQuery(
  { profileId: profileQuery.data?.id ?? "" },
  { enabled: !!profileQuery.data?.id },
);

// Third query depends on second
const preferencesQuery = trpc.preferences.get.useQuery(
  { settingsId: settingsQuery.data?.id ?? "" },
  { enabled: !!settingsQuery.data?.id },
);
```

### Parallel Queries

Independent queries run in parallel:

```typescript
function Dashboard() {
  const profileQuery = trpc.profile.get.useQuery();
  const statsQuery = trpc.stats.get.useQuery();
  const notificationsQuery = trpc.notifications.list.useQuery();

  // All three run in parallel
}
```

## Mutation Patterns

### Basic Mutation

```typescript
const updateMut = trpc.profile.update.useMutation();

const onSubmit = async (data: ProfileData) => {
  await updateMut.mutateAsync(data);
};
```

### Mutation with Cache Invalidation

```typescript
const trpcUtils = trpc.useUtils();
const updateMut = trpc.profile.update.useMutation();

const onSubmit = async (data: ProfileData) => {
  const result = await updateMut.mutateAsync(data);

  // Invalidate affected queries
  await trpcUtils.profile.getByCurrentUser.invalidate();
  await trpcUtils.profile.getById.invalidate({ id: result.id });
};
```

### Parallel Invalidation

```typescript
await Promise.all([
  trpcUtils.profile.invalidate(),
  trpcUtils.settings.invalidate(),
  trpcUtils.notifications.invalidate(),
]);
```

### Mutation with Navigation

```typescript
const router = useRouter();
const trpcUtils = trpc.useUtils();

const onSubmit = async (data: FormData) => {
  await createMut.mutateAsync(data);
  await trpcUtils.items.list.invalidate();
  router.push(appRoutes.items.list);
};
```

### FormData Mutation (File Upload)

```typescript
const uploadMut = trpc.profile.uploadImage.useMutation();

const handleUpload = async (file: File, profileId: string) => {
  const formData = new FormData();
  formData.append("profileId", profileId);
  formData.append("image", file);

  await uploadMut.mutateAsync(formData);
};
```

## Cache Management

### Invalidation

```typescript
const trpcUtils = trpc.useUtils();

// Invalidate single query
await trpcUtils.profile.getByCurrentUser.invalidate();

// Invalidate with specific params
await trpcUtils.user.getById.invalidate({ id: userId });

// Invalidate all queries for a procedure
await trpcUtils.profile.invalidate();
```

### Optimistic Updates

```typescript
const likeMut = trpc.post.like.useMutation({
  onMutate: async (newLike) => {
    // Cancel outgoing refetches
    await trpcUtils.post.getById.cancel({ id: newLike.postId });

    // Snapshot previous value
    const previousPost = trpcUtils.post.getById.getData({ id: newLike.postId });

    // Optimistically update
    trpcUtils.post.getById.setData({ id: newLike.postId }, (old) => ({
      ...old!,
      likes: old!.likes + 1,
    }));

    return { previousPost };
  },
  onError: (err, newLike, context) => {
    // Rollback on error
    trpcUtils.post.getById.setData(
      { id: newLike.postId },
      context?.previousPost,
    );
  },
  onSettled: () => {
    trpcUtils.post.getById.invalidate();
  },
});
```

### Prefetching

```typescript
// Prefetch on hover
const handleMouseEnter = () => {
  trpcUtils.user.getById.prefetch({ id: userId });
};
```

## Loading States

### Component Loading

```typescript
function ProfilePage() {
  const profileQuery = trpc.profile.get.useQuery()

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
  const profileQuery = trpc.profile.get.useQuery()
  const settingsQuery = trpc.settings.get.useQuery(
    { profileId: profileQuery.data?.id ?? '' },
    { enabled: !!profileQuery.data?.id },
  )

  const isLoading = profileQuery.isLoading || settingsQuery.isLoading

  if (isLoading) return <DashboardSkeleton />

  return <DashboardContent profile={profileQuery.data} settings={settingsQuery.data} />
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
const profileQuery = trpc.profile.get.useQuery(undefined, {
  retry: (attempt, error) => {
    // Don't retry on 404
    if (isTRPCNotFoundError(error)) return false;
    return attempt <= 3;
  },
});
```

### Mutation Error Handling

```typescript
const catchErrorToast = useCatchErrorToast();

const onSubmit = async (data: FormData) => {
  return catchErrorToast(
    async () => {
      await mutation.mutateAsync(data);
      router.push(appRoutes.success);
    },
    { description: "Profile updated successfully!" },
  );
};
```

## Best Practices

### Do

- Use `enabled` for dependent queries
- Invalidate related queries after mutations
- Use `trpcUtils` for cache operations
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
