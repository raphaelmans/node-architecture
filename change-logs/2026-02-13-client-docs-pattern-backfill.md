# 2026-02-13: Client Docs Pattern Backfill (Canonical Base Preserved)

## Summary

Integrated missing conventions/patterns into canonical `client/*` docs without changing the docs structure.
The current `client/*` remains the source of truth; old-repo patterns were added only as additive guidance.

## Updated Areas

- `client/core/overview.md`
  - Explicitly states canonical-base rule.
  - Added `Known Drift` section (naming, direct toast imports, mixed-responsibility hooks).
- `client/core/query-keys.md`
  - Added tRPC exception note (use generated keys/utilities for tRPC procedures).
- `client/core/error-handling.md`
  - Added transport metadata pass-through guidance (`message`, `code`, `status`, `requestId`).
- `client/core/logging.md`
  - Added correlation context convention (`requestId` and optional boundary metadata).
- `client/core/conventions.md`
  - Added non-blocking best-effort side-effects rule.
  - Added transport guard boundary note (CSRF/origin/rate-limit/correlation metadata).
- `client/core/state-management.md`
  - Added explicit anti-duplication rule for server state in client stores.

## Framework/Metaframework Alignment

- `client/frameworks/reactjs/conventions.md`
  - Added migration status section for hook naming/SRP drift.
- `client/frameworks/reactjs/forms-react-hook-form.md`
  - Replaced stale alias-specific schema import examples with path-agnostic placeholders.
- `client/frameworks/reactjs/metaframeworks/nextjs/overview.md`
  - Removed stale hardcoded location assumptions.
  - Added request metadata flow section (`x-pathname`, `x-request-id`) as boundary concern.
- `client/frameworks/reactjs/metaframeworks/nextjs/folder-structure.md`
  - Replaced stale `(api)/api` and `[...trpc]` examples with generic App Router API route conventions.
- `client/frameworks/reactjs/metaframeworks/nextjs/ky-fetch.md`
  - Added error normalization handoff section (`ApiClientError -> toAppError -> AppError`).
- `client/frameworks/reactjs/metaframeworks/nextjs/trpc.md`
  - Rewritten to architecture-first guidance.
  - Added explicit `Compatibility Appendix` for legacy tRPC-first patterns.

## Supporting Updates

- `client/diagrams.md`
  - Added request/error correlation diagram showing boundary-owned metadata and normalization flow.
- `client/README.md`
  - Updated API layer stack row to adapter-choice wording.
  - Updated new-feature route checklist to project-defined App Router groups.
