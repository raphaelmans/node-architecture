# 2026-02-15: Server Docs Gap Backfill from `next16bp`

## Summary

Backfilled missing server-side architecture documentation by using `next16bp` as a reference source while keeping this repository as canonical.

Scope was server-only.

## Core Additions

- Added `server/core/rate-limiting.md` for agnostic rate-limiting contracts.
- Added `server/core/async-jobs-outbox.md` for transactional enqueue + retry/idempotency patterns.
- Updated core indexes/conventions:
  - `server/core/overview.md`
  - `server/core/conventions.md`
  - `server/README.md`
- Removed async outbox from deferred non-goals where it is now canonically documented.

## Runtime + Metaframework Additions

- Added `server/runtime/nodejs/libraries/trpc/rate-limiting.md`.
- Added Next.js metaframework operational docs:
  - `server/runtime/nodejs/metaframeworks/nextjs/formdata-transport.md`
  - `server/runtime/nodejs/metaframeworks/nextjs/caching-revalidation.md`
  - `server/runtime/nodejs/metaframeworks/nextjs/metadata-seo.md`
  - `server/runtime/nodejs/metaframeworks/nextjs/next-config-security.md`
  - `server/runtime/nodejs/metaframeworks/nextjs/cron-routes.md`
- Updated indexes:
  - `server/runtime/nodejs/README.md`
  - `server/runtime/nodejs/libraries/README.md`
  - `server/runtime/nodejs/metaframeworks/nextjs/README.md`

## Integration Cross-Links Updated

- `server/runtime/nodejs/libraries/trpc/integration.md` now links to runtime rate-limiting and Next.js FormData transport guidance.
- `server/runtime/nodejs/libraries/supabase/integration.md` now points FormData transport concerns to Next.js metaframework docs.

## Placement Decision Captured

- `zod-form-data` and `FormData` transport conventions are not in core.
- Canonical home is `server/runtime/nodejs/metaframeworks/nextjs/formdata-transport.md`.

