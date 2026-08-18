# Foundations Slice

Use this slice for architecture boundaries, feature placement, composition roots, dependency lifetimes, and cross-runtime domain placement.

## Contents

- [Decision order](#decision-order)
- [Layer ownership](#layer-ownership)
- [Feature structure](#feature-structure)
- [Factories and lifetimes](#factories-and-lifetimes)
- [Domain placement](#domain-placement)
- [Review checklist](#review-checklist)

## Decision Order

For scaffolding, treat the roles below as portable contracts rather than universal filenames. Preserve compatible placement in the target repository. A documented framework specialization may supply a canonical mapping; for an unlisted framework, derive and approve that mapping from repository evidence and current official guidance before writing.

Place behavior by asking, in order:

1. Is it transport-specific? Put it behind `clientApi` or the metaframework transport adapter.
2. Is it endpoint-scoped parsing or mapping? Put it in the feature API.
3. Is it a serialized client/server contract? Put it in the owning module's `shared/contracts` directory.
4. Is it query, mutation, or cache behavior? Put it in the query adapter.
5. Is it a pure cross-runtime rule? Put it in the owning module's `shared` domain module.
6. Is it client-only view-model logic? Keep it in the feature's `domain.ts` or `helpers.ts`.
7. Is it UI workflow orchestration? Keep it in the business component or a justified composed hook.
8. Is it render-only? Keep it in a presentation component.

Promote feature code to `common` only when multiple features use it, no one feature owns it, and a stable contract exists.

## Layer Ownership

```text
route/page
  -> business component
    -> query adapter
      -> feature API
        -> client API
          -> network
```

- Routes own params, layouts, SSR/RSC boundaries, and access composition.
- Business components own form setup, loading/error wiring, navigation, and route-local sequencing through named query/cache operations.
- Query adapters own server-state lifecycle and cache mechanics.
- Feature APIs own endpoint paths, capability response parsing, mapping, and normalized errors.
- Client APIs own transport, universal envelope decoding, auth/header attachment, and request outcomes.
- Presentation components receive props or form context and render.
- Providers coordinate app-wide ports; they do not fetch and redistribute server entities.

Do not add a client controller merely to add another hop. Add a workflow abstraction only when a real multi-step UX flow benefits from an independently testable coordinator.

## Feature Structure

The following TypeScript/React-shaped paths are the documented React specialization. Other frameworks map the same ownership roles to their native view, state, composition, and test conventions instead of copying these filenames.

Keep cross-feature infrastructure under `src/common/`:

```text
src/common/
  errors/
  query-keys/
  logging/
  analytics/
  runtime/
    browser.ts
    request.ts
  clients/
```

Do not create a parallel top-level `src/runtime/` or `src/lib/common/` infrastructure tree when this architecture is being applied.

```text
src/features/<feature>/
  components/
    <feature>-view.tsx
    <feature>-fields.tsx
  api.ts
  api.runtime.ts
  hooks.ts
  schemas.ts
  types.ts
  helpers.ts
```

Add only when justified:

- `domain.ts` for feature-local pure rules;
- `sync.ts` for multi-query cache coordination;
- `realtime-api.ts` and `realtime-api.runtime.ts` for subscriptions;
- `query-options.ts` for prefetch/RSC query options;
- `stores/` for feature-owned coordination state;
- `machines/` for explicit complex interaction state;
- a `hooks/` directory when the root hook file is no longer cohesive.

`api.runtime.ts` exposes a composition-root-owned accessor and stable mock target. It must not construct a hidden singleton.

## Factories and Lifetimes

Use factories for dependency-heavy or swappable infrastructure:

```ts
createAppLogger(config);
createProductAnalytics(config);
createClientApi({ transport, logger });
createProfileApi({ clientApi, toAppError, logger });
```

The composition root owns construction order and lifecycle. Inject specific dependencies:

```ts
createProfileApi({ clientApi, toAppError, logger });
```

Do not inject `{ runtime }` or expose `useRuntime()` as a service locator.

Lifetime defaults:

- Browser infrastructure: one application-scoped instance.
- Stateless SSR infrastructure: application-scoped when it captures no request or actor data.
- Request-contextual SSR infrastructure: one instance per request.
- Tests: one graph per test using the same factories with fakes, spies, or no-op adapters.

Never create factories for React components, Zod schemas, pure helpers, simple hooks, or immutable values.

## Domain Placement

Use this precedence:

1. Wire input/response: `src/lib/modules/<module>/shared/contracts/`.
2. Cross-runtime pure rule or transform: `src/lib/modules/<module>/shared/`.
3. Client-only feature rule or view model: `src/features/<feature>/domain.ts` or `helpers.ts`.

Shared code must remain isomorphic and side-effect free. It must not import database clients, server auth, environment access, browser globals, React, stores, or query hooks.

## Review Checklist

- Every layer owns only its documented responsibility.
- Components do not call HTTP, tRPC, or QueryClient directly.
- Feature APIs implement `I<Feature>Api` and are created through `create<Feature>Api`.
- The composition root is the only owner of infrastructure lifecycle.
- No consumer receives the entire runtime container.
- Browser and SSR lifetimes cannot leak actor/request context.
- Shared domain code is safe in both client and server runtimes.
- Existing legacy code is reported, not broadly rewritten outside scope.

## Derivation Sources

This installed reference is derived from the source repository's client README, core README, onboarding, architecture, conventions, composition-root, folder-structure, domain-logic, and diagrams documents. These paths are provenance; do not attempt to load them from an installed skill.
