# nuqs URL State Management

This guide covers URL query parameter state management using nuqs.

---

## Dependencies

```json
{
  "nuqs": "^2.3.0"
}
```

---

## Overview

nuqs provides type-safe URL query parameter state that:

- Syncs state with URL
- Supports SSR
- Provides type-safe parsers
- Works with Next.js App Router

---

## Basic Setup

### Provider (App Router)

```typescript
// src/app/layout.tsx
import { NuqsAdapter } from 'nuqs/adapters/next/app'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <NuqsAdapter>
          {children}
        </NuqsAdapter>
      </body>
    </html>
  )
}
```

---

## Parser Patterns

### String Literal Parser

```typescript
// src/features/landing/hooks.ts
import { parseAsStringLiteral, useQueryState } from 'nuqs'

const landingStates = ['login', 'signup'] as const
export type LandingState = (typeof landingStates)[number]

export const useQueryLandingState = () => {
  return useQueryState(
    'step', // URL param name: ?step=login
    parseAsStringLiteral(landingStates).withOptions({
      history: 'push', // Create browser history entry
    }),
  )
}

// Usage
const [step, setStep] = useQueryLandingState()
// step: 'login' | 'signup' | null
// setStep('signup') -> URL becomes ?step=signup
```

### Error State Parser

```typescript
const errorStates = ['email-used', 'invalid-token', 'expired'] as const
export type ErrorState = (typeof errorStates)[number]

export const useQueryErrorState = () => {
  return useQueryState(
    'error',
    parseAsStringLiteral(errorStates).withOptions({
      history: 'push',
    }),
  )
}
```

---

## Available Parsers

```typescript
import {
  parseAsString, // string | null
  parseAsInteger, // number | null
  parseAsFloat, // number | null
  parseAsBoolean, // boolean | null
  parseAsStringLiteral, // union type | null
  parseAsStringEnum, // enum value | null
  parseAsArrayOf, // array | null
  parseAsJson, // JSON object | null
  parseAsTimestamp, // Date | null
  parseAsIsoDateTime, // Date | null
} from 'nuqs'
```

### Examples

```typescript
// String
const [search, setSearch] = useQueryState('q', parseAsString)

// Integer with default
const [page, setPage] = useQueryState('page', parseAsInteger.withDefault(1))

// Boolean
const [showFilters, setShowFilters] = useQueryState('filters', parseAsBoolean.withDefault(false))

// Array
const [tags, setTags] = useQueryState('tags', parseAsArrayOf(parseAsString).withDefault([]))

// JSON object
const [filters, setFilters] = useQueryState('filters', parseAsJson<FilterType>())
```

---

## History Options

```typescript
parseAsString.withOptions({
  history: 'push', // Create new history entry (back button works)
  history: 'replace', // Replace current entry (no back button)
})
```

| Option    | Use Case                        |
| --------- | ------------------------------- |
| `push`    | Navigation state (tabs, modals) |
| `replace` | Filters, search, pagination     |

---

## Centralized Query Params

```typescript
// src/common/constants.ts
export const appQueryParams = {
  // Auth
  error: 'error',
  step: 'step',

  // Pagination
  page: 'page',
  limit: 'limit',

  // Filters
  search: 'q',
  status: 'status',
  sortBy: 'sort',

  // Modals
  modal: 'modal',
  id: 'id',
} as const
```

```typescript
// Usage
import { appQueryParams } from '@/common/constants'

export const useQueryErrorState = () => {
  return useQueryState(
    appQueryParams.error, // Centralized param name
    parseAsStringLiteral(errorStates),
  )
}
```

---

## Common Patterns

### Tab Navigation

```typescript
const tabStates = ['overview', 'settings', 'billing'] as const
type TabState = (typeof tabStates)[number]

export const useQueryTab = () => {
  return useQueryState(
    'tab',
    parseAsStringLiteral(tabStates)
      .withDefault('overview')
      .withOptions({ history: 'push' }),
  )
}

// Component
function TabNavigation() {
  const [tab, setTab] = useQueryTab()

  return (
    <Tabs value={tab} onValueChange={setTab}>
      <TabsList>
        <TabsTrigger value='overview'>Overview</TabsTrigger>
        <TabsTrigger value='settings'>Settings</TabsTrigger>
        <TabsTrigger value='billing'>Billing</TabsTrigger>
      </TabsList>
    </Tabs>
  )
}
```

### Pagination

```typescript
export const useQueryPagination = () => {
  const [page, setPage] = useQueryState(
    'page',
    parseAsInteger.withDefault(1).withOptions({ history: 'replace' }),
  )
  const [limit, setLimit] = useQueryState(
    'limit',
    parseAsInteger.withDefault(10).withOptions({ history: 'replace' }),
  )

  return { page, setPage, limit, setLimit }
}
```

### Search with Debounce

```typescript
import { useQueryState } from 'nuqs'
import { useDebouncedCallback } from 'use-debounce'

export const useSearchQuery = () => {
  const [search, setSearch] = useQueryState('q', parseAsString.withOptions({ history: 'replace' }))

  const debouncedSetSearch = useDebouncedCallback(setSearch, 300)

  return { search, setSearch: debouncedSetSearch }
}
```

### Modal State

```typescript
const modalStates = ['create', 'edit', 'delete'] as const

export const useModalState = () => {
  const [modal, setModal] = useQueryState(
    'modal',
    parseAsStringLiteral(modalStates).withOptions({ history: 'push' }),
  )
  const [itemId, setItemId] = useQueryState('id', parseAsString.withOptions({ history: 'push' }))

  const openModal = (type: (typeof modalStates)[number], id?: string) => {
    setModal(type)
    if (id) setItemId(id)
  }

  const closeModal = () => {
    setModal(null)
    setItemId(null)
  }

  return { modal, itemId, openModal, closeModal }
}
```

---

## Server Component Usage

```typescript
// app/posts/page.tsx
import { SearchParams } from 'nuqs/server'

type PageProps = {
  searchParams: SearchParams
}

export default async function PostsPage({ searchParams }: PageProps) {
  const { page, q } = searchParams

  // Use params for server-side data fetching
  const posts = await getPosts({
    page: Number(page) || 1,
    search: q as string,
  })

  return <PostsList posts={posts} />
}
```

---

## Best Practices

1. **Centralize param names** in constants
2. **Use string literals** for type safety
3. **Choose history mode** based on UX needs
4. **Provide defaults** for required values
5. **Debounce** frequent updates (search)

---

## File Structure

```
src/
├── common/
│   └── constants.ts         # Centralized query param names
└── features/<feature>/
    └── hooks.ts             # Feature-specific URL state hooks
```
