# Next.js Folder Structure (App Router)

This document contains Next.js App Router-specific folder and file conventions.

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
```

Notes:

- Group names such as `(protected)`, `(auth)`, `(owner)`, `(admin)`, etc. are implementation choices.
- The architectural rule is ownership and boundary, not fixed group naming.

For the framework-agnostic feature module structure, see `client/core/folder-structure.md`.
