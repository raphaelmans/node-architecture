---
name: frontend-state
description: Implement client state with nuqs URL state and Zustand stores in Next.js projects
---

# Frontend State Management

Use this skill when implementing client-side state management.

## State Type Decision

| State Type | Solution | Skill |
|------------|----------|-------|
| Server data (API) | TanStack Query + tRPC | `frontend-data` |
| URL state | nuqs | This skill |
| Form state | react-hook-form | `frontend-form` |
| Global UI state | Zustand | This skill |
| Persisted client state | Zustand + persist | This skill |

## Part 1: nuqs URL State

Use for shareable, bookmarkable state.

### Tab Navigation

```typescript
// src/features/<feature>/hooks.ts
import { parseAsStringLiteral, useQueryState } from 'nuqs'

const tabs = ['overview', 'settings', 'billing'] as const

export const useQueryTab = () => {
  return useQueryState(
    'tab', // URL param: ?tab=overview
    parseAsStringLiteral(tabs).withDefault('overview').withOptions({ history: 'push' })
  )
}

// Component
function TabNavigation() {
  const [tab, setTab] = useQueryTab()

  return (
    <Tabs value={tab} onValueChange={setTab}>
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="settings">Settings</TabsTrigger>
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
    parseAsInteger.withDefault(1).withOptions({ history: 'replace' })
  )
  const [limit, setLimit] = useQueryState(
    'limit',
    parseAsInteger.withDefault(10).withOptions({ history: 'replace' })
  )
  return { page, setPage, limit, setLimit }
}
```

### Search with Debounce

```typescript
import { useDebouncedCallback } from 'use-debounce'

export const useSearchQuery = () => {
  const [search, setSearch] = useQueryState(
    'q',
    parseAsString.withOptions({ history: 'replace' })
  )

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
    parseAsStringLiteral(modalStates).withOptions({ history: 'push' })
  )
  const [itemId, setItemId] = useQueryState(
    'id',
    parseAsString.withOptions({ history: 'push' })
  )

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

### History Options

| Option | Behavior | Use Case |
|--------|----------|----------|
| `push` | Creates history entry | Tabs, modals, navigation |
| `replace` | Replaces current entry | Search, filters, pagination |

### Available Parsers

```typescript
import {
  parseAsString, // string | null
  parseAsInteger, // number | null
  parseAsBoolean, // boolean | null
  parseAsStringLiteral, // union type | null
  parseAsArrayOf, // array | null
} from 'nuqs'
```

## Part 2: Zustand Stores

### Pattern 1: Global Store (Singleton)

```typescript
// src/features/<feature>/stores.ts
'use client'

import { create } from 'zustand'

type ThemeState = {
  theme: 'light' | 'dark'
  sidebarOpen: boolean
  setTheme: (theme: 'light' | 'dark') => void
  toggleSidebar: () => void
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: 'light',
  sidebarOpen: true,
  setTheme: (theme) => set({ theme }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}))

// Usage - select single value
const theme = useThemeStore((s) => s.theme)

// Usage - select multiple with useShallow
import { useShallow } from 'zustand/shallow'

const { theme, sidebarOpen } = useThemeStore(
  useShallow((s) => ({ theme: s.theme, sidebarOpen: s.sidebarOpen }))
)
```

### Pattern 2: Context Store (Isolated)

For state that needs multiple instances per component tree.

```typescript
// src/features/<feature>/stores/<name>-store.ts
'use client'

import { createContext, useContext } from 'react'
import { create, useStore } from 'zustand'

type CustomerState = {
  activeId: string | undefined
  setActiveId: (id: string | undefined) => void
}

// Store factory
export const createCustomerStore = (initialId?: string) =>
  create<CustomerState>((set) => ({
    activeId: initialId,
    setActiveId: (id) => set({ activeId: id }),
  }))

// Context
export type CustomerStoreAPI = ReturnType<typeof createCustomerStore>
export const CustomerStoreContext = createContext<CustomerStoreAPI | null>(null)

// Hook
export const useCustomerStore = <T>(selector: (s: CustomerState) => T): T => {
  const store = useContext(CustomerStoreContext)
  if (!store) throw new Error('Must be used within CustomerStoreContext.Provider')
  return useStore(store, selector)
}
```

```typescript
// Provider
export function CustomerProvider({
  children,
  initialId,
}: {
  children: React.ReactNode
  initialId?: string
}) {
  const storeRef = useRef<CustomerStoreAPI>()
  if (!storeRef.current) {
    storeRef.current = createCustomerStore(initialId)
  }

  return (
    <CustomerStoreContext.Provider value={storeRef.current}>
      {children}
    </CustomerStoreContext.Provider>
  )
}

// Usage
<CustomerProvider initialId={id}>
  <CustomerDashboard />
</CustomerProvider>

function CustomerDashboard() {
  const activeId = useCustomerStore((s) => s.activeId)
}
```

### Pattern 3: Persisted Store

```typescript
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      selectedDeviceId: null,
      setSelectedDeviceId: (id) => set({ selectedDeviceId: id }),
    }),
    {
      name: 'preferences-storage', // localStorage key
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ selectedDeviceId: state.selectedDeviceId }),
    }
  )
)
```

## Checklist

### nuqs
- [ ] Hook in `features/<feature>/hooks.ts`
- [ ] Appropriate parser for data type
- [ ] `withDefault()` for required values
- [ ] Correct history option (push vs replace)

### Zustand
- [ ] Store in `features/<feature>/stores.ts`
- [ ] Uses selector pattern (not selecting entire state)
- [ ] Uses `useShallow` for multiple values
- [ ] Context store for isolated instances
