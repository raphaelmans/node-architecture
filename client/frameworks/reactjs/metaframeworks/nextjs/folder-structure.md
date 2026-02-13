# Next.js Folder Structure (App Router)

This document contains Next.js App Router-specific folder and file conventions.

## App Router Conventions

- Routes live in `src/app/`.
- Route groups like `(authenticated)` and `(guest)` are used for access control and layout partitioning.
- API routes live under `src/app/(api)/.../route.ts`.

## Reference Structure

```text
src/
  app/
    (api)/
      api/
        trpc/[...trpc]/route.ts
    (authenticated)/
      layout.tsx
      dashboard/page.tsx
    (guest)/
      layout.tsx
      login/page.tsx
    layout.tsx
    page.tsx
```

For the framework-agnostic feature module structure, see `client/core/folder-structure.md`.

