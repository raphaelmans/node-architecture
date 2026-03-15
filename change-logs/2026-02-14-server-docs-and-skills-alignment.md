# 2026-02-14: Server Docs + Skills Alignment

## Summary

Aligned `server/` documentation structure with the same approach used for `client/`:

- legacy references are now treated as drafts (non-canonical)
- server skill references are centralized under top-level skill names

## Changes

- Renamed `server/references/` to `server/drafts/`.
- Added `server/drafts/overview.md` with:
  - explicit non-canonical/outdated warning
  - canonical precedence links (`server/core/*`, `server/trpc/*`, `server/webhook/*`, `server/supabase/*`)
  - draft index table
- Added a draft warning banner to `server/drafts/backend-architecture-overview.md`.
- Moved server skills:
  - from `server/skills/*`
  - to top-level server skill names (`backend-module`, `backend-feature`)
- Updated `server/README.md`:
  - skill references now use top-level skill names instead of path links
  - final section changed from `References` to `Drafts` with non-canonical warning + link to `./drafts/overview.md`
- Updated root `README.md`:
  - documentation tree now shows `server/drafts/`
  - server quick-start now references top-level skill names
  - “For Humans” now points to `drafts/` as legacy/non-canonical detail docs
