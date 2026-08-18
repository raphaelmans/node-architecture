# Next.js Slice

Use this slice for Next.js App Router ownership, SSR/RSC boundaries, route params, access composition, environment variables, tRPC/Ky transport integration, realtime adapters, and Next.js-specific Vitest setup.

## Contents

- [App Router ownership](#app-router-ownership)
- [Routing and request context](#routing-and-request-context)
- [Runtime composition](#runtime-composition)
- [Transport integration](#transport-integration)
- [Environment and tests](#environment-and-tests)
- [Review checklist](#review-checklist)

## App Router Ownership

For scaffolding, load the generic and React contracts first, then detect the installed Next.js/React/Node versions, router mode, config module format, Server/Client boundaries, environment integration, and build setup. Retrieve version-applicable official Next.js documentation for configuration, lifecycle, caching, environment, and production-build behavior before generating those boundaries.

- Routes live in `src/app/`; API route handlers live under `src/app/api/**/route.ts`.
- Pages and layouts are metaframework composition boundaries, not feature business layers.
- Route groups partition layouts and access policies; exact group names remain project-specific.
- Parse and validate route params/search params in the smallest page/layout boundary, then pass typed values into feature components.
- Keep a central route registry for links, redirects, and access classification.
- Keep fast boundary redirects/header propagation in `proxy.ts`, with authoritative session/authorization checks in the appropriate server boundary.

For current App Router request APIs, page/layout params and page search params may be promises. Await them in Server Components and keep route parsing out of feature components.

## Routing and Request Context

SSR/RSC composes features; it does not bypass client boundaries. Server prefetch may use query options and hydration, but client components still consume feature/query APIs rather than transport primitives.

Keep pathname, request ID, cookies, headers, and actor context at metaframework or transport boundaries. Do not add them to feature inputs unless the public business contract independently requires them.

## Runtime Composition

```text
common/runtime/browser.ts
  -> application-scoped logger, analytics, transport, feature APIs

common/runtime/request.ts
  -> request-scoped dependencies only when they capture request context
```

Provider and feature runtime modules expose specific ports/accessors. They never construct hidden singletons or return the complete runtime container.

Place shared client/server capability contracts under `src/lib/modules/<module>/shared/contracts/`. Both `route.ts` or tRPC procedures and the client feature API import the same schema.

## Transport Integration

The canonical chain remains:

```text
components -> query adapter -> featureApi -> clientApi -> network
```

For tRPC:

- Construct the client/link inside the composition root.
- Treat tRPC as transport; preserve `I<Feature>Api` for app-facing capabilities.
- Use generated utilities for direct tRPC query hooks.
- Use `buildTrpcQueryKey` only for feature API wrappers that require tRPC cache interop.
- Keep direct `trpc.*` hooks inside feature hooks as an incremental compatibility mode and project normalized app-facing results.

For Ky/route handlers:

- Construct Ky inside `createClientApi`.
- Use same-origin relative paths in the browser and an absolute base URL for SSR only when required.
- Decode the universal success/error envelope and preserve safe `requestId` metadata.
- Parse the capability payload in `featureApi` and use plain key factories.

For Supabase realtime, construct the client in the composition root, keep channels/status/filter mapping in the adapter, validate rows as unknown, and map them to domain events before React sees them. Database publication, grants, replica identity, and RLS remain reviewed server migrations.

## Environment and Tests

Use `@t3-oss/env-nextjs` as the validated environment boundary. Client-exposed variables require `NEXT_PUBLIC_`; secrets never do. Application code reads the validated module rather than scattered `process.env` calls. Parse string booleans explicitly so `"false"` does not become truthy.

Keep runtime wiring compatible with the installed Next.js version:

- Next.js `>= 13.4.4`: use `experimental__runtimeEnv` and explicitly enumerate every client variable.
- Next.js `< 13.4.4`: use strict `runtimeEnv` and explicitly enumerate every server and client variable.

Next.js statically analyzes environment-variable access for browser bundling, so do not replace explicit entries with dynamic property access. Import the env module from Next.js config to guarantee build-time validation: use a direct TypeScript import on Next.js 16+ and `jiti` on earlier versions. Preserve the detected config module format: CommonJS `next.config.js` on Next.js 12.1+ uses `require`, an async `module.exports`, and Jiti's async import API; ESM syntax belongs in `next.config.mjs`. For an older Next.js version without async config support, resolve a version-compatible strategy or block. Verify all behavior against the installed Next.js and Jiti versions before editing.

Use a unified schema by default. Split client and server schemas when server variable names are sensitive, and prevent client-reachable modules from importing the server schema. In a split setup, give `client.ts` strict `runtimeEnv` entries for its public variables; on Next.js `>= 13.4.4`, give the server-only module `experimental__runtimeEnv: process.env`, never an empty object. Older versions require explicit strict server entries.

For `output: "standalone"`, add `@t3-oss/env-nextjs` and `@t3-oss/env-core` to `transpilePackages`. Confirm TypeScript 5+, ESM, and package-exports-compatible module resolution before adopting the package.

Extend core Vitest with:

- React plugin and Testing Library;
- Node as the default environment;
- jsdom per client test or separate projects;
- a `server-only` shim for runner compatibility;
- scoped fake environment setup for import-time validation.

The shim is not an import-safety check. Keep a Next.js build or equivalent boundary validation in CI.

## Review Checklist

- App Router files own route parsing, layouts, SSR/RSC, and access composition only.
- Feature code remains independent of route shape and transport providers.
- Browser infrastructure is composed once; request context cannot leak through an SSR singleton.
- Shared contracts are isomorphic and imported by both server and client boundaries.
- tRPC or Ky stays behind the feature/data-flow architecture.
- Query/cache mechanics stay in feature hooks or sync modules.
- Environment exposure and version-specific runtime wiring are explicit and validated during the build.
- Split environment schemas preserve the client/server import boundary when variable names are sensitive.
- Standalone output transpiles both T3 Env packages.
- Next.js tests extend, rather than replace, core behavioral and Vitest rules.

## Derivation Sources

Derived from all source repository documents under the Next.js metaframework directory, plus the React and core contracts they extend. These paths are provenance only in an installed skill.
