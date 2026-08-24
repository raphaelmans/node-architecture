# Client Configuration Boundaries

> Classify configuration by consumer and lifecycle, validate it at the deployable boundary, and inject only the normalized values each dependency needs.

## Configuration Surfaces

Client-facing configuration has two distinct surfaces:

| Surface | Delivery | Materialization | Visibility |
| --- | --- | --- | --- |
| `BrowserBuildConfig` | Host environment supplied to the build | Embedded in browser output | Public |
| `BrowserRuntimeConfig` | Static resource or HTTP response loaded by the browser | When the dependent application work begins | Public |

An SSR or full-stack client may also participate in `PrivateBuildConfig` and `ServerRuntimeConfig`; those non-browser surfaces follow the [server configuration contract](../../server/core/configuration.md). Do not collapse the surfaces into one generic client/server environment object.

## Environment-Backed Browser Build Configuration

`BrowserBuildConfig` is an application-owned, public configuration surface. The selected build tool determines how external variables are exposed and embedded, but the architecture requires:

- an executable schema owned by the deployable application;
- validation at the build boundary before output depending on the values is accepted;
- deliberate normalization from external names and strings into application-facing fields;
- no secrets, credentials, or private variable names in browser-reachable modules; and
- build/cache invalidation for every external value or file that can change generated output.

The schema validates only declared variables. Unrelated ambient variables remain available to the framework or tooling and do not enter the validated result.

## Optional Browser Runtime Configuration

`BrowserRuntimeConfig` is not an environment-variable surface. Activate it only when the browser must obtain public configuration independently of the build, such as when one static artifact is promoted across deployments.

Load and validate the resource when the application or capability that depends on it begins. A failure blocks only the dependent work: a shell-wide API origin may block application startup, while checkout-only configuration blocks checkout rather than the whole application. Do not silently substitute `BrowserBuildConfig`; defaults and optional values belong in the runtime schema.

The runtime resource and any human-readable example are projections of the executable runtime schema. They never contain secrets.

## Schema Authority and Documentation

The executable schema is the source of truth. A committed `.env.example` is a checked, human- or agent-authored projection for environment-backed fields, with safe placeholders and useful comments.

Drift verification must detect:

- schema variables missing from the example;
- stale example variables absent from the schema; and
- browser-public fields accidentally classified as private or secret.

Unknown host variables do not make validation fail. Validation errors name the field and expected shape without printing supplied values.

## Composition and Dependency Injection

External names stop at the environment boundary:

```text
PUBLIC_API_ORIGIN
  -> executable schema
  -> BrowserBuildConfig.apiOrigin
  -> browser composition root
  -> narrow transport configuration
```

Reusable packages declare focused configuration needs and receive values, options, or ports from the application composition root. They never read a deployable environment, fetch a global runtime-config resource, or receive a complete configuration surface.

Framework providers may expose specific stable ports or focused configuration namespaces. Do not create a generic `useConfig()` or runtime-container service locator.

## Scaffolding and Verification

- Create a build configuration surface only when the application declares build-consumed public values.
- Create `BrowserRuntimeConfig` and its loader only when independent runtime delivery is explicitly required.
- Preserve the selected framework/build tool's native loading and lifecycle behavior.
- Retrieve current documentation for the installed framework, build tool, validator, module system, and deployment target before generating exact syntax.
- Test valid, missing, malformed, optional, and conditional values through each executable schema.
- Verify a production build for browser exposure and import-boundary safety.
- Verify runtime-resource failure at the narrowest dependent application boundary.

## Related Docs

- [Client Composition Root](./composition-root.md)
- [Client Scaffolding Contract](./scaffolding.md)
- [React Configuration](../frameworks/reactjs/environment.md)
- [Next.js Environment Configuration](../frameworks/reactjs/metaframeworks/nextjs/environment.md)
- [Server Configuration Boundaries](../../server/core/configuration.md)
- [Monorepo Environment Ownership](../../monorepo/core/environment.md)
