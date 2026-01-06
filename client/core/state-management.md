# State Management

> Patterns for URL state (nuqs) and client state (Zustand).

## State Decision Flow

```
What kind of state is this?
├── Server data (API) → TanStack Query via tRPC
├── Form data → react-hook-form
├── URL state (shareable, bookmarkable) → nuqs
├── Global client state → Zustand (global store)
└── Component tree state (isolated) → Zustand (context store)
```

## URL State (nuqs)

### Overview

nuqs provides type-safe URL query parameter state that:

- Syncs state with URL automatically
- Supports SSR
- Provides type-safe parsers
- Works with Next.js App Router

### Setup

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

### Basic Usage

```typescript
import { parseAsStringLiteral, useQueryState } from "nuqs";
import { appQueryParams } from "@/common/constants";

const tabs = ["overview", "settings", "billing"] as const;
type Tab = (typeof tabs)[number];

export const useQueryTab = () => {
  return useQueryState(
    appQueryParams.tab, // Centralized param name
    parseAsStringLiteral(tabs)
      .withDefault("overview")
      .withOptions({ history: "push" }),
  );
};

// Usage
const [tab, setTab] = useQueryTab();
// tab: 'overview' | 'settings' | 'billing'
// setTab('settings') → URL becomes ?tab=settings
```

### Available Parsers

```typescript
import {
  parseAsString, // string | null
  parseAsInteger, // number | null
  parseAsFloat, // number | null
  parseAsBoolean, // boolean | null
  parseAsStringLiteral, // union type | null
  parseAsArrayOf, // array | null
  parseAsJson, // JSON object | null
} from "nuqs";
```

### History Modes

| Mode      | Behavior               | Use Case                         |
| --------- | ---------------------- | -------------------------------- |
| `push`    | Creates history entry  | Tabs, modals (back button works) |
| `replace` | Replaces current entry | Filters, search, pagination      |

```typescript
parseAsString.withOptions({ history: "push" }); // Back button works
parseAsString.withOptions({ history: "replace" }); // No history entry
```

### Common Patterns

**Tab Navigation:**

```typescript
// src/features/settings/hooks.ts
const tabs = ["profile", "billing", "security"] as const;

export const useQuerySettingsTab = () => {
  return useQueryState(
    "tab",
    parseAsStringLiteral(tabs)
      .withDefault("profile")
      .withOptions({ history: "push" }),
  );
};
```

**Pagination:**

```typescript
export const useQueryPagination = () => {
  const [page, setPage] = useQueryState(
    "page",
    parseAsInteger.withDefault(1).withOptions({ history: "replace" }),
  );
  const [limit, setLimit] = useQueryState(
    "limit",
    parseAsInteger.withDefault(10).withOptions({ history: "replace" }),
  );
  return { page, setPage, limit, setLimit };
};
```

**Search:**

```typescript
export const useQuerySearch = () => {
  return useQueryState("q", parseAsString.withOptions({ history: "replace" }));
};
```

**Modal State:**

```typescript
const modals = ["create", "edit", "delete"] as const;

export const useQueryModal = () => {
  const [modal, setModal] = useQueryState(
    "modal",
    parseAsStringLiteral(modals).withOptions({ history: "push" }),
  );
  const [itemId, setItemId] = useQueryState(
    "id",
    parseAsString.withOptions({ history: "push" }),
  );

  const openModal = (type: (typeof modals)[number], id?: string) => {
    setModal(type);
    if (id) setItemId(id);
  };

  const closeModal = () => {
    setModal(null);
    setItemId(null);
  };

  return { modal, itemId, openModal, closeModal };
};
```

### Centralized Param Names

```typescript
// src/common/constants.ts
export const appQueryParams = {
  // Auth
  error: "error",
  step: "step",

  // Pagination
  page: "page",
  limit: "limit",

  // Search & Filters
  search: "q",
  status: "status",
  sort: "sort",

  // UI State
  tab: "tab",
  modal: "modal",
  id: "id",
} as const;
```

---

## Client State (Zustand)

### When to Use

| Use Case                      | Solution                |
| ----------------------------- | ----------------------- |
| Server data                   | TanStack Query          |
| Form data                     | react-hook-form         |
| URL state                     | nuqs                    |
| Global UI state               | Zustand (global store)  |
| Isolated component tree state | Zustand (context store) |

### Pattern 1: Global Store

For app-wide state (single instance):

```typescript
// src/features/media/stores.ts
"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

type MediaSelectionState = {
  // State
  selectedVideoDeviceId: string | null;
  selectedAudioDeviceId: string | null;

  // Actions
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

**Usage:**

```typescript
// Select single value
const selectedVideoDeviceId = useMediaSelectionStore(
  (s) => s.selectedVideoDeviceId,
);

