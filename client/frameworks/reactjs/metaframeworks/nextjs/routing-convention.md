# Opinionated Next.js Routing Convention

This document defines the application-owned convention for constructing internal URLs, classifying route access, parsing route input, and managing shareable query state in a Next.js application.

The convention is durable. Exact Next.js and nuqs configuration keys, imports, types, and call shapes are version-sensitive and must be resolved from the target application's installed versions and current official documentation before implementation.

## Ownership Model

| Concern | Owner |
| --- | --- |
| Route existence, layouts, and route groups | Next.js route tree |
| Internal pathname construction | `appRoutes` |
| Pathname access classification | Route policy registry |
| Path and query input parsing | Page/layout boundary |
| Shareable query representation | Feature-owned nuqs parser map |
| Domain and cross-field validation | Feature/domain schema |
| Server data and query caching | TanStack Query or the selected server boundary |

These owners cooperate but do not replace one another. The route tree remains the source of route existence; `appRoutes` is the application API for constructing URLs that point into that tree.

## Application Placement

```text
src/
  common/
    routing/
      app-routes.ts
      route-policies.ts
  features/
    items/
      search-params.ts
      hooks.ts
  app/
    (protected)/
      items/
        [itemId]/page.tsx
        page.tsx
```

The routing registry and policies belong to the deployable Next.js application. A monorepo does not make them shared-package concerns. Extract a shared URL contract only when multiple deployables intentionally own the same public URL space.

## `appRoutes`

`appRoutes` is a named, application-wide API for internal pathnames:

- Represent static paths as literals.
- Represent dynamic paths as named builder functions.
- Encode every value inserted into a path segment.
- Group routes by user-facing area or capability, not by route-group folder names that do not appear in the URL.
- Use the registry in links, redirects, and router operations; do not concatenate internal paths at call sites.
- Keep query-string parsing and serialization out of pathname builders.
- Enable and use the installed Next.js version's typed-route support when available.

```typescript
// src/common/routing/app-routes.ts
import type { Route } from "next";

const staticRoute = <T extends Route>(href: T) => href;

export const appRoutes = {
  home: staticRoute("/"),
  auth: {
    login: staticRoute("/login"),
    signup: staticRoute("/signup"),
  },
  items: {
    index: staticRoute("/items"),
    detail: (itemId: string) =>
      `/items/${encodeURIComponent(itemId)}` as Route,
    edit: (itemId: string) =>
      `/items/${encodeURIComponent(itemId)}/edit` as Route,
  },
} as const;
```

Generated route types validate literals and framework navigation. Dynamic builders may still require a framework route assertion, so test their observable output rather than treating the assertion as proof of correctness.

## Route Policies

Do not overload `appRoutes` with request matching. URL construction and pathname classification have different shapes, especially for dynamic segments.

Keep a colocated route policy registry that:

- classifies public, guest-only, protected, owner, and administrative route families;
- matches complete path segments rather than unsafe string prefixes;
- is consumed by the framework's current request-interception boundary; and
- supports early redirects without becoming the authoritative capability-authorization layer.

Route groups and server layouts enforce session and shell boundaries. Server services or capability handlers remain authoritative for ownership, tenant, role, and resource authorization.

## Params and Page Boundaries

Pages and layouts are metaframework composition boundaries:

1. Read path and search parameters using the installed Next.js version's route-aware types and request API.
2. Parse their URL representation at that boundary.
3. Apply domain or cross-field validation after representation parsing.
4. Pass normalized, typed input into feature components.

Feature components must not know whether a value came from a dynamic segment, query parameter, header, or another framework-owned source.

## Query State with nuqs

Use nuqs for shareable, bookmarkable, non-sensitive interaction state such as filters, search, sorting, pagination, tabs, and navigation-like modal state.

Prefer one feature-owned parser map over a global bag of query-key strings. The parser map owns:

- domain-facing property names;
- URL key aliases;
- URL representation parsers;
- defaults and clearing behavior; and
- the serializer used to create links with query state.

Use the same parser map in client hooks, page-boundary loaders, and link serializers. Use a multi-key state hook when filters and pagination change as one unit. Reset pagination in the same URL update when a result-changing filter changes.

History behavior is intentional:

- replace for filters, search, sorting, and pagination;
- push for tabs or modal states when Back/Forward navigation improves the experience.

Client-cache-driven lists normally keep URL updates shallow and debounce only the free-text value used in the server-state query key. When the RSC tree must react to query changes, opt into server notification using the installed nuqs version's supported option and rate-limit free-text updates. Prefer a page-boundary loader; use request-local server search-parameter caching only when deeply nested Server Components genuinely need it.

Do not put secrets, large payloads, drafts, or disposable presentation state in the URL.

## Validation Boundary

nuqs and domain schemas have distinct responsibilities:

- nuqs parses and serializes the query-string representation;
- a domain or feature schema validates business constraints and relationships between values.

Do not duplicate primitive parsing in both layers. A successfully parsed URL representation is not proof that the resulting values satisfy domain rules.

## Verification Scenarios

Verify the convention with behavior, not only type assertions:

- A static route registry value points to an existing route.
- A dynamic builder encodes reserved characters in a segment.
- A filtered-list link round-trips through the feature parser map.
- Changing a result filter resets pagination atomically.
- Back/Forward navigation behaves intentionally for tabs and modals.
- Client-cache-driven query updates do not rerender the server tree accidentally.
- Server-driven query updates refresh the intended RSC boundary.
- Route policy matching does not classify a similarly prefixed pathname.
- Early route guarding and authoritative resource authorization remain separate.

Run the installed Next.js version's route type generation or production build, focused routing/query-state tests, and the relevant client boundary tests.

## Official Implementation References

- [Next.js TypeScript and typed routes](https://nextjs.org/docs/app/api-reference/config/typescript)
- [Next.js route-aware page props](https://nextjs.org/docs/app/api-reference/file-conventions/page)
- [nuqs adapters](https://nuqs.dev/docs/adapters)
- [nuqs multi-key state](https://nuqs.dev/docs/batching)
- [nuqs server-side parsing](https://nuqs.dev/docs/server-side)
- [nuqs serializers](https://nuqs.dev/docs/utilities)
- [nuqs options](https://nuqs.dev/docs/options)
