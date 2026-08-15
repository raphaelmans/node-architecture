# Zustand (Client State)

Use Zustand for **client coordination state** (UI state that is not server/IO state).

## When to Use

| Use Case                      | Solution                |
| ----------------------------- | ----------------------- |
| Server/IO data                | TanStack Query          |
| Form data                     | react-hook-form         |
| URL state                     | nuqs (Next.js)          |
| Global UI state               | Zustand (global store)  |
| Isolated component tree state | Zustand (context store) |

## Pattern 1: Global Store

For app-wide state (single instance):

```typescript
// src/features/media/stores/media-selection-store.ts
"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

type MediaSelectionState = {
  selectedVideoDeviceId: string | null;
  selectedAudioDeviceId: string | null;
  setSelectedVideoDevice: (id: string) => void;
  setSelectedAudioDevice: (id: string) => void;
};

export const useMediaSelectionStore = create<MediaSelectionState>()(
  persist(
    (set) => ({
      selectedVideoDeviceId: null,
      selectedAudioDeviceId: null,
      setSelectedVideoDevice: (id) => set({ selectedVideoDeviceId: id }),
      setSelectedAudioDevice: (id) => set({ selectedAudioDeviceId: id }),
    }),
    {
      name: "media-selection",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        selectedVideoDeviceId: state.selectedVideoDeviceId,
        selectedAudioDeviceId: state.selectedAudioDeviceId,
      }),
    },
  ),
);
```

## Pattern 2: Context Store

For isolated state per component tree (multiple instances):

```typescript
// src/features/customer/stores/customer-store.tsx
"use client";

import {
  createContext,
  useContext,
  useState,
  type PropsWithChildren,
} from "react";
import { useStore } from "zustand";
import { createStore } from "zustand/vanilla";

type CustomerState = {
  activeCustomerId: string | undefined;
  setActiveCustomerId: (id: string | undefined) => void;
  reset: () => void;
};

export const createCustomerStore = (initialCustomerId?: string) =>
  createStore<CustomerState>()((set) => ({
    activeCustomerId: initialCustomerId,
    setActiveCustomerId: (id) => set({ activeCustomerId: id }),
    reset: () => set({ activeCustomerId: undefined }),
  }));

export type CustomerStoreAPI = ReturnType<typeof createCustomerStore>;
export const CustomerStoreContext = createContext<CustomerStoreAPI | null>(null);

export function CustomerStoreProvider({
  initialCustomerId,
  children,
}: PropsWithChildren<{ initialCustomerId?: string }>) {
  const [store] = useState(() => createCustomerStore(initialCustomerId));
  return (
    <CustomerStoreContext.Provider value={store}>
      {children}
    </CustomerStoreContext.Provider>
  );
}

export const useCustomerInContext = <T>(selector: (s: CustomerState) => T): T => {
  const store = useContext(CustomerStoreContext);
  if (!store) {
    throw new Error("useCustomerInContext must be used within CustomerStoreContext.Provider");
  }
  return useStore(store, selector);
};
```

## Conventions

- Prefer selecting primitives over selecting entire state objects.
- Use `useShallow` when selecting multiple values to avoid unnecessary re-renders.
- Persisted stores must use `partialize` to avoid storing accidental data.
- In SSR applications, do not render persistence-dependent UI as authoritative until client hydration has completed; server markup cannot read browser storage.
