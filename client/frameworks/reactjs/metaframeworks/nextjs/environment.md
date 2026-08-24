# Next.js Configuration

> Preserve Next.js environment and rendering behavior while exposing separate typed configuration surfaces at the lifecycle that consumes them.

Apply the [client configuration contract](../../../../core/configuration.md), the [React specialization](../../environment.md), and the [server configuration contract](../../../../../server/core/configuration.md). In a monorepo, every schema remains owned by the deployable Next.js application.

## Surface Map

A Next.js deployable may activate four configuration surfaces:

| Surface | Source and consumer | Activation |
| --- | --- | --- |
| `BrowserBuildConfig` | Public host variables embedded into browser output by Next.js | Browser code consumes build-selected values |
| `PrivateBuildConfig` | Private host variables consumed by build tooling or build-executed server code | The build genuinely reads them |
| `ServerRuntimeConfig` | Host variables consumed by the running Next.js server | Server composition requires them |
| `BrowserRuntimeConfig` | Public resource loaded by browser code | Values must change independently of the browser build |

Do not call all four surfaces “the Next.js environment.” Consumer and lifecycle determine ownership, validation timing, browser exposure, and cache behavior.

## T3 Env as the Next.js Adapter

[`@t3-oss/env-nextjs`](https://env.t3.gg/docs/nextjs) is the supported typed adapter when selected or already installed. It provides a framework-aware bridge between executable schemas and Next.js environment exposure; it does not become an inward architecture dependency.

Before implementation, detect the installed Next.js, T3 Env, validator, TypeScript, module-system, and deployment versions. Retrieve their current official documentation before choosing:

- public-variable naming and static exposure;
- runtime maps or destructuring requirements;
- unified versus split modules;
- configuration-module imports;
- build-time validation wiring;
- server-only import guards; or
- standalone/server deployment packaging.

Do not copy a version table or remembered API into another project.

## Logical Separation, Adaptive Physical Shape

The four typed surfaces remain distinct even when the selected adapter can implement several of them in one physical module. A unified implementation is acceptable only when it preserves lifecycle validation and the browser/server import boundary.

Split modules when required to prevent server schemas, secret names, runtime-only validation, or server dependencies from becoming client-reachable. Do not create an isomorphic barrel that imports or re-exports server/private surfaces.

Application code does not receive a global env object. Outer Next.js modules map validated external fields into normalized configuration and focused dependencies.

## Lifecycle Validation

Validate only what the current lifecycle consumes:

```text
Next.js build
  -> BrowserBuildConfig
  -> PrivateBuildConfig only when build work consumes private values
  -> generated output

Next.js server execution
  -> ServerRuntimeConfig
  -> server composition
  -> dependent traffic/work

browser runtime capability
  -> load public runtime resource
  -> BrowserRuntimeConfig
  -> dependent browser work
```

Do not import a runtime-only server schema into the Next.js configuration merely to claim build-time validation. Runtime-only credentials may be absent during a portable build and must instead be validated before the server accepts work that requires them.

When prerendering, static generation, instrumentation, code generation, or another build path reads a private variable, that variable belongs to `PrivateBuildConfig` and affects the build task's cache identity. If the running server also consumes it, reuse its field declaration across the two deployable-owned schemas while validating each lifecycle independently.

## Browser Exposure

Only deliberately public `BrowserBuildConfig` fields may enter client-reachable code. Next.js public build values are frozen into the artifact according to the installed framework's documented behavior; changing server/container variables later does not rewrite existing browser assets.

`BrowserRuntimeConfig` is an independent public file or response. Activate it only when runtime delivery is required. Validate it where dependent browser work begins, and scope failure to that work. Never use it for secrets or silently fall back to `BrowserBuildConfig`.

## Composition

```text
external Next.js variable
  -> app-owned executable schema
  -> typed lifecycle surface
  -> server/browser composition boundary
  -> focused config or constructed port
  -> dependency
```

Server components, route handlers, actions, instrumentation, and infrastructure factories may participate in outer composition according to the installed framework lifecycle. Client components receive only browser-safe values or ports. Reusable packages never import the Next.js environment adapter.

## Schema and Example Contract

- Executable schemas are authoritative.
- `.env.example` is a checked, human- or agent-authored projection of environment-backed fields across the activated build and server-runtime schemas.
- Group example fields by lifecycle/consumer and use safe placeholders only.
- Unknown ambient framework/platform variables are permitted and excluded from normalized application configuration.
- Validation failures identify variable names and expectations without printing supplied values.
- Browser runtime resources use their own schema/example rather than masquerading as environment variables.

## Tests and Deployment Verification

- Test each schema independently with valid, missing, malformed, optional, and conditional values.
- Scope fake values to tests that load the relevant lifecycle boundary.
- Keep browser-oriented tests free of server-secret setup so they can reveal accidental server imports.
- Verify the production build with only its genuine build inputs.
- Verify server startup/execution with its runtime inputs.
- Verify browser runtime-resource behavior only when activated.
- Confirm standalone or container output includes the selected environment adapter using the installed framework's current packaging contract.

## Checklist

- [ ] Every field is classified by consumer and lifecycle.
- [ ] Browser build values are explicitly public and contain no secrets.
- [ ] Private build values exist only when build work consumes them.
- [ ] Server runtime values are not required by unrelated builds.
- [ ] Browser runtime delivery is opt-in and validated at dependent use.
- [ ] Physical schema shape preserves logical surface and import separation.
- [ ] External names stop at outer composition.
- [ ] `.env.example` key parity is checked against executable schemas.
- [ ] Build cache inputs match actual build consumption.
- [ ] Exact Next.js/T3 Env integration is derived from current official documentation for installed versions.

## Official References

- [Next.js: Environment Variables](https://nextjs.org/docs/app/guides/environment-variables)
- [Next.js Configuration](https://nextjs.org/docs/app/api-reference/config/next-config-js)
- [T3 Env for Next.js](https://env.t3.gg/docs/nextjs)
- [T3 Env Core](https://env.t3.gg/docs/core)
