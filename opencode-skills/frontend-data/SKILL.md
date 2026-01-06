---
name: frontend-data
description: Implement data fetching with tRPC queries, mutations, cache invalidation, and optimistic updates in Next.js projects
---

# Frontend Data Fetching

Use this skill when fetching server data, creating mutations, or managing cache.

## Query Patterns

### Basic Query

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

### Dependent Queries

```typescript
// First query
const profileQuery = trpc.profile.getByCurrentUser.useQuery()

// Second query - only runs when first has data
const detailsQuery = trpc.profile.getDetails.useQuery(
  { profileId: profileQuery.data?.id ?? '' },
  { enabled: !!profileQuery.data?.id }
)
```

### Parallel Queries

```typescript
// These run simultaneously
const profileQuery = trpc.profile.getByCurrentUser.useQuery()
const companiesQuery = trpc.company.list.useQuery()
const tagsQuery = trpc.tags.list.useQuery()

// Combined loading
const isLoading =
  profileQuery.isLoading || companiesQuery.isLoading || tagsQuery.isLoading
```

### Query with Custom Retry

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

## Mutation Patterns

### Basic Mutation

```typescript
const updateMut = trpc.profile.update.useMutation()

const onSubmit = async (data: FormData) => {
  const result = await updateMut.mutateAsync(data)
}
```

### Mutation with Cache Invalidation

```typescript
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
```

### With Error Toast

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

### Chained Mutations

```typescript
const onSubmit = async (data: FormData) => {
  // 1. Create entity
  const result = await createMut.mutateAsync(data)

  // 2. Upload file if present
  if (data.imageAsset?.file) {
    const formData = new FormData()
    formData.append('entityId', result.id)
    formData.append('image', data.imageAsset.file)
    await uploadMut.mutateAsync(formData)
  }

  // 3. Invalidate cache
  await trpcUtils.entity.list.invalidate()
}
```

## Optimistic Updates

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

## Cache Management

```typescript
const trpcUtils = trpc.useUtils()

// Invalidate all queries for a router
await trpcUtils.profile.invalidate()

// Invalidate specific query
await trpcUtils.profile.getById.invalidate({ id: profileId })

// Parallel invalidation
await Promise.all([trpcUtils.profile.invalidate(), trpcUtils.company.invalidate()])

// Read from cache
const cached = trpcUtils.profile.getById.getData({ id })

// Write to cache
trpcUtils.profile.getById.setData({ id }, (old) => ({ ...old!, name: 'New' }))
```

## Loading States

```typescript
export function ProfileSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <div className="space-y-2" key={i}>
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-10 w-full" />
        </div>
      ))}
    </div>
  )
}
```

## Form Integration

```typescript
function EditForm({ entityId }: { entityId: string }) {
  const entityQuery = trpc.entity.getById.useQuery({ id: entityId })

  const form = useForm<FormHandler>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: '', description: '' },
  })

  const { reset } = form

  // Sync server data to form
  useEffect(() => {
    if (entityQuery.data) {
      reset({
        name: entityQuery.data.name ?? '',
        description: entityQuery.data.description ?? '',
      })
    }
  }, [entityQuery.data, reset])

  if (entityQuery.isLoading) return <FormSkeleton />

  return <form>...</form>
}
```

## Checklist

- [ ] Query uses correct tRPC procedure
- [ ] Loading state shows skeleton
- [ ] Error state handled
- [ ] Mutations invalidate affected queries
- [ ] `enabled` option used for dependent queries
- [ ] Error toast used for mutation failures
