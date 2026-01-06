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
import { trpc } from '@/lib/trpc/client'

function MyForm() {
  const trpcUtils = trpc.useUtils()
  const updateMut = trpc.profile.update.useMutation()

  const onSubmit = async (data: FormData) => {
    await updateMut.mutateAsync(data)
    
    // Invalidate affected queries
    await Promise.all([
      trpcUtils.profile.getByCurrentUser.invalidate(),
      trpcUtils.profile.getById.invalidate({ id: data.id }),
    ])
  }
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
const likeMutation = trpc.post.like.useMutation({
  onMutate: async (newLike) => {
    // Cancel outgoing refetches
    await trpcUtils.post.getById.cancel({ id: newLike.postId })
    
    // Snapshot previous value
    const previous = trpcUtils.post.getById.getData({ id: newLike.postId })
    
    // Optimistically update
    trpcUtils.post.getById.setData({ id: newLike.postId }, (old) => ({
      ...old!,
      likes: old!.likes + 1,
    }))
    
    return { previous }
  },
  onError: (err, newLike, context) => {
    // Rollback on error
    trpcUtils.post.getById.setData({ id: newLike.postId }, context?.previous)
  },
  onSettled: () => {
    // Refetch to ensure consistency
    trpcUtils.post.getById.invalidate()
  },
})
```

## Invalidation Strategies

| Method | Use Case |
|--------|----------|
| `trpcUtils.resource.invalidate()` | Invalidate all queries for a procedure |
| `trpcUtils.resource.getById.invalidate({ id })` | Invalidate specific query |
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
