# Server Configuration Boundaries

> Treat external configuration as a deployable-owned adapter: validate declared inputs at the lifecycle that consumes them, normalize once, and inject narrow values inward.

## Configuration Surfaces

Non-browser configuration separates build execution from runtime execution:

| Surface | Consumer | Materialization | Visibility |
| --- | --- | --- | --- |
| `PrivateBuildConfig` | Artifact-producing build work | While producing the artifact | Private |
| `ServerRuntimeConfig` | Server, worker, job runner, or function | At its runtime composition boundary | Private |

The host supplies these values to the relevant execution. Application code does not retrieve or refresh environment-backed configuration over HTTP.

## Deployable-Owned Schemas

Each deployable owns executable schemas for the external values it consumes. A schema:

- declares only application-owned variables for one lifecycle surface;
- permits unrelated ambient variables rather than validating the entire process environment;
- returns only declared, normalized fields;
- identifies invalid fields without printing supplied values; and
- is the source of truth for requiredness, optionality, defaults, and conditional configuration modes.

A framework, platform, or tool may consume undeclared ambient variables directly. When application composition begins to depend on one, add it to the appropriate schema.

## Lifecycle Validation

Validate at the earliest lifecycle boundary where the dependent work has its required values:

```text
build host values
  -> PrivateBuildConfig schema
  -> build work that depends on them

runtime host values
  -> ServerRuntimeConfig schema
  -> runtime composition
  -> accept dependent traffic or work
```

Do not validate runtime-only secrets during a build that does not consume them. Conversely, a variable used while prerendering, generating code, or producing another artifact belongs to `PrivateBuildConfig` when it can change that artifact, even when a similarly named value is also used at runtime.

When one external variable is genuinely consumed in both lifecycles, define its field contract once inside the deployable and compose it into both lifecycle schemas. Each lifecycle still receives and validates its own host-injected value; this does not create a shared global environment object.

Credentials that only authorize publication, deployment, source-map upload, or another external side effect are task execution inputs, not `PrivateBuildConfig`. Run that side effect separately from the cached artifact-producing task so it still executes when requested after a cache hit; make its credentials available without making credential rotation invalidate the artifact cache. Resolve the exact mechanism from the installed build system's current official documentation.

## Configuration Modes

Optional capabilities use explicit modes. Activating a mode requires every field needed to compose that capability; missing unrelated variables do not implicitly enable or disable it.

```text
capability disabled
  -> no provider configuration required

capability enabled
  -> validate complete provider configuration
  -> construct provider adapter
```

Failure blocks only work that depends on the configuration. A required server-wide database configuration normally prevents startup, while configuration for a lazily activated administrative job may fail that job without redefining unrelated application behavior.

## Composition and Framework Integration

Map external names into framework-neutral configuration before crossing inward:

```text
DATABASE_URL
  -> executable environment schema
  -> ServerRuntimeConfig.databaseUrl
  -> composition root or framework provider
  -> DatabaseConfig { connectionString }
  -> database adapter
```

Framework-owned dependency injection, configuration modules, lifecycle hooks, and testing support remain the outer composition mechanism. Inner controllers, services, use cases, repositories, domain objects, and shared contracts receive focused values or ports and never import the environment adapter, `process.env`, or a complete configuration object.

Reusable packages accept normalized options through factories, constructors, or framework integration modules. They do not own deployable variable names or read a workspace-wide environment.

## Documentation and Tests

The executable schemas are authoritative. A committed `.env.example` is a checked, human- or agent-authored projection of all environment-backed lifecycle schemas owned by that deployable. Group fields by lifecycle and consumer, retain safe comments/placeholders, and never include real credentials.

Verify:

- valid, missing, malformed, optional, and conditional schema cases;
- schema-to-example key parity;
- build validation only for values that can affect the produced artifact;
- separate execution of requested publication/deployment side effects after cached or uncached builds;
- runtime validation before dependent traffic or work;
- framework composition with narrow configuration; and
- logs and failures that never echo supplied configuration values.

## Related Docs

- [Server Conventions](./conventions.md)
- [Server Scaffolding Contract](./scaffolding.md)
- [Next.js Environment Configuration](../runtime/nodejs/metaframeworks/nextjs/environment-variables.md)
- [NestJS Configuration](../runtime/nodejs/metaframeworks/nestjs/configuration.md)
- [Client Configuration Boundaries](../../client/core/configuration.md)
- [Monorepo Environment Ownership](../../monorepo/core/environment.md)
