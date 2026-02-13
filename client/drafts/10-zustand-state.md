# Zustand State Management

This guide covers client-side state management patterns using Zustand.

---

## Dependencies

```json
{
  "zustand": "^5.0.3"
}
```

---

## When to Use Zustand

| Use Case                | Solution                     |
| ----------------------- | ---------------------------- |
| Server state (API data) | TanStack Query + tRPC        |
| URL state               | nuqs                         |
| Form state              | react-hook-form              |
| Global UI state         | Zustand                      |
| Complex local state     | Zustand                      |
| Persisted client state  | Zustand + persist middleware |

---

## Store Patterns

### Pattern 1: Global Store (Singleton)

For app-wide state that doesn't need isolation:

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
      setVideoDevices: devices => set({ videoDevices: devices }),
      setAudioDevices: devices => set({ audioDevices: devices }),

      setSelectedVideoDevice: deviceId => {
        const device = get().videoDevices.find(d => d.deviceId === deviceId)
        if (device) {
          set({ selectedVideoDeviceId: device.deviceId })
        }
      },

      setSelectedAudioDevice: deviceId => {
        const device = get().audioDevices.find(d => d.deviceId === deviceId)
        if (device) {
          set({ selectedAudioDeviceId: device.deviceId })
        }
      },

      setDevices: devices => {
        const { selectedVideoDeviceId, selectedAudioDeviceId } = get()
        set({
          videoDevices: devices.videoDevices,
          audioDevices: devices.audioDevices,
          isInitialized: true,
          // Default to first device if none selected
          selectedVideoDeviceId: selectedVideoDeviceId || devices.videoDevices.at(0)?.deviceId,
          selectedAudioDeviceId: selectedAudioDeviceId || devices.audioDevices.at(0)?.deviceId,
        })
      },
    }),
    {
      name: 'media-selection-storage',
      storage: createJSONStorage(() => localStorage),
      // Only persist specific fields
      partialize: state => ({
        selectedVideoDeviceId: state.selectedVideoDeviceId,
        selectedAudioDeviceId: state.selectedAudioDeviceId,
      }),
    },
  ),
)
```

**Usage:**

```typescript
// Direct hook usage
const selectedVideoDeviceId = useMediaSelectionStore(state => state.selectedVideoDeviceId)
const setSelectedVideoDevice = useMediaSelectionStore(state => state.setSelectedVideoDevice)

// Multiple selectors with useShallow (prevents unnecessary re-renders)
import { useShallow } from 'zustand/shallow'

const { videoDevices, selectedVideoDeviceId } = useMediaSelectionStore(
  useShallow(state => ({
    videoDevices: state.videoDevices,
    selectedVideoDeviceId: state.selectedVideoDeviceId,
  })),
)
```

---

### Pattern 2: Context Store (Isolated per Provider)

For state that needs to be isolated per component tree (e.g., multiple instances):

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
  setActiveCustomerProfile: (profile?: TargetCustomerState['activeCustomerProfile']) => void
  setIsGenerating: (v: boolean) => void
  reset: () => void
}

// 2. Create store factory (not a hook!)
export const createTargetCustomerStore = (initialActiveCustomerId?: string) =>
  create<TargetCustomerState>(set => ({
    activeCustomerId: initialActiveCustomerId,
    activeCustomerProfile: undefined,
    isGenerating: false,

    setActiveCustomerId: id => set({ activeCustomerId: id }),
    setActiveCustomerProfile: p => set({ activeCustomerProfile: p }),
    setIsGenerating: v => set({ isGenerating: v }),
    reset: () => set({ activeCustomerId: undefined, activeCustomerProfile: undefined }),
  }))

// 3. Create context
export type TargetCustomerStoreAPI = ReturnType<typeof createTargetCustomerStore>
export const TargetCustomerStoreContext = createContext<TargetCustomerStoreAPI | null>(null)

// 4. Create typed selector hook
export const useTargetCustomerInContext = <T>(selector: (s: TargetCustomerState) => T): T => {
  const store = useContext(TargetCustomerStoreContext)
  if (!store) {
    throw new Error(
      'useTargetCustomerInContext must be used within TargetCustomerStoreContext.Provider',
    )
  }
  return useStore(store, selector)
}
```

**Provider Setup:**

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
  initialCustomerId
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

**Usage:**

```typescript
// Wrap component tree
<TargetCustomerProvider initialCustomerId={customerId}>
  <CustomerDashboard />
</TargetCustomerProvider>

// Consume in child components
function CustomerDashboard() {
  const activeCustomerId = useTargetCustomerInContext(s => s.activeCustomerId)
  const setActiveCustomerId = useTargetCustomerInContext(s => s.setActiveCustomerId)

  return (
    <div>
      <p>Active: {activeCustomerId}</p>
      <button onClick={() => setActiveCustomerId('new-id')}>
        Change Customer
      </button>
    </div>
  )
}
```

---

## Conventions

### State Shape

```typescript
type StoreState = {
  // Group: State values
  value1: string
  value2: number
  isLoading: boolean

  // Group: Actions (setters)
  setValue1: (v: string) => void
  setValue2: (v: number) => void
  setIsLoading: (v: boolean) => void

  // Group: Complex actions
  reset: () => void
  fetchAndSet: () => Promise<void>
}
```

### Naming Conventions

| Type              | Convention                          | Example                      |
| ----------------- | ----------------------------------- | ---------------------------- |
| Store file        | `<feature>-store.ts` or `stores.ts` | `target-customer-store.ts`   |
| Global store hook | `use<Name>Store`                    | `useMediaSelectionStore`     |
| Store factory     | `create<Name>Store`                 | `createTargetCustomerStore`  |
| Context           | `<Name>StoreContext`                | `TargetCustomerStoreContext` |
| Context hook      | `use<Name>InContext`                | `useTargetCustomerInContext` |

### Selector Best Practices

```typescript
// Good: Single selector
const count = useStore(state => state.count)

// Good: Multiple values with useShallow
import { useShallow } from 'zustand/shallow'

const { count, name } = useStore(useShallow(state => ({ count: state.count, name: state.name })))

// Bad: Selecting entire state (causes re-render on any change)
const state = useStore(state => state) // Avoid!
```

---

## Persist Middleware

For persisting state to localStorage:

```typescript
import { persist, createJSONStorage } from 'zustand/middleware'

export const usePersistedStore = create<State>()(
  persist(
    (set, get) => ({
      // ... state and actions
    }),
    {
      name: 'store-key', // localStorage key
      storage: createJSONStorage(() => localStorage),

      // Only persist specific fields
      partialize: state => ({
        selectedId: state.selectedId,
        preferences: state.preferences,
      }),

      // Migration for schema changes
      version: 1,
      migrate: (persistedState, version) => {
        if (version === 0) {
          // Migrate from v0 to v1
          return { ...persistedState, newField: 'default' }
        }
        return persistedState
      },
    },
  ),
)
```

---

## File Structure

```
src/features/<feature>/
├── stores/
│   ├── <name>-store.ts       # Context-based store
│   └── index.ts              # Barrel export
├── stores.ts                 # Or single file for simple stores
└── components/
    └── <name>-provider.tsx   # Provider component
```

---

## When to Use Each Pattern

| Pattern                | Use When                                      |
| ---------------------- | --------------------------------------------- |
| **Global Store**       | Single instance needed, app-wide state        |
| **Context Store**      | Multiple instances, isolated state per tree   |
| **Persist Middleware** | State should survive page refresh             |
| **useShallow**         | Selecting multiple values, prevent re-renders |
