# Next.js Server Configuration

> Use Next.js and its selected environment adapter at the outer boundary, validate private build and server runtime inputs at their actual lifecycles, and inject narrow configuration inward.

Apply the [server configuration contract](../../../../core/configuration.md). The corresponding [client Next.js guide](../../../../../client/frameworks/reactjs/metaframeworks/nextjs/environment.md) owns browser build/runtime exposure.

## Boundary

```text
host-injected external values
  -> app-owned executable lifecycle schema
  -> PrivateBuildConfig or ServerRuntimeConfig
  -> Next.js composition / infrastructure factory
  -> narrow configuration or port
  -> application dependency
```

Rules:

- Keep ordinary `process.env` access inside environment adapters and explicit bootstrap/test boundaries.
- Permit unrelated ambient Next.js, platform, and tooling variables; exclude them from normalized application configuration.
- Import validated lifecycle surfaces only from server/build composition code that owns the corresponding work.
- Pass focused values such as `{ connectionString }` or `{ apiKey }`, never `process.env`, a complete env object, or a generic configuration service.
- Keep framework-neutral controllers, services, use cases, repositories, entities, and wire contracts independent of environment access.
- Never log supplied configuration values or whole configuration objects.

## T3 Env Specialization

[`@t3-oss/env-nextjs`](https://env.t3.gg/docs/nextjs) is the supported Next.js adapter when selected or detected. It remains a runtime/framework implementation detail.

Detect the installed Next.js, T3 Env, validator, TypeScript, module-system, and deployment versions. Retrieve their current official documentation before choosing exact schema APIs, runtime maps, public exposure, module splitting, configuration imports, or standalone packaging.

A unified physical module is acceptable when it preserves lifecycle behavior and server/browser import safety. Split private build, server runtime, or browser modules when a unified import would validate unavailable values or make private schemas client-reachable.

## Build and Runtime Separation

`PrivateBuildConfig` contains only private values actually consumed while Next.js builds:

- prerender/static-generation data access;
- code generation; or
- another build-executed integration whose value can change the produced artifact.

`ServerRuntimeConfig` contains values consumed by the running server, worker-like hook, route handler, action, or server-side integration.

Do not force runtime-only secrets into the build environment. Validate those values before the deployed server accepts dependent traffic or work. Likewise, if artifact-producing build code consumes a value that can change the output, classify it as a build input and account for it in cache identity even when server runtime also uses a value with the same external name.

One deployable-owned field declaration may be composed into both lifecycle schemas. This shares validation intent, not an injected value or global env object; build and runtime receive values independently from their hosts.

## Publication and Deployment Side Effects

Credentials that only authorize source-map upload, artifact publication, deployment, or another external side effect are not cached build inputs. A credential rotation does not change the artifact, and restoring a cached artifact does not replay the side effect.

Model publication as a separate app/package-owned task that consumes the completed build outputs. It must execute when publication is requested even when the build is restored from cache, so keep it non-cacheable or use the detected build system's equivalent side-effect semantics. Make its credentials available without adding them to build cache identity. Retrieve the installed task runner's current official documentation before choosing the exact dependency, cache, and environment mechanisms.

If a value genuinely changes generated output as well as authorizing publication, split the output-affecting build field from the publication credential and classify each by its actual consumer.

## Framework-Native Composition

Use the Next.js lifecycle and module boundaries appropriate to the installed version. Map the validated surface into framework-neutral factory arguments:

```text
DATABASE_URL
  -> ServerRuntimeConfig.databaseUrl
  -> makeDatabase({ connectionString: databaseUrl })
  -> Database port/adapter
```

Application-scoped clients are safe only when they hold no request-specific state. Cookies, headers, sessions, actors, and request-bound clients remain request scoped.

Reusable packages accept normalized options or ports. They never import the Next.js environment module, own deployable variable names, or load a workspace-root environment file.

## Schema and Example Contract

- Executable schemas are the source of truth.
- `.env.example` is a checked, human- or agent-authored projection of activated environment-backed schemas.
- A drift check rejects missing schema keys and stale example keys while preserving comments and safe placeholders.
- Validation handles declared values only and does not reject unrelated ambient variables.
- Error output identifies fields and expected shapes without echoing supplied values.

## Tests

- Test private-build and server-runtime schemas independently.
- Provide harmless fake values only before importing the lifecycle boundary under test.
- Do not place server-secret placeholders in global browser test setup.
- Verify a production build without unrelated runtime-only credentials.
- Verify server composition/startup with required runtime configuration.
- Test explicit configuration modes for optional providers or jobs.

## Review Checklist

- [ ] Private build and server runtime fields are classified by actual consumption.
- [ ] Runtime-only secrets are not required by unrelated builds.
- [ ] Output-affecting build values influence build cache identity.
- [ ] Publication/deployment credentials are supplied to a separate side-effect task and do not hash the cached build.
- [ ] A build cache hit cannot skip a requested publication/deployment side effect.
- [ ] T3 Env/Next.js stay at the outer adapter boundary.
- [ ] Inner layers and reusable packages receive only narrow normalized configuration or ports.
- [ ] Unknown ambient variables are permitted but excluded from application configuration.
- [ ] Schema/example parity is enforced without real secrets.
- [ ] Validation failures never print supplied values.
- [ ] Exact integration and packaging follow current official documentation for installed versions.

## Official References

- [Next.js: Environment Variables](https://nextjs.org/docs/app/guides/environment-variables)
- [Next.js Configuration](https://nextjs.org/docs/app/api-reference/config/next-config-js)
- [T3 Env for Next.js](https://env.t3.gg/docs/nextjs)
- [T3 Env Customization](https://env.t3.gg/docs/customization)
