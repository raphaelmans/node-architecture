# 2026-02-13: Client Docs Restructure

## Summary

Restructured `client/` documentation into:

- `client/core/` for framework-agnostic guidelines and architecture
- `client/frameworks/reactjs/` for React-specific docs (RHF, StandardForm, shadcn/Radix, Zustand)
- `client/frameworks/reactjs/metaframeworks/nextjs/` for Next.js-specific docs (routing/SSR/params, nuqs, env, adapters)

## Notable Changes

- Renamed `client/references/` to `client/drafts/` and fixed `client/drafts/client-side-architecture.md` links.
- Moved client skills out of `client/` into `skills/client/` (including the Next.js auth/routing skill).
- Updated `client/README.md` and root `README.md` to reflect the new structure.

## Follow-Up Convention Updates (Same Change Window)

- Added ASCII visualization: `client/diagrams.md` (structure, data flow, state decisioning) and linked it from `client/README.md`.
- Hook naming in docs:
  - Queries: `useQuery<Feature><Noun><Qualifier?>`
  - Mutations: `useMut<Feature><Verb><Object?>`
  - Composed hooks: `useMod<Descriptive>`
  - Updated examples in `client/frameworks/reactjs/*` and `client/frameworks/reactjs/metaframeworks/nextjs/*` accordingly.
- Feature schema file naming: canonical docs now refer to `schemas.ts` (instead of `dtos.ts`) for Zod schemas + derived types + mapping helpers.
- React form typing: canonical RHF docs now use `<Feature>FormShape` (derived from `<feature>FormSchema` / `<feature>FormSchema`) instead of `*FormHandler`.
- Default form UX convention: submit button disabled only while submitting (`isSubmitting`), with `mode: "onSubmit"` as the default validation mode.
  - Edit-form exception documented: disable when `!isDirty` (optional).
- Removed extra “form ready” state in docs (`isFormReady`); readiness is derived from `!!record` / query success, and `useEffect` + `reset` handles updates.
- Centralized invalidations in docs: extracted `onSubmitInvalidateQueries()` and wrapped invalidations in `Promise.all([...])` for multi-query invalidation.
- Query key conventions standardized:
  - Canonical query key guidance lives in `client/core/query-keys.md`.
  - Keys are stored in `src/common/query-keys/<feature>.ts` (to support cross-feature invalidation).
  - `client/frameworks/reactjs/metaframeworks/nextjs/query-keys.md` now redirects to the canonical core doc.
- Decoupled React docs from tRPC:
  - Removed `trpc.*` usage from `client/frameworks/reactjs/*.md` examples.
  - tRPC remains only under `client/frameworks/reactjs/metaframeworks/nextjs/`.
- Domain logic placement guidance:
  - Added `client/core/domain-logic.md` to define precedence and boundaries for shared vs client-only transforms.
  - Convention: reusable domain logic can live under `src/lib/modules/<module>/shared/*`; UI-only shaping stays in `src/features/<feature>/*`.
- Client logging standard:
  - Added `client/core/logging.md` for client logging conventions using `debug`.
  - Convention: primary logs live at boundaries (`clientApi` and `featureApi`), not in presentation components.
  - Added a documented break-glass override (`localStorage["app:log:provider"]`) gated by `NEXT_PUBLIC_ALLOW_BREAK_GLASS_LOGGING`.
- Client error handling (React):
  - Expanded `client/core/error-handling.md` with an `AppError` contract and `toAppError(err: unknown)` adapter rule.
  - Added `client/frameworks/reactjs/error-handling.md` documenting the React facade and `useCatchErrorToast` pattern (toast-library-agnostic).
