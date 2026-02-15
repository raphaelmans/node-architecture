# 2026-02-14: Server Docs + Skills Alignment

## Summary

Aligned `server/` documentation structure with the same approach used for `client/`:

- legacy references are now treated as drafts (non-canonical)
- server skills are centralized under top-level `skills/server/`

## Changes

- Renamed `server/references/` to `server/drafts/`.
- Added `server/drafts/overview.md` with:
  - explicit non-canonical/outdated warning
  - canonical precedence links (`server/core/*`, `server/trpc/*`, `server/webhook/*`, `server/supabase/*`)
  - draft index table
- Added a draft warning banner to `server/drafts/backend-architecture-overview.md`.
- Moved server skills:
  - from `server/skills/*`
  - to `skills/server/*`
- Updated `server/README.md`:
  - skills links now point to `../skills/server/*`
  - final section changed from `References` to `Drafts` with non-canonical warning + link to `./drafts/overview.md`
- Updated root `README.md`:
  - documentation tree now shows `server/drafts/` and top-level `skills/server/`
  - server quick-start skills link now points to `./skills/server/`
  - “For Humans” now points to `drafts/` as legacy/non-canonical detail docs

