---
name: raphfe-composition-pattern
description: Production React composition architecture: coordinate high, fetch low, render dumb. Use when designing/refactoring feature modules with React Query server state, React Context/Zustand client coordination state, and Zod DTO parsing/shaping.
---

# raphfe Composition Pattern

Apply this architecture:

- Coordinate high
- Fetch low
- Render dumb

This keeps re-render scope small, prevents "god components", and makes UI units easy to test.

## Boundaries

| Layer | Owns | Must not own |
| --- | --- | --- |
| Provider layer | App wiring + cross-cutting coordination | Server data fetching, DTO transforms, pagination, cache logic |
| Business layer | Queries/mutations + orchestration for a feature slice | Styling-only primitives |
| Presentation layer | Pure UI from props/callbacks | Queries/mutations, navigation, global state |

Rule: "Fetch low" still means **in the business layer** (not inside presentation components).

## Colocation Ladder

Default decisions:

1) Inline `useQuery` / `useMutation` in the smallest business component that needs the data.
2) Extract to `features/<feature>/hooks.ts` only if reused across multiple business components or it materially simplifies TSX.
3) Move shaping into pure functions and apply them via React Query `select`.
4) Promote to shared clients only when multiple features genuinely share the same API surface.

## Step-by-step Workflow

### 1) Start with a dumb view

Write a view that only renders props.

```tsx
type UserCardViewProps = {
  name: string
  email: string
  isSaving: boolean
  onSave: () => void
}

export function UserCardView(props: UserCardViewProps) {
  return (
    <section>
      <h2>{props.name}</h2>
      <p>{props.email}</p>
      <button type="button" disabled={props.isSaving} onClick={props.onSave}>
        Save
      </button>
    </section>
  )
}
```

### 2) Add a small business component (fetch low)

Colocate the query/mutation where they're consumed.

```tsx
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { UserCardView } from './user-card-view'

const UserDtoSchema = z.object({
  id: z.string(),
  name: z.string().nullable().optional(),
  email: z.string().nullable().optional(),
})

type UserModel = {
  id: string
  name: string
  email: string
}

function toUserModel(dto: z.infer<typeof UserDtoSchema>): UserModel {
  return {
    id: dto.id,
    name: dto.name ?? '',
    email: dto.email ?? '',
  }
}

async function fetchUser(userId: string) {
  const res = await fetch(`/api/users/${userId}`)
  if (!res.ok) throw new Error('Failed to fetch user')
  return UserDtoSchema.parse(await res.json())
}

async function saveUser(input: { userId: string }) {
  const res = await fetch(`/api/users/${input.userId}`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to save user')
  return UserDtoSchema.parse(await res.json())
}

export function UserCard(props: { userId: string }) {
  const qc = useQueryClient()

  const userQuery = useQuery({
    queryKey: ['user', props.userId],
    queryFn: () => fetchUser(props.userId),
    select: toUserModel,
  })

  const saveMut = useMutation({
    mutationFn: () => saveUser({ userId: props.userId }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['user', props.userId] })
    },
  })

  if (userQuery.isLoading) return <div>Loading...</div>
  if (userQuery.isError) return <div>Error</div>
  if (!userQuery.data) return <div>Not found</div>

  return (
    <UserCardView
      name={userQuery.data.name}
      email={userQuery.data.email}
      isSaving={saveMut.isPending}
      onSave={() => saveMut.mutate()}
    />
  )
}
```

### 3) Coordinate high by composing sections

Keep the coordinator focused on layout/composition. Each section owns its own server state.

```tsx
export function SettingsScreen(props: { userId: string }) {
  return (
    <div>
      <UserCard userId={props.userId} />
      <SecuritySection userId={props.userId} />
      <NotificationsSection userId={props.userId} />
    </div>
  )
}
```

### 4) Use Zustand/Context only for client coordination

Store IDs, modes, and UI flags. Do not store server objects that duplicate the query cache.

```ts
import { create } from 'zustand'

type UiState = {
  activeUserId: string | null
  drawerOpen: boolean
  setActiveUserId: (id: string | null) => void
  setDrawerOpen: (open: boolean) => void
}

export const useUiStore = create<UiState>((set) => ({
  activeUserId: null,
  drawerOpen: false,
  setActiveUserId: (id) => set({ activeUserId: id }),
  setDrawerOpen: (open) => set({ drawerOpen: open }),
}))
```

If the state needs multiple isolated instances per subtree, use a Context-scoped store factory.

## Cache Management Patterns

### Invalidate after writes (default)

```ts
await queryClient.invalidateQueries({ queryKey: ['users'] })
await queryClient.invalidateQueries({ queryKey: ['user', userId] })
```

### Optimistic update (when UX needs it)

```ts
useMutation({
  mutationFn: async (input: { userId: string; nextName: string }) => {
    const res = await fetch(`/api/users/${input.userId}`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ name: input.nextName }),
    })
    if (!res.ok) throw new Error('Failed to save')
    return UserDtoSchema.parse(await res.json())
  },
  onMutate: async (input) => {
    await queryClient.cancelQueries({ queryKey: ['user', input.userId] })
    const previous = queryClient.getQueryData<UserModel>(['user', input.userId])
    queryClient.setQueryData<UserModel>(['user', input.userId], (old) =>
      old ? { ...old, name: input.nextName } : old,
    )
    return { previous }
  },
  onError: (_err, input, ctx) => {
    queryClient.setQueryData(['user', input.userId], ctx?.previous)
  },
  onSettled: (_data, _err, input) => {
    queryClient.invalidateQueries({ queryKey: ['user', input.userId] })
  },
})
```

## Anti-patterns

- Fetching/mutating inside presentation components.
- One mega "screen component" that owns every query on the page.
- Providers that fetch server data and push it into context.
- Zustand storing server objects (store IDs + flags; derive server objects from queries).

## Testing Guidance

- Test presentation components by passing plain props (no providers).
- Test business components by mocking the business hooks you extracted (if any), not by mocking fetch.
- Keep transforms pure and test them as normal functions.

## Checklist

- Provider layer is wiring/coordination only.
- Queries/mutations are colocated in business components (or feature hooks when reused).
- Presentation is props/callbacks only.
- Zod parses server payloads at the boundary (in `queryFn` / `mutationFn`).
- Cache invalidation is explicit after writes.
- Zustand/Context stores coordination state only (IDs, modes, flags).
