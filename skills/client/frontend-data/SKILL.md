---
name: frontend-data
description: Implement data fetching with tRPC queries, mutations, and cache management
---

# Frontend Data Fetching

Use this skill when implementing data fetching patterns with tRPC and TanStack Query.

## When to Use

- Fetching server data in components
- Creating mutations with cache invalidation
- Implementing loading/error states
- Setting up dependent or parallel queries
- Optimistic updates

## Prerequisites

- tRPC router endpoint exists on the backend
- Component is a Client Component (`'use client'`)

## Steps

### 1. Identify Query Pattern

Determine which pattern fits your use case:

| Pattern | Use Case |
|---------|----------|
| Basic Query | Single data fetch |
| Dependent Query | Data depends on another query's result |
| Parallel Queries | Multiple independent fetches |
| Mutation | Create/update/delete operations |
| Optimistic Update | Instant UI feedback before server confirms |

### 2. Implement Query

#### Basic Query

```typescript
import { trpc } from '@/lib/trpc/client'

function MyComponent() {
  const profileQuery = trpc.profile.getByCurrentUser.useQuery({
    signedAssets: true,
  })

  if (profileQuery.isLoading) return <Skeleton />
  if (profileQuery.isError) return <Error error={profileQuery.error} />
  
  return <div>{profileQuery.data.name}</div>
}
```

Preferred convention for server-state hooks (TanStack Query wrappers):

- Query hooks: `useQuery<Feature><Noun><Qualifier?>`
- Mutation hooks: `useMut<Feature><Verb><Object?>`
- Composite hooks: `useMod<Descriptive>`

Example (feature hook wrapper):

```typescript
// src/features/profile/hooks.ts
export function useQueryProfileMe() {
  return trpc.profile.getByCurrentUser.useQuery()
}
```

#### Dependent Queries

```typescript
// First query
const profileQuery = trpc.profile.getByCurrentUser.useQuery()

// Second query - only runs when first has data
const detailsQuery = trpc.profile.getDetails.useQuery(
  { profileId: profileQuery.data?.id ?? '' },
  { enabled: !!profileQuery.data?.id }
)
```

#### Parallel Queries

```typescript
// These run simultaneously
const profileQuery = trpc.profile.getByCurrentUser.useQuery()
const companiesQuery = trpc.company.list.useQuery()
const tagsQuery = trpc.tags.list.useQuery()
```

### 3. Implement Mutation with Cache Invalidation

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTRPC } from "@/trpc/client";

function MyForm() {
  const trpc = useTRPC();
  const queryClient = useQueryClient();

  const updateMut = useMutation(trpc.profile.update.mutationOptions());

  const onSubmit = async (data: FormData) => {
    await updateMut.mutateAsync(data);

    // Invalidate affected queries (type-safe)
    await Promise.all([
      queryClient.invalidateQueries(trpc.profile.getByCurrentUser.queryFilter()),
      queryClient.invalidateQueries(trpc.profile.getById.queryFilter({ id: data.id })),
    ]);
  };
}
```

### 4. Add Loading States

Create a skeleton component matching your UI structure:

```typescript
export function ProfileSkeleton() {
  return (
    <div className='space-y-4'>
      {Array.from({ length: 5 }).map((_, i) => (
        <div className='space-y-2' key={i}>
          <Skeleton className='h-4 w-20' />
          <Skeleton className='h-10 w-full' />
        </div>
      ))}
    </div>
  )
}
```

### 5. Handle Errors

Use the `useCatchErrorToast` hook for mutations:

```typescript
const catchErrorToast = useCatchErrorToast()

const onSubmit = async (data: FormData) => {
  return catchErrorToast(
    async () => {
      await mutation.mutateAsync(data)
      router.push(appRoutes.success)
    },
    { description: 'Saved successfully!' }
  )
}
```

For queries, use custom retry logic:

```typescript
const query = trpc.resource.getById.useQuery(
  { id },
  {
    retry: (attempt, error) => {
      if (utils.isTRPCNotFoundError(error)) return false
      return attempt <= 3
    },
  }
)
```

### 6. (Optional) Implement Optimistic Updates

For instant UI feedback:

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTRPC } from "@/trpc/client";

const trpc = useTRPC();
const queryClient = useQueryClient();

const likeMutation = useMutation(
  trpc.post.like.mutationOptions({
    onMutate: async (newLike) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries(
        trpc.post.getById.queryFilter({ id: newLike.postId }),
      );

      // Snapshot previous value
      const previous = queryClient.getQueryData(
        trpc.post.getById.queryKey({ id: newLike.postId }),
      );

      // Optimistically update
      queryClient.setQueryData(
        trpc.post.getById.queryKey({ id: newLike.postId }),
        (old) => ({
          ...old!,
          likes: old!.likes + 1,
        }),
      );

      return { previous };
    },
    onError: (_err, newLike, context) => {
      // Rollback on error
      queryClient.setQueryData(
        trpc.post.getById.queryKey({ id: newLike.postId }),
        context?.previous,
      );
    },
    onSettled: (_data, _err, newLike) => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries(
        trpc.post.getById.queryFilter({ id: newLike.postId }),
      );
    },
  }),
);
```

## Invalidation Strategies

| Method | Use Case |
|--------|----------|
| `queryClient.invalidateQueries(trpc.resource.pathFilter())` | Invalidate all queries under a router |
| `queryClient.invalidateQueries(trpc.resource.getById.queryFilter({ id }))` | Invalidate specific query |
| `Promise.all([...])` | Parallel invalidation |

## Checklist

- [ ] Query uses correct tRPC procedure
- [ ] Loading state shows skeleton
- [ ] Error state handled appropriately
- [ ] Mutations invalidate affected queries
- [ ] `enabled` option used for dependent queries
- [ ] Error toast used for mutation failures

## References

See `references/data-patterns.md` for detailed patterns.
