# 2026-02-14: Server Runtime Restructure + Webhook Core Placement

## Summary

Restructured `server/` docs to mirror the layered shape used in `client/`:

- `server/core/` for agnostic guidance
- `server/runtime/nodejs/` for Node runtime-specific libraries and metaframeworks
- `server/runtime/nodejs/metaframeworks/*` for framework-specific behavior

Additionally, webhook docs were promoted to core because they are treated as agnostic/isomorphic guidance.

## Changes

- Moved tRPC docs:
  - `server/trpc/integration.md` -> `server/runtime/nodejs/libraries/trpc/integration.md`
  - `server/trpc/authentication.md` -> `server/runtime/nodejs/libraries/trpc/authentication.md`
- Moved Supabase docs:
  - `server/supabase/README.md` -> `server/runtime/nodejs/libraries/supabase/README.md`
  - `server/supabase/integration.md` -> `server/runtime/nodejs/libraries/supabase/integration.md`
  - `server/supabase/auth.md` -> `server/runtime/nodejs/libraries/supabase/auth.md`
- Moved Next.js docs:
  - `server/nextjs/README.md` -> `server/runtime/nodejs/metaframeworks/nextjs/README.md`
  - `server/nextjs/route-handlers.md` -> `server/runtime/nodejs/metaframeworks/nextjs/route-handlers.md`
- Moved webhook docs to core:
  - `server/webhook/*.md` -> `server/core/webhook/*.md`
- Added runtime indexes/placeholders:
  - `server/runtime/README.md`
  - `server/runtime/nodejs/README.md`
  - `server/runtime/nodejs/libraries/README.md`
  - `server/runtime/nodejs/metaframeworks/README.md`
  - `server/runtime/nodejs/metaframeworks/express/README.md`
  - `server/runtime/nodejs/metaframeworks/nestjs/README.md`
- Removed now-empty legacy directories:
  - `server/trpc/`, `server/supabase/`, `server/nextjs/`, `server/webhook/`

## Link and Index Alignment

- Updated `server/README.md` documentation map and canonical precedence paths.
- Updated root `README.md` server tree to reflect `runtime/nodejs`.
- Updated cross-links in:
  - `server/core/overview.md`
  - `server/core/api-response.md`
  - `server/core/error-handling.md`
  - `server/core/webhook/*` (path references)
  - `server/drafts/overview.md`
  - `server/drafts/backend-architecture-overview.md`
