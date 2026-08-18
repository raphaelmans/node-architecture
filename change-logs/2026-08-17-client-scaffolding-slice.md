# Client Scaffolding Slice

Date: 2026-08-17

## Summary

Added repository-aware scaffolding to the existing `$client` router. The action bootstraps missing foundations or creates one real vertical feature slice in listed or unlisted client frameworks without introducing a separate skill or generator-owned source of truth.

## Commands

```text
$client scaffold foundation
$client scaffold <feature>/<operation>
$client scaffold <feature>/<operation> using canonical layout
```

## Behavior

- Defaults to adapting the repository's existing layout; canonical placement requires explicit user intent.
- Treats canonical layout as stack-relative boundary-to-path mapping rather than one universal TypeScript tree.
- Applies the generic foundation contract to unlisted frameworks and derives stack integration from repository evidence plus current primary documentation.
- Requires version-applicable primary-source retrieval for dependency, config, lifecycle, module-format, build, and deployment decisions; missing or contradictory evidence blocks affected writes.
- Completes framework, layout, contract, abstraction, dependency, package-manager, and verification preflight before writing.
- Shows the smallest exact, version-pinned dependency command set and requires approval before installation.
- Keeps package and native-primitive defaults in stack specializations while preserving compatible existing adapters first.
- Reuses structural equivalents, creates only missing files, and never overwrites or emits generator metadata.
- Requires a real feature contract and aborts before writing when a required capability is declined.
- Follows client-core orchestration: query adapters, optional `useMod*`/`sync.ts`, feature APIs, and business coordinators without a default controller layer.
- Verifies generated boundaries with targeted tests, typecheck, lint, and relevant builds.

## Artifacts

- Added `client/core/scaffolding.md` as the framework-agnostic canonical contract.
- Added React and Next.js scaffolding specializations under `client/frameworks/reactjs/`.
- Added `client/skill/references/scaffolding.md` as the portable execution slice.
- Updated `$client` routing, metadata, client navigation, onboarding, and the standalone Skills page.
- Added the ninth slice to repository-only source-drift tracking.

## Scope

React and Next.js are documented specializations, not an allowlist. For any other client framework, the router applies core boundaries and derives framework integration from repository evidence and current official resources. Server scaffolding and arbitrary application initialization remain outside this change.

## Primary Sources Verified

- [Next.js `next.config.js` documentation](https://nextjs.org/docs/app/api-reference/config/next-config-js) — CommonJS `next.config.js`, ESM `next.config.mjs`, and async configuration behavior.
- [Jiti programmatic usage](https://github.com/unjs/jiti#programmatic) — CommonJS initialization and preferred asynchronous import API.
