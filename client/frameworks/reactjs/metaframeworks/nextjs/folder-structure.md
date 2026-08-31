# Next.js Folder Structure (App Router)

This document contains Next.js App Router-specific folder and file conventions.

The tree is relative to the selected Next.js application root, which may be `apps/<client>/` in a monorepo. Shared contracts, domain rules, or UI move to packages only when activated by the monorepo package-boundary contract.

## App Router Conventions

- Routes live in `src/app/`.
- Route groups are used for access control and layout partitioning (group names are project-defined).
- API routes live under `src/app/api/**/route.ts`.

## Reference Structure

```text
src/
  app/
    api/
      trpc/[trpc]/route.ts
      public/example/route.ts
    (protected)/
      layout.tsx
      dashboard/page.tsx
    (guest)/
      layout.tsx
      login/page.tsx
    layout.tsx
    page.tsx
  common/
    routing/
      app-routes.ts                 # Internal pathname literals and builders
      route-policies.ts             # Pathname access classification
    clients/                       # HTTP/realtime provider adapters
    logging/                       # AppLogger + debug/Sentry adapters
    analytics/                     # ProductAnalytics + consent/vendor adapters
    runtime/
      browser.ts                   # application-scoped client composition root
      request.ts                   # request-scoped composition when required
  lib/
    modules/<module>/
      shared/
        contracts/                  # Shared client/server Zod wire contracts
  features/<feature>/
    search-params.ts                # Optional feature-owned query parser/serializer map
    api.ts                          # Parses shared response contracts
    hooks.ts                        # TanStack Query adapter
    sync.ts                         # Optional named cache-sync operations
    realtime-api.ts                 # Optional provider-to-domain event boundary
    schemas.ts                      # Client-only form/UI schemas
    components/
```

Notes:

- Group names such as `(protected)`, `(auth)`, `(owner)`, `(admin)`, etc. are implementation choices.
- The architectural rule is ownership and boundary, not fixed group naming.
- `route.ts` and the corresponding client `featureApi` import the same contract from `lib/modules/<module>/shared/contracts/`.
- `common/runtime/browser.ts` owns browser singletons created through factories; feature modules do not construct hidden singletons.
- `common/runtime/request.ts` is used only when SSR dependencies capture request context.
- `common/routing/` remains owned by the deployable Next.js application; workspace topology alone does not make routes a shared package concern.
- `features/<feature>/search-params.ts` exists only when the feature owns shareable query state.
- Runtime consumers receive specific ports or feature API accessors, never the whole runtime container.

For the framework-agnostic feature module structure, see `client/core/folder-structure.md`.
