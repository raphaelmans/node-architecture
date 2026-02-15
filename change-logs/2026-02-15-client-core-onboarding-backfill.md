# 2026-02-15: Client Core + React/Next Alignment Backfill

## Summary

Expanded `client/core/*` and then aligned React/Next framework docs with those core contracts.
This remains client-boundary only; server docs are unchanged.

## Added

- `client/core/onboarding.md`
  - New startup guide for new projects and contributors.
  - Includes read order, bootstrap checklist, first-feature definition of done, and PR checklist.
- `client/frameworks/reactjs/server-state-patterns-react.md`
  - New comprehensive cookbook for mixed invalidation ownership patterns.
  - Covers hook-owned, component-coordinator, and hybrid patterns with scenario guidance.

## Updated

- `client/core/overview.md`
  - Added explicit start path and reading order.
  - Added common mistakes and updated core index.
- `client/core/conventions.md`
  - Added execution decision flows (logic placement + promotion rules).
  - Added naming/import/colocation conventions and PR review checklist.
- `client/core/server-state-tanstack-query.md`
  - Expanded from high-level notes to a practical playbook:
    - query lifecycle (basic/dependent/parallel/composed)
    - mutation lifecycle (invalidation batching, optimistic guardrails, navigation ordering)
    - cache ownership and anti-patterns
- `client/core/folder-structure.md`
  - Added feature starter contract (required/recommended/optional files).
  - Added ownership boundaries and cross-feature promotion rules.
- `client/README.md`
  - Added core onboarding link in Core Documentation table.
  - Added onboarding doc as the default quick start entrypoint.
- `README.md` (root)
  - Updated client stack wording to adapter-based API layer.
  - Added `client/core/onboarding.md` to the top-level documentation tree.
  - Replaced stale project structure sample with a contract-oriented structure aligned to current client-core conventions.
  - Updated client quick-start flow to core-first (`onboarding -> conventions -> client-api architecture -> framework docs`).
- `client/frameworks/README.md`
  - Added explicit core-first entrypoint before framework docs.
- `client/frameworks/reactjs/README.md`
  - Added required core read order before React-specific guidance.
- `client/frameworks/reactjs/metaframeworks/nextjs/README.md`
  - Added explicit read order (`core -> reactjs -> nextjs`) to reduce metaframework-first onboarding drift.
- `client/frameworks/reactjs/composition-react.md`
  - Aligned wording with canonical hook naming (`useQuery*` / `useMut*` / `useMod*`) and reduced direct library-hook phrasing in anti-patterns.
- `client/frameworks/reactjs/metaframeworks/nextjs/overview.md`
  - Updated forms/error bullets to align with current `AppError` normalization and validation-to-form mapping conventions.
  - Added mixed invalidation ownership guidance and cookbook cross-link.
- `client/frameworks/reactjs/conventions.md`
  - Added explicit mixed invalidation ownership guidance and link to React cookbook.
- `client/frameworks/reactjs/forms-react-hook-form.md`
  - Expanded mutation section into three variants (hook-owned, component-coordinator, hybrid).
  - Added scenario cookbook and checklist items for invalidation strategy + `Promise.all` batching.
- `client/frameworks/reactjs/ui-shadcn-radix.md`
  - Updated business component examples to show both valid ownership patterns.
- `client/frameworks/reactjs/error-handling.md`
  - Clarified `useCatchErrorToast` success+error semantics and optional success toast behavior.
- `client/frameworks/reactjs/metaframeworks/nextjs/trpc.md`
  - Added both hook-owned and component-coordinator invalidation variants for tRPC with decision criteria.
- `client/frameworks/reactjs/metaframeworks/nextjs/ky-fetch.md`
  - Added mixed invalidation ownership variants for non-tRPC HTTP adapter flows.
- `client/frameworks/reactjs/metaframeworks/nextjs/README.md`
  - Added React server-state cookbook link for Next.js readers.
- `client/frameworks/reactjs/README.md`
  - Added direct link to the new React server-state cookbook in the Start Here section.
- `client/frameworks/reactjs/overview.md`
  - Added explicit server-state ownership concern and cookbook pointer.

## Notes

- No runtime code or API behavior changed.
- This update is documentation-contract only.
