# Next.js Routing, SSR, and Params

This document captures Next.js App Router conventions that affect client-side architecture.

Examples target Next.js 16 request APIs, where route params and page search params are asynchronous.

## Core Rules

- Treat SSR/RSC as part of the client boundary: pages/layouts are metaframework concerns that **compose** feature components.
- Feature components should not depend on route shape directly (keep route parsing in page/layout).
- Read params/searchParams in the smallest metaframework-owned layer possible (page/layout) and pass typed values into the feature.

## Params and Search Params

- `params`: path segments (e.g. `/users/[id]`)
- `searchParams`: URL query (e.g. `?tab=settings`)

Conventions:

- Normalize/validate at the boundary (Zod recommended).
- Keep “URL state” implementation in Next.js + `nuqs` docs.
- In current App Router releases, page/layout `params` and page `searchParams` are promises. Await them in Server Components or read them with React `use(...)` in a Client Component.

```typescript
export default async function UserPage(
  props: PageProps<"/users/[id]">,
) {
  const { id } = await props.params;
  const searchParams = await props.searchParams;
  const input = UserRouteInputSchema.parse({ id, tab: searchParams.tab });

  return <UserView input={input} />;
}
```

Prefer generated `PageProps<"/literal/route">` when available. Route parsing stays here; the resulting typed input is passed into the feature component.

## Auth and Access Control

- Server-side guarding belongs in layouts/route groups.
- Keep a single source of truth for route access.

Implementation guide:

- Keep route access rules in your route registry and `proxy.ts`.
- Keep layout/route-group guards server-side.
- Use `proxy.ts` for fast request-boundary checks, redirects, and header/cookie propagation—not as the sole authorization or session-management layer.
