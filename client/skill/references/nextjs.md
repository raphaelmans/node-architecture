# Next.js Slice

For local process setup, Portless, or concurrent worktree origins, coordinate with installed `$development nextjs` when available. Keep browser configuration ownership here. Development tooling supplies the existing app-origin variable before startup; application source and schemas stay unaware of the proxy. Preserve same-origin relative browser calls.

Use this slice for Next.js App Router ownership, SSR/RSC boundaries, route params, access composition, environment variables, tRPC/Ky transport integration, realtime adapters, and Next.js-specific Vitest setup.

## Contents

- [App Router ownership](#app-router-ownership)
- [Convention leaves](#convention-leaves)
- [Routing and request context](#routing-and-request-context)
- [Runtime composition](#runtime-composition)
- [Transport integration](#transport-integration)
- [Environment and tests](#environment-and-tests)
- [Review checklist](#review-checklist)

## App Router Ownership

For scaffolding, load the generic and React contracts first, then detect the installed Next.js/React/Node versions, router mode, config module format, Server/Client boundaries, environment integration, and build setup. Retrieve version-applicable official Next.js documentation for configuration, lifecycle, caching, environment, and production-build behavior before generating those boundaries.

In a workspace, also load `workspace`. Treat all `src/*` paths below as relative to the selected Next.js app, and consume activated internal packages through public exports using current version-matched Next.js/build-system guidance.

- Use the detected router's current route and route-handler file conventions.
- Pages and layouts are metaframework composition boundaries, not feature business layers.
- Route groups partition layouts and access policies; exact group names remain project-specific.
- Parse and validate route params/search params in the smallest page/layout boundary, then pass typed values into feature components.
- Keep a central `appRoutes` API for links and redirects, with a colocated route policy registry for access classification.
- Keep fast request-boundary redirects and header propagation in the framework's current interception boundary, with authoritative session and authorization checks in the appropriate server boundary.

Resolve the installed version's route-param and search-param shapes at the page/layout boundary and keep route parsing out of feature components. Current official documentation owns whether those values are synchronous, asynchronous, or otherwise wrapped.

## Convention Leaves

Read [Next.js Access Control](nextjs/access-control.md) together with [React Access Control](react/access-control.md) for protected SSR/RSC data, access hydration, or organization/branch navigation. It adds request/rendering isolation; it does not replace the React UI contract or the server's capability authorization.

Read [Next.js Routing Convention](nextjs/routing.md) before acting when the task involves `appRoutes`, route policies, internal links or redirects, dynamic path builders, route params, search params, nuqs, or URL-backed filters, pagination, tabs, and modal state.

Do not load that leaf for unrelated environment, transport, realtime-provider, composition-root, or test-runner work. When the request first requires a state-ownership decision, keep `state-realtime` loaded; the routing leaf owns the Next.js implementation after URL state is selected.

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

Place shared client/server capability contracts in the resolved topology boundary: the local module path in one project or an activated contract package when cross-package. Both the framework route adapter or tRPC procedure and the client feature API import the same schema.

## Transport Integration

The canonical chain remains:

```text
components -> query adapter -> featureApi -> clientApi -> network
```

For tRPC:

- Construct the client/link inside the composition root.
- Treat tRPC as transport; preserve `I<Feature>Api` for app-facing capabilities.
- Use the installed tRPC integration's generated utilities for direct query hooks.
- For feature API wrappers that require tRPC cache interop, use the installed integration's supported query-key adapter rather than reconstructing internal keys.
- Keep direct tRPC-generated hooks inside feature hooks as an incremental compatibility mode and project normalized app-facing results.

For Ky/route handlers:

- Construct Ky inside `createClientApi`.
- Use same-origin relative paths in the browser and an absolute base URL for SSR only when required.
- Decode the universal success/error envelope and preserve safe `requestId` metadata.
- Parse the capability payload in `featureApi` and use plain key factories.

For Supabase realtime, construct the client in the composition root, keep channels/status/filter mapping in the adapter, validate rows as unknown, and map them to domain events before React sees them. Database publication, grants, replica identity, and RLS remain reviewed server migrations.

## Environment and Tests

Use one deployable-owned logical environment boundary with distinct typed surfaces: public `BrowserBuildConfig`, build-only private `PrivateBuildConfig`, `ServerRuntimeConfig`, and optional public `BrowserRuntimeConfig`. T3 Env is a supported outer Next.js adapter when detected or selected; it is never an inward architecture dependency.

Detect the installed Next.js, environment-adapter, TypeScript, and module-system versions. Retrieve their current official documentation before choosing runtime maps, public-variable conventions, configuration-module syntax, import strategy, build-time validation wiring, schema split/unification, or standalone-output packaging. These implementation details must not be inferred from this skill, repository examples, or training memory.

Use one physical implementation only when it preserves lifecycle validation and server/browser isolation. Split modules when private/server schemas or runtime-only validation would otherwise become client-reachable or build-required. Validate only genuine build inputs during the build; validate runtime-only server values before dependent server work. Browser runtime resources validate when dependent browser work begins.

Executable schemas are authoritative; `.env.example` is a checked projection of environment-backed fields. Validation permits unrelated ambient variables and exposes only declared normalized values. Outer composition maps these surfaces into focused configuration/ports instead of exporting a global env object.

Extend the core test contract with compatible React/Next.js integration, a Node-default environment, explicit browser-like opt-in for client tests, scoped fake configuration for import-time validation, and any server-only marker shim required by the installed runner/framework combination.

The shim is not an import-safety check. Keep a Next.js build or equivalent boundary validation in CI.

## Review Checklist

- App Router files own route parsing, layouts, SSR/RSC, and access composition only.
- Routing tasks load the routing convention leaf; unrelated Next.js tasks do not.
- Feature code remains independent of route shape and transport providers.
- Browser infrastructure is composed once; request context cannot leak through an SSR singleton.
- Shared contracts are isomorphic and imported by both server and client boundaries.
- tRPC or Ky stays behind the feature/data-flow architecture.
- Query/cache mechanics stay in feature hooks or sync modules.
- Environment exposure and version-specific runtime wiring are explicit and validated at the lifecycle that consumes each value.
- Split environment schemas preserve the client/server import boundary when variable names are sensitive.
- Standalone output includes every required environment-adapter dependency according to the installed framework's packaging contract.
- Next.js tests extend, rather than replace, core behavioral and Vitest rules.

## Official Implementation References

- [Next.js documentation](https://nextjs.org/docs)
- [tRPC client documentation](https://trpc.io/docs/client)
- [T3 Env for Next.js](https://env.t3.gg/docs/nextjs)
- [Vitest guide](https://vitest.dev/guide/)

Next.js owns routing, rendering, request-boundary, configuration, and build conventions; tRPC, T3 Env, and Vitest are documented specializations at their respective outer boundaries. Keep those roles and rationale while deriving their exact integration from the target versions.

## Derivation Sources

Derived from the broad source repository documents under the Next.js metaframework directory, plus the React and core contracts they extend. Opinionated routing details are progressively disclosed through the routing convention leaf. These paths are provenance only in an installed skill.