// Select multiple values (prevent re-renders)
import { useShallow } from "zustand/shallow";

const { selectedVideoDeviceId, selectedAudioDeviceId } = useMediaSelectionStore(
  useShallow((s) => ({
    selectedVideoDeviceId: s.selectedVideoDeviceId,
    selectedAudioDeviceId: s.selectedAudioDeviceId,
  })),
);
```

### Pattern 2: Context Store

For isolated state per component tree (multiple instances):

```typescript
// src/features/customer/stores/customer-store.ts
"use client";

import { createContext, useContext } from "react";
import { create, useStore } from "zustand";

// 1. Define state type
type CustomerState = {
  activeCustomerId: string | undefined;
  setActiveCustomerId: (id: string | undefined) => void;
  reset: () => void;
};

// 2. Create store factory
export const createCustomerStore = (initialCustomerId?: string) =>
  create<CustomerState>((set) => ({
    activeCustomerId: initialCustomerId,
    setActiveCustomerId: (id) => set({ activeCustomerId: id }),
    reset: () => set({ activeCustomerId: undefined }),
  }));

// 3. Create context
export type CustomerStoreAPI = ReturnType<typeof createCustomerStore>;
export const CustomerStoreContext = createContext<CustomerStoreAPI | null>(
  null,
);

// 4. Create typed hook
export const useCustomerInContext = <T>(
  selector: (s: CustomerState) => T,
): T => {
  const store = useContext(CustomerStoreContext);
  if (!store) {
    throw new Error(
      "useCustomerInContext must be used within CustomerStoreContext.Provider",
    );
  }
  return useStore(store, selector);
};
```

**Provider:**

```typescript
// src/features/customer/components/customer-provider.tsx
'use client'

import { useRef } from 'react'
import { createCustomerStore, CustomerStoreContext, CustomerStoreAPI } from '../stores/customer-store'

export function CustomerProvider({
  children,
  initialCustomerId,
}: {
  children: React.ReactNode
  initialCustomerId?: string
}) {
  const storeRef = useRef<CustomerStoreAPI>()
  if (!storeRef.current) {
    storeRef.current = createCustomerStore(initialCustomerId)
  }

  return (
    <CustomerStoreContext.Provider value={storeRef.current}>
      {children}
    </CustomerStoreContext.Provider>
  )
}
```

**Usage:**

```typescript
// Wrap component tree
<CustomerProvider initialCustomerId={customerId}>
  <CustomerDashboard />
</CustomerProvider>

// Consume in children
function CustomerDashboard() {
  const activeCustomerId = useCustomerInContext(s => s.activeCustomerId)
  const setActiveCustomerId = useCustomerInContext(s => s.setActiveCustomerId)

  return (
    <button onClick={() => setActiveCustomerId('new-id')}>
      Change Customer
    </button>
  )
}
```

### Naming Conventions

| Type              | Convention           | Example                  |
| ----------------- | -------------------- | ------------------------ |
| Store file        | `<name>-store.ts`    | `customer-store.ts`      |
| Global store hook | `use<Name>Store`     | `useMediaSelectionStore` |
| Store factory     | `create<Name>Store`  | `createCustomerStore`    |
| Context           | `<Name>StoreContext` | `CustomerStoreContext`   |
| Context hook      | `use<Name>InContext` | `useCustomerInContext`   |

### Persist Middleware

```typescript
import { persist, createJSONStorage } from "zustand/middleware";

create<State>()(
  persist(
    (set) => ({
      /* ... */
    }),
    {
      name: "storage-key",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Only persist specific fields
        field1: state.field1,
      }),
    },
  ),
);
```

### useShallow for Multiple Selectors

```typescript
import { useShallow } from "zustand/shallow";

// Without useShallow - re-renders on ANY state change
const state = useStore((s) => ({ a: s.a, b: s.b })); // Bad

// With useShallow - only re-renders when a or b changes
const state = useStore(useShallow((s) => ({ a: s.a, b: s.b }))); // Good
```

---

## Conventions Summary

| State Type          | Solution        | Location                       |
| ------------------- | --------------- | ------------------------------ |
| Server data         | TanStack Query  | tRPC hooks in components       |
| Form data           | react-hook-form | Feature components             |
| URL state           | nuqs            | `features/<feature>/hooks.ts`  |
| Global client state | Zustand global  | `features/<feature>/stores.ts` |
| Isolated tree state | Zustand context | `features/<feature>/stores/`   |

## Checklist

- [ ] URL state uses centralized param names from `constants.ts`
- [ ] nuqs hooks defined in feature `hooks.ts`
- [ ] Zustand stores use selectors (avoid selecting entire state)
- [ ] Multiple selections use `useShallow`
- [ ] Context stores use `useRef` for stable reference
- [ ] Persisted state uses `partialize` to limit what's stored
