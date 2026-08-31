# Next.js Routing Convention Leaf

Load this convention leaf only when a Next.js task involves internal URL construction, route policies, links or redirects, dynamic path builders, route params, search params, nuqs, or URL-backed filters, pagination, tabs, and modal state.

Do not load it for unrelated Next.js environment, transport, realtime, or test-runner work. If the task is still deciding whether state belongs in the URL, keep the `state-realtime` slice loaded; this leaf owns the Next.js implementation after that ownership decision.

## Preflight

Inspect the target application before applying the convention:

- detect the router mode, source root, route tree, route groups, and current navigation helpers;
- detect the installed Next.js, TypeScript, and nuqs versions;
- find existing route registries, access matchers, query parser maps, and direct path concatenation;
- identify whether query-dependent data is client-cache-driven or server-rendered; and
- retrieve current official documentation for typed routes, route inputs, request interception, and every nuqs API required by the change.

Preserve a cohesive existing convention during incremental work unless the user requests migration. Do not introduce nuqs merely because this reference documents it; the target stack or explicit request must activate it.

## Ownership

| Concern | Owner |
| --- | --- |
| Route existence and layouts | Next.js route tree |
| Internal pathname construction | Application-owned `appRoutes` |
| Pathname access classification | Application-owned route policies |
| Path/query normalization | Smallest page or layout boundary |
| Shareable query representation | Feature-owned nuqs parser map |
| Business and cross-field validation | Feature/domain schema |
| Server data cache | TanStack Query or selected server boundary |

Keep the route registry and policies inside the deployable Next.js application. A workspace alone does not justify moving them into a package.

## Internal Route Construction

Use one named `appRoutes` API for internal links, redirects, and router operations:

- static routes are literals;
- dynamic routes are named builders;
- inserted path segments are encoded;
- groups follow user-facing areas, not invisible route-group directory names;
- call sites do not concatenate internal pathnames; and
- query strings are produced by the owning query serializer rather than pathname string concatenation.

Use the installed Next.js version's generated route validation when available. Resolve its current config, type-generation, navigation, and route-type syntax from official documentation. A type assertion on a dynamic builder is not sufficient verification; test representative outputs and run framework route type generation or a production build.

## Access Classification

Keep access classification colocated with routing but separate from `appRoutes`. Construction and request matching have different models, particularly for dynamic routes.

Route policies may drive early request-boundary redirects and route-group/layout session checks. They do not replace authoritative ownership, tenant, role, or resource authorization in the server capability boundary. Match whole path segments and test similarly prefixed paths.

## Route Inputs

Read path and search parameters in the smallest framework-owned page/layout boundary. Use the installed version's route-aware input types, parse the URL representation, apply domain or cross-field validation, and pass normalized input into feature components.

nuqs owns query representation and serialization; domain schemas own business validity. Do not duplicate the same primitive conversion across both layers.

## Query State

Use URL state only for shareable, bookmarkable, non-sensitive interaction state. Keep secrets, large payloads, drafts, and disposable presentation state elsewhere.

For activated nuqs usage:

- define one feature-owned parser map with domain-facing names, URL aliases, parsers, defaults, and clearing semantics;
- reuse that map in client hooks, server/page loaders, and link serializers;
- update related filters and pagination as one unit;
- reset pagination when result-changing filters change;
- replace history for filters, search, sorting, and pagination;
- push history only for navigation-like tabs or modals where Back/Forward behavior is useful; and
- include every result-changing parsed value in the server-state query key.

For client-cache-driven lists, keep updates client-local and debounce the free-text value entering the query key. For query-driven RSC output, use the installed nuqs version's supported server-notification behavior and rate-limit free-text updates. Prefer page-boundary loading; use request-local server search-parameter caching only for justified deep Server Component access.

## Review Checklist

- The route tree remains the source of route existence.
- Internal pathnames come from `appRoutes`, including redirects.
- Dynamic builders encode inserted segments and have focused tests.
- Route policies and pathname construction are distinct.
- Early route guarding does not claim authoritative capability authorization.
- Route input parsing stays at the page/layout boundary.
- Query parser definitions are feature-owned and reused across client, server, and serialization.
- URL state is shareable, non-sensitive, and has intentional history behavior.
- Coupled filter and pagination changes are atomic.
- Server notification versus client-local query updates is explicit.
- Feature components remain independent of Next.js route shapes.

## Official Implementation References

- [Next.js documentation](https://nextjs.org/docs)
- [Next.js TypeScript and typed routes](https://nextjs.org/docs/app/api-reference/config/typescript)
- [Next.js route-aware page props](https://nextjs.org/docs/app/api-reference/file-conventions/page)
- [nuqs documentation](https://nuqs.dev/docs)
- [nuqs server-side usage](https://nuqs.dev/docs/server-side)
- [nuqs serializers](https://nuqs.dev/docs/utilities)
- [nuqs options](https://nuqs.dev/docs/options)

Next.js owns route existence, framework navigation, route inputs, and request interception. nuqs is the documented typed query-state specialization. Preserve the ownership rules and opinionated application API while deriving exact vendor symbols and behavior from the target versions.

## Derivation Sources

Derived from the source repository's opinionated Next.js routing, routing/SSR/params, URL-state, and overview documents. These paths are provenance only in an installed skill.
