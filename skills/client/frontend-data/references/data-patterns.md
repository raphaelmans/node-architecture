# Data Fetching Patterns Reference

## Query Patterns

### Basic Query

```typescript
const profileQuery = trpc.profile.getByCurrentUser.useQuery({
  signedAssets: true,
})

// Access states
profileQuery.isLoading    // Initial load
profileQuery.isFetching   // Any fetch (including background)
profileQuery.isError      // Error occurred
profileQuery.isSuccess    // Data available
profileQuery.data         // The data (undefined until success)
profileQuery.error        // Error object (if isError)
```

### Query with Custom Options

```typescript
const profileQuery = trpc.profile.getByCurrentUser.useQuery(
  { signedAssets: true },
  {
    // Retry configuration
    retry: (attempt, error) => {
      if (utils.isTRPCNotFoundError(error)) return false
      return attempt <= 3
    },
    
    // Stale time (how long data is "fresh")
    staleTime: 60 * 1000, // 1 minute
    
    // Cache time (how long to keep in cache)
    gcTime: 5 * 60 * 1000, // 5 minutes
    
    // Refetch options
    refetchOnWindowFocus: false,
    refetchOnMount: true,
  }
)
```

### Dependent Queries

Chain queries where later queries depend on earlier results:

```typescript
// Level 1: User profile
const profileQuery = trpc.profile.getByCurrentUser.useQuery()

// Level 2: Depends on profile
const professionalProfileQuery = trpc.professionalProfile.getByProfileId.useQuery(
  { profileId: profileQuery.data?.id ?? '' },
  { enabled: !!profileQuery.data?.id }
)

// Level 3: Depends on professional profile
const industryTagsQuery = trpc.industryTags.getByProfessionalProfileId.useQuery(
  { professionalProfileId: professionalProfileQuery.data?.id ?? '' },
  { enabled: !!professionalProfileQuery.data?.id }
)

// Combined loading state
const isLoading = profileQuery.isLoading || 
                  professionalProfileQuery.isLoading || 
                  industryTagsQuery.isLoading
```

### Parallel Queries

For independent data that can fetch simultaneously:

```typescript
// All start fetching immediately
const profileQuery = trpc.profile.getByCurrentUser.useQuery()
const companiesQuery = trpc.company.list.useQuery()
const tagsQuery = trpc.tags.list.useQuery()

// Check all loaded
const isLoading = profileQuery.isLoading || 
                  companiesQuery.isLoading || 
                  tagsQuery.isLoading
```

---

## Mutation Patterns

### Basic Mutation

```typescript
const updateMut = trpc.profile.update.useMutation()

const onSubmit = async (data: ProfileFormHandler) => {
  const result = await updateMut.mutateAsync(data)
  // result contains the response
}

// Mutation states
updateMut.isPending   // Mutation in progress
updateMut.isError     // Mutation failed
updateMut.isSuccess   // Mutation succeeded
updateMut.error       // Error object
```

### Mutation with Cache Invalidation

```typescript
import { useQueryClient } from "@tanstack/react-query";
import { useTRPC } from "@/trpc/client";

const trpc = useTRPC();
const queryClient = useQueryClient();

const onSubmit = async (data: ProfileFormHandler) => {
  const result = await updateMut.mutateAsync(data);

  // Invalidate single query
  await queryClient.invalidateQueries(trpc.profile.getByCurrentUser.queryFilter());

  // Invalidate with params
  await queryClient.invalidateQueries(trpc.profile.getById.queryFilter({ id: result.id }));

  // Parallel invalidation
  await Promise.all([
    queryClient.invalidateQueries(trpc.profile.pathFilter()),
    queryClient.invalidateQueries(trpc.company.pathFilter()),
  ]);
};
```

### Chained Mutations

For multi-step operations:

```typescript
const onSubmit = async (data: ProfileFormHandler) => {
  // 1. Update profile
  const profileResult = await profileMut.mutateAsync(data)

  // 2. Conditional create/update
  let detailsId: string
  if (existingDetails?.id) {
    await updateDetailsMut.mutateAsync({
      id: existingDetails.id,
      ...detailsData,
    })
    detailsId = existingDetails.id
  } else {
    const createResult = await createDetailsMut.mutateAsync({
      profileId: profileResult.id,
      ...detailsData,
    })
    detailsId = createResult.id
  }

  // 3. File upload (if present)
  if (data.imageAsset.file) {
    const formData = new FormData()
    formData.append('entityId', profileResult.id)
    formData.append('image', data.imageAsset.file)
    await uploadMut.mutateAsync(formData)
  }

  // 4. Invalidate cache
  await queryClient.invalidateQueries(trpc.profile.getByCurrentUser.queryFilter())
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

---

## Cache Management

### Invalidation Methods

```typescript
import { useQueryClient } from "@tanstack/react-query";
import { useTRPC } from "@/trpc/client";

const trpc = useTRPC();
const queryClient = useQueryClient();

// Invalidate all queries for a router
await queryClient.invalidateQueries(trpc.profile.pathFilter());

