# URL Query State (nuqs)

nuqs is the documented Next.js specialization for typed, shareable query state. Use it for bookmarkable, non-sensitive filters, search, sorting, pagination, tabs, and navigation-like modal state.

The broader pathname, route-policy, and boundary convention lives in [Opinionated Next.js Routing Convention](./routing-convention.md). For deeper historical examples, see `legacy/client/06-nuqs-url-state.md`.

Before implementation, detect the installed nuqs and Next.js versions and retrieve their current official documentation. The examples below illustrate the current documented shape; vendor API names and options remain version-sensitive.

## Setup

Mount the App Router adapter once at the application root:

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

## Feature-Owned Parser Maps

Centralize the complete query representation, not only parameter-name strings. A feature-owned parser map defines domain-facing names, short URL keys, parsing, defaults, server loading, and link serialization in one place.

```typescript
// src/features/items/search-params.ts
import {
  createLoader,
  createSerializer,
  parseAsInteger,
  parseAsString,
  parseAsStringLiteral,
  type UrlKeys,
} from "nuqs/server";

const ITEM_STATUSES = ["active", "archived"] as const;
const ITEM_SORTS = ["newest", "oldest"] as const;

export const itemSearchParams = {
  search: parseAsString.withDefault(""),
  status: parseAsStringLiteral(ITEM_STATUSES),
  sort: parseAsStringLiteral(ITEM_SORTS).withDefault("newest"),
  page: parseAsInteger.withDefault(1),
};

export const itemSearchParamKeys: UrlKeys<typeof itemSearchParams> = {
  search: "q",
  status: "status",
  sort: "sort",
  page: "page",
};

export const loadItemSearchParams = createLoader(itemSearchParams);
export const serializeItemSearchParams = createSerializer(itemSearchParams, {
  urlKeys: itemSearchParamKeys,
});
```

Keep a global query-key registry only for parameters with genuinely application-wide semantics. Most filters belong to the feature that interprets them.

## Coupled Filters and Pagination

Use one multi-key hook when values form a single state unit:

```typescript
"use client";

import { useQueryStates } from "nuqs";
import {
  itemSearchParamKeys,
  itemSearchParams,
} from "./search-params";

export function useItemFilters() {
  const [filters, setFilters] = useQueryStates(itemSearchParams, {
    history: "replace",
    urlKeys: itemSearchParamKeys,
  });

  const setStatus = (status: typeof filters.status) =>
    setFilters({ status, page: 1 });

  const setSort = (sort: typeof filters.sort) =>
    setFilters({ sort, page: 1 });

  const setSearch = (search: string) =>
    setFilters({ search, page: 1 });

  return { filters, setFilters, setStatus, setSort, setSearch };
}
```

Related updates are applied as one URL transition. Reset pagination whenever a result-changing filter changes.

## History Behavior

| Mode | Use case |
| --- | --- |
| Replace | Filters, search, sorting, pagination |
| Push | Tabs or modal state when Back/Forward navigation is useful |

Push history only when the query state acts like navigation. Repeated filter edits must not pollute browser history.

## Server Boundary

Use the same parser map at the page boundary, then apply domain validation:

```typescript
// src/app/(protected)/items/page.tsx
import { ItemListInputSchema } from "@/features/items/schemas";
import { loadItemSearchParams } from "@/features/items/search-params";

export default async function ItemsPage(props: PageProps<"/items">) {
  const queryState = await loadItemSearchParams(props.searchParams);
  const input = ItemListInputSchema.parse(queryState);

  return <ItemList input={input} />;
}
```

nuqs owns query-string representation, defaults, and serialization. Zod or the selected feature/domain schema owns business and cross-field validity. A value accepted by a URL parser can still be invalid for the application.

Prefer a page-boundary loader and explicit typed input. Use nuqs request-local search-parameter caching only when deeply nested Server Components genuinely need access without prop passing.

## Link Serialization

Use the shared serializer to produce links with query state:

```typescript
import { appRoutes } from "@/common/routing/app-routes";
import { serializeItemSearchParams } from "@/features/items/search-params";

const archivedItemsHref = serializeItemSearchParams(appRoutes.items.index, {
  status: "archived",
  page: 1,
});
```

Do not manually concatenate query strings or maintain separate link-only serialization rules.

## Client-Cache versus Server-Driven Updates

nuqs query updates are client-local by default in its current Next.js integration. Choose behavior from the data owner:

- For TanStack Query-driven lists, keep updates client-local and debounce only the free-text value used in the query key. Include every result-changing parsed value in that key.
- If an RSC page must rerun when a query value changes, opt into the installed nuqs version's server-notification behavior and rate-limit free-text updates.
- Do not debounce select, toggle, tab, or pagination changes unless measured behavior justifies it.

## Limits

Do not store secrets, large payloads, drafts, or disposable presentation state in the URL. Use component state, a feature store, a form abstraction, or server state according to the state-ownership decision guide.

## Verification

- Parser defaults and clearing behavior are intentional.
- Client hooks and server loading use the same parser map.
- Serializer output round-trips through that parser map.
- Result-changing filters reset pagination atomically.
- Back/Forward behavior matches the selected history mode.
- Client-local updates do not accidentally rerender the RSC tree.
- Server-driven updates refresh the intended boundary without excessive requests.

See `client/core/server-state-tanstack-query.md` for query-key integration and testing guidance.

## Official References

- [nuqs adapters](https://nuqs.dev/docs/adapters)
- [nuqs multi-key state](https://nuqs.dev/docs/batching)
- [nuqs server-side usage](https://nuqs.dev/docs/server-side)
- [nuqs serializers](https://nuqs.dev/docs/utilities)
- [nuqs options](https://nuqs.dev/docs/options)
