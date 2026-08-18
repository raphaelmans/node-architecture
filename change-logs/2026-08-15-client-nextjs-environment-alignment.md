# Client Next.js Environment Alignment

Date: 2026-08-15

## Summary

Aligned the client Next.js environment guidance with the current `@t3-oss/env-nextjs` integration contract while keeping the repository's Zod-first validation standard.

## Changes

- Documented TypeScript, ESM, and package-exports compatibility requirements.
- Distinguished strict `runtimeEnv` wiring for older Next.js versions from `experimental__runtimeEnv` client wiring on Next.js 13.4.4 and newer.
- Explained why browser-exposed variables must be statically enumerated.
- Added optional client/server schema splitting when server variable names are sensitive, including explicit runtime wiring for each split module.
- Added build-time validation setup for Next.js 16+ and earlier versions using `jiti`.
- Added the required T3 Env transpilation configuration for standalone output.
- Propagated the implementation and review rules into the `$client` Next.js slice.

## Scope

This change updates client documentation and the client skill only. Server documentation remains outside this change.