// Invalidate specific query (no params)
await queryClient.invalidateQueries(trpc.profile.getByCurrentUser.queryFilter());

// Invalidate specific query (with params)
await queryClient.invalidateQueries(trpc.profile.getById.queryFilter({ id: profileId }));

// Parallel invalidation
await Promise.all([
  queryClient.invalidateQueries(trpc.profile.pathFilter()),
  queryClient.invalidateQueries(trpc.company.pathFilter()),
]);
```

### Direct Cache Updates (getData/setData)

```typescript
import { useQueryClient } from "@tanstack/react-query";
import { useTRPC } from "@/trpc/client";

const trpc = useTRPC();
const queryClient = useQueryClient();

// Read from cache
const cachedProfile = queryClient.getQueryData(
  trpc.profile.getById.queryKey({ id: profileId }),
);

// Write to cache
queryClient.setQueryData(trpc.profile.getById.queryKey({ id: profileId }), (old) => ({
  ...old!,
  name: "Updated Name",
}));

// Cancel outgoing queries
await queryClient.cancelQueries(trpc.profile.getById.queryFilter({ id: profileId }));
```

---

## Optimistic Updates

Full pattern for instant UI feedback:

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTRPC } from "@/trpc/client";

const trpc = useTRPC();
const queryClient = useQueryClient();

const likeMutation = useMutation(
  trpc.post.like.mutationOptions({
    onMutate: async (newLike) => {
      // 1. Cancel outgoing refetches to prevent overwrite
      await queryClient.cancelQueries(
        trpc.post.getById.queryFilter({ id: newLike.postId }),
      );

      // 2. Snapshot previous value for rollback
      const previousPost = queryClient.getQueryData(
        trpc.post.getById.queryKey({ id: newLike.postId }),
      );

      // 3. Optimistically update cache
      queryClient.setQueryData(
        trpc.post.getById.queryKey({ id: newLike.postId }),
        (old) => ({
          ...old!,
          likes: old!.likes + 1,
        }),
      );

      // 4. Return context for rollback
      return { previousPost };
    },

    onError: (_err, newLike, context) => {
      // 5. Rollback on error
      queryClient.setQueryData(
        trpc.post.getById.queryKey({ id: newLike.postId }),
        context?.previousPost,
      );
    },

    onSettled: (_data, _err, newLike) => {
      // 6. Refetch to ensure consistency
      queryClient.invalidateQueries(
        trpc.post.getById.queryFilter({ id: newLike.postId }),
      );
    },
  }),
);
```

---

## Loading States

### Skeleton Pattern

```typescript
function ProfilePage() {
  const profileQuery = trpc.profile.getByCurrentUser.useQuery()

  if (profileQuery.isLoading) {
    return <ProfileSkeleton />
  }

  return <ProfileContent data={profileQuery.data} />
}

function ProfileSkeleton() {
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

### Combined Loading State

```typescript
function DashboardPage() {
  const profileQuery = trpc.profile.getByCurrentUser.useQuery()
  const statsQuery = trpc.dashboard.stats.useQuery()
  const activityQuery = trpc.dashboard.activity.useQuery()

  const isLoading = profileQuery.isLoading || 
                    statsQuery.isLoading || 
                    activityQuery.isLoading

  if (isLoading) {
    return <DashboardSkeleton />
  }

  return (
    <Dashboard
      profile={profileQuery.data}
      stats={statsQuery.data}
      activity={activityQuery.data}
    />
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
      // Don't retry on 404
      if (utils.isTRPCNotFoundError(error)) return false
      return attempt <= 3
    },
  }
)

if (profileQuery.isError) {
  return <ErrorDisplay error={profileQuery.error} />
}
```

### Mutation Error Handling with Toast

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
    }
  )
}
```

---

## Form Integration

### Form with Query Data

```typescript
function ProfileForm() {
  const profileQuery = trpc.profile.getByCurrentUser.useQuery()

  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
    defaultValues: {
      firstName: '',
      lastName: '',
    },
  })

  const { reset } = form

  // Sync server data to form
  useEffect(() => {
    if (profileQuery.data) {
      reset({
        firstName: profileQuery.data.firstName ?? '',
        lastName: profileQuery.data.lastName ?? '',
      })
    }
  }, [profileQuery.data, reset])

  if (profileQuery.isLoading) {
    return <ProfileFormSkeleton />
  }

  return <form>...</form>
}
```

### Form with Mutation

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTRPC } from "@/trpc/client";

function ProfileForm() {
  const trpc = useTRPC();
  const queryClient = useQueryClient();
  const router = useRouter();
  const catchErrorToast = useCatchErrorToast();

  const updateMut = useMutation(trpc.profile.update.mutationOptions());

  const onSubmit = async (data: ProfileFormHandler) => {
    return catchErrorToast(
      async () => {
        await updateMut.mutateAsync(data);
        await queryClient.invalidateQueries(
          trpc.profile.getByCurrentUser.queryFilter(),
        );
        router.push(appRoutes.dashboard);
      },
      { description: "Profile updated!" },
    );
  };

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      {/* fields */}
    </StandardFormProvider>
  );
}
```
