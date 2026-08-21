# React Scaffolding

This guide implements the [client scaffolding contract](../../core/scaffolding.md) for an existing React repository. It is a known specialization, not a requirement for other client frameworks.

When React is inside a workspace, apply this mapping within the resolved client application/package. Package creation, exports, workspace dependency edges, and cross-package contracts/domain/UI extraction are coordinated by [monorepo scaffolding](../../../monorepo/core/scaffolding.md) before React files are written.

## Preflight

In addition to core preflight:

1. Detect the installed React version, renderer, build tool or metaframework, language mode, JSX transform, module format, source root, aliases, and test environment.
2. Inspect existing providers, composition roots, error boundaries, transport adapters, TanStack Query or equivalent server-state layer, forms, telemetry, and component-test setup.
3. Retrieve version-applicable official documentation for React and every activated package when lifecycle, peer compatibility, configuration, or build behavior affects the scaffold.
4. If a metaframework is present, load its specialization before planning routes, server rendering, environment access, or build configuration.

React without Next.js is supported. Preserve the repository's actual renderer and build system; do not add Next.js, Vite, or another framework merely because it appears in an example.

## Canonical Role Mapping

Adaptive mode preserves compatible placement. When React canonical layout is explicitly requested, map core roles to:

```text
src/
├── common/
│   ├── analytics/        # activated only when required
│   ├── clients/
│   ├── errors/
│   ├── logging/
│   ├── query-keys/       # server state only
│   └── runtime/
├── features/<feature>/
├── lib/modules/<module>/shared/contracts/
└── __tests__/
```

This mapping is React-specific. It does not redefine the abstract roles in client core.

## Capability Resolution

Prefer compatible existing packages. When a capability is absent and required, verify current versions and peers before proposing an exact installation:

| Capability | React specialization |
| --- | --- |
| Runtime wire validation | Repository standard; Zod is the documented TypeScript default |
| Server-state synchronization | TanStack Query |
| Non-trivial forms | React Hook Form and its resolver adapter when schema integration requires it |
| Local operational logging | Existing logger; otherwise `debug` behind `AppLogger` |
| Remote error reporting | Existing or explicitly requested provider behind the repository facade |
| Product analytics | Existing or requested provider behind `ProductAnalytics` |
| Component tests | Existing runner plus React Testing Library when UI behavior is generated |
| Transport | Existing compatible adapter; otherwise platform `fetch` behind `IClientApi` |

Do not activate a package merely because it is installed. A read-only view does not require form tooling; a feature without a meaningful event does not require analytics. Do not infer Vite plugins merely because Vitest is used.

Safe optional fallbacks are narrow:

- a declined transport library may use platform `fetch` behind `IClientApi`;
- declined optional analytics may reuse a typed no-op adapter;
- declined remote reporting leaves local operational logging only.

A serialized-contract feature, server-state feature, complete UI slice, or required test boundary remains blocked if its required validated contract, state adapter, or test capability cannot be resolved.

## Foundation Mapping

Create only missing React-compatible boundaries:

```text
common/errors/       AppError + unknown normalization
common/logging/      AppLogger port + local/provider adapters
common/clients/      IClientApi + createClientApi
common/runtime/      composition root + stable browser accessor
common/analytics/    conditional ProductAnalytics port/adapter
```

Use factories for dependency-heavy infrastructure:

```text
createAppLogger(config) -> AppLogger
createClientApi(deps) -> IClientApi
createProductAnalytics(config) -> ProductAnalytics   # conditional
create<Feature>Api(deps) -> I<Feature>Api
```

Browser instances are application-scoped. Request scope is a metaframework concern and exists only when server rendering captures request-bound dependencies.

## Feature Mapping

Preserve:

```text
component
  -> query adapter
    -> I<Feature>Api
      -> <Feature>Api
        -> IClientApi
          -> network
```

Canonical placement, adjusted in adaptive mode:

```text
lib/modules/<module>/shared/contracts/<operation>.contract.ts
common/query-keys/<feature>.ts                  # server state only
features/<feature>/api.ts                       # port + implementation + factory
features/<feature>/api.runtime.ts               # stable composition-root accessor
features/<feature>/hooks.ts                     # query/mutation hooks
features/<feature>/sync.ts                      # complex cache sync only
features/<feature>/schemas.ts                   # form/UI validation only
features/<feature>/domain.ts|helpers.ts          # real pure policy/mapping only
features/<feature>/components/*                 # business/presentation split
__tests__/...                                   # mirrored public boundaries
```

Parse untrusted responses in the feature API and keep concrete query/cache mechanics in hooks or `sync.ts`. Presentation components render and emit callbacks only. A business component or feature hook may coordinate route-local `submit -> sync -> navigate` behavior. Use a `useMod*` hook only for genuine multi-hook or multi-step feature orchestration.

## Verification

Run generated contract, API, hook, component, and factory tests before project-wide checks. Then run the repository's typecheck, touched-file lint, and production build. Add DOM, JSX, alias, or peer tooling only when repository configuration proves it is required.
