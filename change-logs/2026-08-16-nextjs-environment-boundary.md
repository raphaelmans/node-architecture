# 2026-08-16: Next.js Environment Boundary

## Summary

Added a canonical Next.js environment-configuration pattern based on T3 Env and aligned it with the server architecture's runtime and dependency-injection boundaries.

## Canonical Guidance

- Added `server/runtime/nodejs/metaframeworks/nextjs/environment-variables.md`.
- Defined `process.env` as untyped runtime input that is validated once at an app-owned Next.js boundary.
- Recommended `@t3-oss/env-nextjs` without making it a core or cross-framework dependency.
- Separated server-only and `NEXT_PUBLIC_` variables and documented the optional server/client schema split.
- Added current runtime-map, build validation, standalone output, deployment, and import-time test guidance.
- Required composition roots and infrastructure factories to inject narrow configuration instead of passing the env object into inner layers.

## Cohesion Updates

- Linked the guide from the Next.js and server indexes and from Next.js security gating.
- Updated Supabase deployment-variable guidance and Next.js proxy examples to use the validated env module.
- Removed environment-dependent debug branching from the tRPC logging example; the logger adapter's configured level owns record suppression.
- Updated the `$server` router and runtimes slice so environment/configuration tasks load the runtime guidance.
- Added the environment boundary and a compact T3 Env example to the standalone server architecture HTML.
- Added the new canonical source to runtimes drift tracking.

## Validation

- Passed Markdown and standalone-HTML link checks with no missing local targets or duplicate HTML IDs.
- Passed server skill source drift and complete canonical coverage checks: eight slices and 50 guides.
- Passed the official skill quick validator in an isolated PyYAML environment.
- Verified the HTML Runtime panel, environment-guide link, copy fallback, and contained responsive layout at 1440px and 390px widths.
