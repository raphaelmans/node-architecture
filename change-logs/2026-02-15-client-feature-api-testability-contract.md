# 2026-02-15: Client Feature API Testability Contract

## Summary

Standardized the client docs around a strict feature API contract:

- `I<Feature>Api` interface
- `class <Feature>Api implements I<Feature>Api`
- `create<Feature>Api` factory with injected dependencies

Also formalized test boundaries for `api.ts`, `hooks.ts`, and pure domain/helper functions.

## Updated

- `client/core/client-api-architecture.md`
  - Added required class-based feature API contract and factory pattern.
  - Added boundary-based testing contract (`api.ts`, `hooks.ts`, `domain.ts`, `helpers.ts`).
- `client/core/conventions.md`
  - Added required `I<Feature>Api` + class + factory convention.
  - Added PR checklist items for feature API and testing boundaries.
- `client/core/folder-structure.md`
  - Updated feature module structure to include class-based API contract.
  - Added recommended test layout (`api.test.ts`, `hooks.test.ts`, `domain.test.ts`, `helpers.test.ts`).
- `client/core/domain-logic.md`
  - Added function-based rule for `domain.ts` / `helpers.ts`.
  - Added pure-function testing strategy and shared-module testing notes.
- `client/core/onboarding.md`
  - Added bootstrap and DoD checks for feature API contract and test coverage.
- `client/core/overview.md`
  - Added key decision note for class-based feature APIs.
- `client/core/architecture.md`
  - Added principle for testable feature API boundaries.
- `client/core/server-state-tanstack-query.md`
  - Added contract that query adapters depend on `I<Feature>Api`.
  - Added testing split guidance for API class vs query hooks.
- `client/core/error-handling.md`
  - Added `toAppError` injection rule for feature API classes.
- `client/frameworks/reactjs/conventions.md`
  - Added React hook dependency rule on `I<Feature>Api`.
  - Added React testing conventions by layer.
- `client/frameworks/reactjs/server-state-patterns-react.md`
  - Added testing cookbook for query hooks, feature APIs, and domain/helpers.
- `client/frameworks/reactjs/composition-react.md`
  - Expanded testing section with interface-based hook tests and API class tests.
- `client/frameworks/reactjs/metaframeworks/nextjs/overview.md`
  - Added Next.js usage guidance for class-based feature APIs.
- `client/frameworks/reactjs/metaframeworks/nextjs/trpc.md`
  - Clarified recommended `I<Feature>Api` boundary with tRPC compatibility mode.
- `client/frameworks/reactjs/metaframeworks/nextjs/ky-fetch.md`
  - Added recommended feature API wrapper contract over raw ky transport helpers.

## Notes

- Documentation-only update.
- No runtime code behavior changed.
