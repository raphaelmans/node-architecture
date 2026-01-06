---
name: frontend-state
description: Implement client state with nuqs URL state and Zustand stores
---

# Frontend State Management

Use this skill when implementing client-side state management.

## When to Use

| State Type | Solution | Use This Skill |
|------------|----------|----------------|
| Server data (API) | TanStack Query + tRPC | No - use `frontend-data` |
| URL state | nuqs | Yes |
| Form state | react-hook-form | No - use `frontend-form` |
| Global UI state | Zustand | Yes |
| Complex local state | Zustand | Yes |
| Persisted client state | Zustand + persist | Yes |

## Part 1: nuqs URL State

### When to Use nuqs

- Tab navigation (shareable URLs)
- Pagination
- Search/filter parameters
- Modal state (deep-linkable)
- Multi-step flows

### Steps

#### 1. Define the State Type

```typescript
// src/features/<feature>/hooks.ts
const tabStates = ['overview', 'settings', 'billing'] as const
type TabState = (typeof tabStates)[number]
```

#### 2. Create the Hook

```typescript
import { parseAsStringLiteral, useQueryState } from 'nuqs'

export const useQueryTab = () => {
  return useQueryState(
    'tab',  // URL param name: ?tab=overview
    parseAsStringLiteral(tabStates)
      .withDefault('overview')
      .withOptions({ history: 'push' })
  )
}
```

#### 3. Use in Component

```typescript
function TabNavigation() {
  const [tab, setTab] = useQueryTab()

  return (
    <Tabs value={tab} onValueChange={setTab}>
      <TabsList>
        <TabsTrigger value='overview'>Overview</TabsTrigger>
        <TabsTrigger value='settings'>Settings</TabsTrigger>
      </TabsList>
    </Tabs>
  )
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
  parseAsString,          // string | null
  parseAsInteger,         // number | null
  parseAsBoolean,         // boolean | null
  parseAsStringLiteral,   // union type | null
  parseAsArrayOf,         // array | null
} from 'nuqs'
```

---

## Part 2: Zustand Stores

### Pattern 1: Global Store (Singleton)

For app-wide state:

#### 1. Create the Store

```typescript
// src/features/<feature>/stores.ts
'use client'

import { create } from 'zustand'

type ThemeState = {
  // State
  theme: 'light' | 'dark'
  sidebarOpen: boolean
  
  // Actions
  setTheme: (theme: 'light' | 'dark') => void
  toggleSidebar: () => void
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: 'light',
  sidebarOpen: true,
  
  setTheme: (theme) => set({ theme }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}))
```

#### 2. Use in Components

```typescript
// Select single value
const theme = useThemeStore((state) => state.theme)
const setTheme = useThemeStore((state) => state.setTheme)

// Select multiple with useShallow (prevents re-renders)
import { useShallow } from 'zustand/shallow'

const { theme, sidebarOpen } = useThemeStore(
  useShallow((state) => ({
    theme: state.theme,
    sidebarOpen: state.sidebarOpen,
  }))
)
```

### Pattern 2: Context Store (Isolated)

For state that needs multiple instances:

#### 1. Create Store Factory

```typescript
// src/features/<feature>/stores/<name>-store.ts
'use client'

import { createContext, useContext } from 'react'
import { create, useStore } from 'zustand'

type CustomerState = {
  activeId: string | undefined
  setActiveId: (id: string | undefined) => void
}

// Store factory (not a hook!)
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
  if (!store) {
    throw new Error('useCustomerStore must be used within CustomerStoreContext.Provider')
  }
  return useStore(store, selector)
}
```

#### 2. Create Provider

```typescript
// src/features/<feature>/components/<name>-provider.tsx
'use client'

import { useRef } from 'react'
import { createCustomerStore, CustomerStoreContext, CustomerStoreAPI } from '../stores/<name>-store'

export function CustomerProvider({ 
  children, 
  initialId 
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
```

#### 3. Use in Component Tree

```typescript
// Wrap
<CustomerProvider initialId={customerId}>
  <CustomerDashboard />
</CustomerProvider>

// Consume
function CustomerDashboard() {
  const activeId = useCustomerStore((s) => s.activeId)
  const setActiveId = useCustomerStore((s) => s.setActiveId)
  // ...
}
```

### Pattern 3: Persisted Store

For state that survives page refresh:

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
      name: 'preferences-storage',  // localStorage key
      storage: createJSONStorage(() => localStorage),
      // Only persist specific fields
      partialize: (state) => ({
        selectedDeviceId: state.selectedDeviceId,
      }),
    }
  )
)
```

## Checklist

### nuqs
- [ ] Hook defined in `features/<feature>/hooks.ts`
- [ ] Uses appropriate parser for data type
- [ ] Uses `withDefault()` for required values
- [ ] Uses correct history option (push vs replace)

### Zustand
- [ ] Store defined in `features/<feature>/stores.ts` or `stores/` folder
- [ ] State and actions clearly separated in type
- [ ] Uses selector pattern (not selecting entire state)
- [ ] Uses `useShallow` when selecting multiple values
- [ ] Context store has provider component if isolated instances needed

## References

See `references/state-patterns.md` for detailed patterns.
