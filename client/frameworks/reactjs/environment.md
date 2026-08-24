# React Configuration

> React consumes configuration; the selected build tool or metaframework owns how external values enter the application.

Apply the [client configuration contract](../../core/configuration.md) first. Detect the installed build tool/metaframework, validator, module format, and deployment model, then retrieve their current official documentation before choosing exact environment syntax.

## Standalone React

A standalone browser application normally uses `BrowserBuildConfig`:

```text
CI or local build environment
  -> build-tool public-variable mechanism
  -> executable app-owned schema
  -> BrowserBuildConfig
  -> React composition root / focused provider
  -> browser dependencies
```

The external values are public and become part of the generated browser artifact. Changing a container environment after the build does not alter an already generated static bundle unless the deployment deliberately creates a separate runtime resource.

React itself does not prescribe prefixes, environment files, static substitution, or validation libraries. Resolve those details from the installed build tool. T3 Env Core is a supported typed adapter when compatible with the selected stack; it remains an outer application dependency rather than a reusable-package requirement.

## Optional Browser Runtime Configuration

Activate `BrowserRuntimeConfig` only when the browser must receive public configuration independently of the build:

```text
static file or HTTP response
  -> executable runtime-resource schema
  -> BrowserRuntimeConfig
  -> dependent React application/capability boundary
```

Load and validate it when the dependent work begins. If the application shell requires the resource, bootstrap is that first use. If only one route or capability requires it, failure remains scoped there.

Do not expose host/container environment variables directly to browser code. A server, entrypoint, or deployment adapter must intentionally project selected public values into the runtime resource.

## React Composition

Map external names to normalized fields before React sees them. Supply focused configuration or already-constructed ports through the composition root and specific providers:

```text
PUBLIC_API_ORIGIN
  -> BrowserBuildConfig.apiOrigin
  -> createClientApi({ baseUrl: apiOrigin })
  -> ClientApi provider
```

Do not expose a complete environment/configuration object through React context. A capability that loads `BrowserRuntimeConfig` owns that loading state and passes only the values or ports its children require.

## Schema and Example Contract

- The executable schema is authoritative.
- `.env.example` is a checked, human- or agent-authored projection of browser-build environment fields.
- A browser runtime resource uses its own schema/example and does not appear in `.env.example` as though it were a process environment variable.
- Unknown build-host variables are ignored by application validation.
- Validation errors identify fields without echoing supplied values.

## Verification

- Test schema valid/missing/malformed cases.
- Verify every browser-exposed field is intentionally public.
- Run the production build with the installed build tool.
- Confirm build-affecting values participate in workspace cache identity when applicable.
- Test runtime-resource loading at the narrowest dependent React boundary when activated.

## Official Implementation References

- [React documentation](https://react.dev/)
- [Vite environment variables and modes](https://vite.dev/guide/env-and-mode)
- [T3 Env Core](https://env.t3.gg/docs/core)

These sources describe supported specializations. Resolve exact APIs, prefixes, file loading, and build behavior from the target repository's installed versions.
