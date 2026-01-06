# State Management Patterns Reference

## nuqs URL State Patterns

### Tab Navigation

```typescript
// src/features/dashboard/hooks.ts
import { parseAsStringLiteral, useQueryState } from 'nuqs'

const tabStates = ['overview', 'settings', 'billing'] as const
type TabState = (typeof tabStates)[number]

export const useQueryTab = () => {
  return useQueryState(
    'tab',
    parseAsStringLiteral(tabStates)
      .withDefault('overview')
      .withOptions({ history: 'push' })
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
import { useQueryState } from 'nuqs'
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

### Multi-Step Flow

```typescript
const landingStates = ['login', 'signup', 'verify'] as const
export type LandingState = (typeof landingStates)[number]

export const useQueryLandingState = () => {
  return useQueryState(
    'step',
    parseAsStringLiteral(landingStates).withOptions({ history: 'push' })
  )
}

// Component
function LandingFlow() {
  const [step, setStep] = useQueryLandingState()

  switch (step) {
    case 'login':
      return <LoginForm onSignup={() => setStep('signup')} />
    case 'signup':
      return <SignupForm onVerify={() => setStep('verify')} />
    case 'verify':
      return <VerifyForm />
    default:
      return <LoginForm onSignup={() => setStep('signup')} />
  }
}
```

### Error State

```typescript
const errorStates = ['email-used', 'invalid-token', 'expired'] as const
export type ErrorState = (typeof errorStates)[number]

export const useQueryErrorState = () => {
  return useQueryState(
    'error',
    parseAsStringLiteral(errorStates).withOptions({ history: 'push' })
  )
}
```

### Centralized Query Param Names

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

// Usage
import { appQueryParams } from '@/common/constants'

export const useQueryErrorState = () => {
  return useQueryState(
    appQueryParams.error,
    parseAsStringLiteral(errorStates)
  )
}
```

---

## Zustand Store Patterns

### Global Store (Full Example)

```typescript
// src/features/video-infra/stores.ts
'use client'

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

type MediaSelectionState = {
  // State
  videoDevices: MediaDeviceInfo[]
  audioDevices: MediaDeviceInfo[]
  selectedVideoDeviceId: string | null
  selectedAudioDeviceId: string | null
  isInitialized: boolean

  // Actions
  setVideoDevices: (devices: MediaDeviceInfo[]) => void
  setAudioDevices: (devices: MediaDeviceInfo[]) => void
  setSelectedVideoDevice: (deviceId: string) => void
  setSelectedAudioDevice: (deviceId: string) => void
  setDevices: (devices: {
    videoDevices: MediaDeviceInfo[]
    audioDevices: MediaDeviceInfo[]
  }) => void
}

export const useMediaSelectionStore = create<MediaSelectionState>()(
  persist(
    (set, get) => ({
      // Initial state
      videoDevices: [],
      audioDevices: [],
      selectedVideoDeviceId: null,
      selectedAudioDeviceId: null,
      isInitialized: false,

      // Actions
      setVideoDevices: (devices) => set({ videoDevices: devices }),
      setAudioDevices: (devices) => set({ audioDevices: devices }),

      setSelectedVideoDevice: (deviceId) => {
        const device = get().videoDevices.find((d) => d.deviceId === deviceId)
        if (device) {
          set({ selectedVideoDeviceId: device.deviceId })
        }
      },

      setSelectedAudioDevice: (deviceId) => {
        const device = get().audioDevices.find((d) => d.deviceId === deviceId)
        if (device) {
          set({ selectedAudioDeviceId: device.deviceId })
        }
      },

      setDevices: (devices) => {
        const { selectedVideoDeviceId, selectedAudioDeviceId } = get()
        set({
          videoDevices: devices.videoDevices,
          audioDevices: devices.audioDevices,
          isInitialized: true,
          selectedVideoDeviceId:
            selectedVideoDeviceId || devices.videoDevices.at(0)?.deviceId,
          selectedAudioDeviceId:
            selectedAudioDeviceId || devices.audioDevices.at(0)?.deviceId,
        })
      },
    }),
    {
      name: 'media-selection-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        selectedVideoDeviceId: state.selectedVideoDeviceId,
        selectedAudioDeviceId: state.selectedAudioDeviceId,
      }),
    }
  )
)
```

### Context Store (Full Example)

