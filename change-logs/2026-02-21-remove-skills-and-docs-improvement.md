# 2026-02-21: Remove Skills + Docs Improvement

## Summary

Removed the `skills/` directory entirely. Skills are no longer part of this architecture repository. Also includes documentation improvements from recent commit.

## Removed

- `skills/` directory and all contents (server skills, client skills).
- `change-logs/2026-02-14-server-docs-and-skills-alignment.md` (now obsolete).

## Updated (from `830db9d` — docs: improvement)

- Added `AGENTS-MD-ALIGNMENT.md` — alignment guide for agents and markdown docs.
- Added `GUIDES-README.md` — guides readme.
- Added `UPDATE-ARCHITECTURE.md` — architecture update guide.
- Updated `client/README.md` — minor link fix.
- Updated `client/core/` docs:
  - `client-api-architecture.md`, `conventions.md`, `domain-logic.md` — small additions.
  - `folder-structure.md` — expanded structure docs.
  - `overview.md` — additions.
  - `testing.md` — new comprehensive client testing guide.
- Updated `copy-guides.sh` — expanded copy script.
- Added `server/core/testing-service-layer.md` — server service layer testing guide.

## Notes

- Skills are fully removed — any references to `skills/` in other docs should be cleaned up separately.
- Documentation-only changes. No runtime code changes.
