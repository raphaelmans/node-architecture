# Monorepo Environment Ownership

> Keep configuration owned by deployable applications, keep reusable packages environment-free, and keep task-environment policy distinct from application validation.

## Consumer and Lifecycle Matrix

Classify configuration by who consumes it and when:

| Consumer | Build lifecycle | Runtime lifecycle |
| --- | --- | --- |
| Browser | `BrowserBuildConfig` | `BrowserRuntimeConfig` |
| Non-browser | `PrivateBuildConfig` | `ServerRuntimeConfig` |

The first three surfaces may be backed by host-injected environment variables. `BrowserRuntimeConfig` is a public resource loaded by the browser and is not a process environment.

## Deployable Ownership

Every deployable application owns the schemas, examples, and composition that translate its external configuration. In a workspace:

```text
apps/client-a/    owns its browser build/runtime boundaries
apps/server-a/    owns its private build/server runtime boundaries
apps/worker-a/    owns its private build/worker runtime boundaries
packages/*/       declare focused configuration needs only
```

Do not create a root environment file or a shared environment package. Reusable packages receive normalized values, options, or ports from each consuming application. Even when two applications use the same external variable name, each application independently owns its deployment contract.

A deployable may reuse field declarations across its own lifecycle schemas when the same variable is genuinely consumed in more than one lifecycle. This is schema composition inside one environment boundary, not cross-application environment ownership.

## Executable Schemas and Examples

Executable schemas are authoritative and validate only declared application variables. Unrelated ambient variables are permitted and excluded from the validated result.

Each deployable keeps its own `.env.example` as a checked, human- or agent-authored projection of its environment-backed schemas. Browser runtime resources use their own executable schema and example; they do not become entries in `.env.example` merely because they are configuration.

## Task Environment Policy

Build orchestration controls which ambient variables reach a task and which participate in cache identity. That policy is separate from application validation:

```text
host environment
  -> task environment policy       availability + cache identity
  -> deployable schema             application validation
  -> narrow application config     dependency injection
```

Required outcomes:

- every variable or file that can change cached task output influences that task's cache identity;
- credentials that only authorize publication, deployment, or another external side effect do not influence the cached build's identity;
- publication/deployment runs as a separate non-cacheable task, or equivalent side-effect execution, that consumes build outputs and still runs when those outputs are restored from cache;
- runtime-only values do not invalidate a build that does not consume them;
- non-cacheable development or execution tasks may allow undeclared ambient framework/tool variables through;
- a task runner filtering an ambient variable is not repaired by weakening the application schema; and
- root-wide environment inputs are used only when they genuinely affect every participating task.

The build-system specialization resolves the exact current mechanism from version-matched official documentation. Framework inference or environment pass-through never replaces the executable application schema.

## Scaffolding and Verification

Foundation scaffolding establishes environment ownership without inventing variables, root environment files, shared environment packages, browser runtime loaders, cache credentials, or provider accounts.

When a deployable declares configuration:

1. classify every field by consumer and lifecycle;
2. create only the activated schemas and delivery boundaries;
3. map external names into narrow application configuration;
4. coordinate task availability and cache identity with the detected build system;
5. check schema/example parity; and
6. verify build and runtime boundaries independently.

## Related Docs

- [Monorepo Architecture](./architecture.md)
- [Package Boundaries](./package-boundaries.md)
- [Scaffolding](./scaffolding.md)
- [Client Configuration Boundaries](../../client/core/configuration.md)
- [Server Configuration Boundaries](../../server/core/configuration.md)
