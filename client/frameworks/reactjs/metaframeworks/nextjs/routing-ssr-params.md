# Next.js Routing, SSR, and Params

This document captures Next.js App Router conventions that affect client-side architecture.

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

## Auth and Access Control

- Server-side guarding belongs in layouts/route groups.
- Keep a single source of truth for route access.

Implementation guide:

- `skills/client/metaframeworks/nextjs/nextjs-auth-routing/SKILL.md`

