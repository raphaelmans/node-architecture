# URL Query State (nuqs)

nuqs provides type-safe URL query parameter state that:

- syncs state with URL automatically
- supports SSR
- provides type-safe parsers
- works with Next.js App Router

For deeper examples, see `client/drafts/06-nuqs-url-state.md`.

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