```typescript
// src/features/daily-brief-feed/stores/target-customer-store.ts
'use client'

import { createContext, useContext } from 'react'
import { create, useStore } from 'zustand'

// 1. Define state type
type TargetCustomerState = {
  activeCustomerId: string | undefined
  activeCustomerProfile?: {
    id: string
    name: string
    description?: string | null
  }
  isGenerating: boolean

  setActiveCustomerId: (id: string | undefined) => void
  setActiveCustomerProfile: (
    profile?: TargetCustomerState['activeCustomerProfile']
  ) => void
  setIsGenerating: (v: boolean) => void
  reset: () => void
}

// 2. Create store factory
export const createTargetCustomerStore = (initialActiveCustomerId?: string) =>
  create<TargetCustomerState>((set) => ({
    activeCustomerId: initialActiveCustomerId,
    activeCustomerProfile: undefined,
    isGenerating: false,

    setActiveCustomerId: (id) => set({ activeCustomerId: id }),
    setActiveCustomerProfile: (p) => set({ activeCustomerProfile: p }),
    setIsGenerating: (v) => set({ isGenerating: v }),
    reset: () =>
      set({ activeCustomerId: undefined, activeCustomerProfile: undefined }),
  }))

// 3. Create context
export type TargetCustomerStoreAPI = ReturnType<typeof createTargetCustomerStore>
export const TargetCustomerStoreContext =
  createContext<TargetCustomerStoreAPI | null>(null)

// 4. Create typed selector hook
export const useTargetCustomerInContext = <T>(
  selector: (s: TargetCustomerState) => T
): T => {
  const store = useContext(TargetCustomerStoreContext)
  if (!store) {
    throw new Error(
      'useTargetCustomerInContext must be used within TargetCustomerStoreContext.Provider'
    )
  }
  return useStore(store, selector)
}
```

### Provider Component

```typescript
// src/features/daily-brief-feed/components/target-customer-provider.tsx
'use client'

import { useRef } from 'react'
import {
  createTargetCustomerStore,
  TargetCustomerStoreContext,
  TargetCustomerStoreAPI,
} from '../stores/target-customer-store'

interface TargetCustomerProviderProps {
  children: React.ReactNode
  initialCustomerId?: string
}

export function TargetCustomerProvider({
  children,
  initialCustomerId,
}: TargetCustomerProviderProps) {
  // Create store once, preserve across re-renders
  const storeRef = useRef<TargetCustomerStoreAPI>()
  if (!storeRef.current) {
    storeRef.current = createTargetCustomerStore(initialCustomerId)
  }

  return (
    <TargetCustomerStoreContext.Provider value={storeRef.current}>
      {children}
    </TargetCustomerStoreContext.Provider>
  )
}
```

---

## Selector Best Practices

### Single Value

```typescript
// Good: Single selector
const count = useStore((state) => state.count)
const setCount = useStore((state) => state.setCount)
```

### Multiple Values

```typescript
// Good: Multiple values with useShallow
import { useShallow } from 'zustand/shallow'

const { count, name } = useStore(
  useShallow((state) => ({
    count: state.count,
    name: state.name,
  }))
)
```

### Anti-Patterns

```typescript
// Bad: Selecting entire state (causes re-render on any change)
const state = useStore((state) => state) // Avoid!

// Bad: Multiple separate calls without useShallow when values are related
const count = useStore((state) => state.count)
const name = useStore((state) => state.name)  // May cause extra re-renders
```

---

## Persist Middleware Options

```typescript
import { persist, createJSONStorage } from 'zustand/middleware'

export const usePersistedStore = create<State>()(
  persist(
    (set, get) => ({
      // state and actions
    }),
    {
      // Required: localStorage key
      name: 'store-key',
      
      // Storage type
      storage: createJSONStorage(() => localStorage),

      // Only persist specific fields
      partialize: (state) => ({
        selectedId: state.selectedId,
        preferences: state.preferences,
      }),

      // Migration for schema changes
      version: 1,
      migrate: (persistedState, version) => {
        if (version === 0) {
          return { ...persistedState, newField: 'default' }
        }
        return persistedState
      },
    }
  )
)
```

---

## File Structure

```
src/features/<feature>/
├── hooks.ts                  # nuqs hooks
├── stores.ts                 # Simple global stores
├── stores/                   # Complex/context stores
│   ├── <name>-store.ts
│   └── index.ts
└── components/
    └── <name>-provider.tsx   # Context store provider
```

---

## When to Use Each Pattern

| Pattern | Use When |
|---------|----------|
| **nuqs** | State should be in URL (shareable, back button) |
| **Global Store** | Single instance needed, app-wide state |
| **Context Store** | Multiple instances, isolated state per component tree |
| **Persist Middleware** | State should survive page refresh |
| **useShallow** | Selecting multiple values to prevent re-renders |
