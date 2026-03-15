# URL Query State (nuqs)

nuqs provides type-safe URL query parameter state that:

- syncs state with URL automatically
- supports SSR
- provides type-safe parsers
- works with Next.js App Router

For deeper historical examples, see `legacy/client/06-nuqs-url-state.md`.

## Setup

```typescript
// src/app/layout.tsx
import { NuqsAdapter } from "nuqs/adapters/next/app";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <NuqsAdapter>{children}</NuqsAdapter>
      </body>
    </html>
  );
}
```

## Basic Usage

```typescript
import { parseAsStringLiteral, useQueryState } from "nuqs";
import { appQueryParams } from "@/common/constants";

const tabs = ["overview", "settings", "billing"] as const;

export const useQueryTab = () => {
  return useQueryState(
    appQueryParams.tab,
    parseAsStringLiteral(tabs).withDefault("overview").withOptions({ history: "push" }),
  );
};
```

## Available Parsers

```typescript
import {
  parseAsString,
  parseAsInteger,
  parseAsFloat,
  parseAsBoolean,
  parseAsStringLiteral,
  parseAsArrayOf,
  parseAsJson,
} from "nuqs";
```

## History Modes

| Mode      | Behavior               | Use Case                         |
| --------- | ---------------------- | -------------------------------- |
| `push`    | Creates history entry  | Tabs, modals (back button works) |
| `replace` | Replaces current entry | Filters, search, pagination      |

## Centralized Param Names

Centralize param names to prevent drift:

```typescript
// src/common/constants.ts
export const appQueryParams = {
  page: "page",
  limit: "limit",
  search: "q",
  status: "status",
  sort: "sort",
  tab: "tab",
  modal: "modal",
  id: "id",
} as const;
```

## Filters + Search + Pagination Pattern

nuqs is the canonical mechanism for all user-facing filter, search, and pagination state. This keeps URLs shareable and supports browser back/forward navigation.

```typescript
// Feature filter hook
export function useItemFilters() {
  const [status, setStatus] = useQueryState("status", parseAsStringLiteral(STATUSES));
  const [sort, setSort] = useQueryState("sort", parseAsStringLiteral(SORT_OPTIONS).withDefault("newest"));
  const [search, setSearch] = useQueryState("q", parseAsString.withDefault(""));
  const [page, setPage] = useQueryState("page", parseAsInteger.withDefault(1));

  const debouncedSearch = useDebounce(search, 300);

  return { status, setStatus, sort, setSort, search, setSearch, debouncedSearch, page, setPage };
}
```

Rules:

- All filter/search/pagination state in URL — never in React state or Zustand for filterable lists
- Use `replace` history mode for filters (don't pollute browser history)
- Debounce text search at 300ms before passing to TanStack Query
- Reset page to 1 when filters change

See `client/core/server-state-tanstack-query.md` for the TanStack Query integration pattern.
