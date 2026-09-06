# Runtimes Slice

For local startup and concurrent worktree origins, coordinate with installed `$development` using its Next.js or Node.js mapping as appropriate. Express/Hono and other HTTP servers must consume the assigned port at their actual listener through generic bootstrap configuration. Development tooling supplies existing self-origin variables only when needed and resolves separate frontend/API targets within the same checkout. Keep callback, cookie, and trusted-origin validation here; application source and schemas stay unaware of the proxy.

Use this slice for the documented Node.js composition and concrete tRPC, OpenAPI, Next.js, Express, Hono, NestJS, Supabase, Pino, FormData, caching, cron, metadata, and security adapter behavior.

## Scaffolding

Load the generic server scaffolding contract first. Node.js and its documented adapters are specializations, not an allowlist. Detect the installed runtime/language mode, module format, framework, host, packages, and build/test setup; retrieve version-applicable official resources before applying configuration, lifecycle, module, build, or deployment behavior. For another runtime/framework, keep the generic contract and derive its role mapping from repository evidence plus current primary sources.

In a workspace, also load `workspace`. Apply runtime behavior inside resolved app/capability/adapter packages, keep environment validation with deployable apps, and retrieve current build-system/framework guidance for exact package consumption and build behavior.

## Runtime Rule

Choose only the adapters present in the target project. Every runtime entrypoint must preserve:

```text
framework request/context
  -> request observability + authentication + rate limiting
  -> normalized shared input
  -> framework-neutral controller
  -> validated shared payload
  -> framework envelope/status
  -> central error mapping
```

No framework request/context type crosses the controller boundary. Adapters resolve controller factories only.

Adapters authenticate and apply rate limits or transport-wide coarse gates. Ownership, tenant membership, domain roles, target-resource lookup, and operation-specific authorization remain in the selected service/use case so alternate transports cannot bypass them.

## Next.js Route Handlers

- Keep the framework's current route-handler entrypoint as a thin Fetch/Next adapter.
- Parse malformed JSON through a helper that throws `ValidationError`.
- Establish observability before authentication or application work.
- Validate shared input and payload schemas.
- Return `ApiResponse<T>` for success and the canonical error response for failure.
- Build security-sensitive redirects from a validated application origin.

Choose the caching model supported and enabled by the installed Next.js version. Preserve explicit lifetime, invalidation identity, stale-while-revalidate semantics, and read-your-own-writes only where the interaction requires them; retrieve current official documentation for exact directives, functions, signatures, and allowed call sites.

Validate FormData as untrusted input, including total size, file count, type, and storage path. Authenticate cron handlers and make them idempotent. Keep metadata/SEO generation deterministic and avoid leaking request secrets.

## Next.js Environment Configuration

Use one deployable-owned logical environment boundary with separate private-build and server-runtime surfaces. When T3 Env is detected or selected, it is a Next.js adapter rather than an inward architecture dependency.

- Declare secrets under the server schema without a public prefix.
- Declare browser-safe values explicitly under the client schema using the public exposure convention required by the installed framework.
- Keep ordinary `process.env` access inside the env module and test/runtime bootstrap code.
- Import validated values only at runtime composition and infrastructure factories; inject narrow configuration rather than the env object.
- Keep controllers, services, use cases, repositories, entities, and isomorphic contracts free of environment access.
- Parse strings, especially booleans, deliberately; JavaScript truthiness is not configuration validation.
- Validate private build values only when they can affect the produced artifact. Validate runtime-only credentials before accepting dependent traffic/work; do not require them for unrelated builds.
- Keep publication/deployment credentials out of cached build identity. Run the requested external side effect as a separate non-cacheable task, or equivalent, that consumes build outputs and still executes after a cache hit; resolve exact task/environment syntax from current build-system documentation.
- Permit unrelated ambient variables and exclude them from normalized application configuration.
- Treat executable schemas as authoritative and `.env.example` as a checked human- or agent-authored projection.
- Retrieve current official Next.js and environment-adapter documentation for runtime maps, configuration-module syntax, build-time imports, and standalone packaging.
- Scope fake import-time values to Node/server test setup and retain a real Next.js build or boundary check in CI.

## Express and Hono

For Express, determine async rejection propagation from the installed major's official documentation. Parse input with shared normalization, call one controller, and ensure failures reach central error mapping exactly once after routes.

For Hono, use its current validation extension point to throw the shared `ValidationError`; do not let a framework-default response bypass the canonical envelope. Adapt the shared numeric error status to the installed framework's accepted status type at the boundary. Keep Hono context variables at middleware/adapter scope.

For NestJS, retain its native configuration module, typed/focused providers, dependency injection, lifecycle, and testing facilities at the outer application boundary. The deployable validates `ServerRuntimeConfig`; inward portable code receives normalized constructor/factory arguments rather than a generic configuration service. Reusable dynamic modules accept normalized options and never read the deployable environment. Keep decorators, pipes, guards, interceptors, and exception filters outside the same framework-neutral controller boundary.

## tRPC and OpenAPI

Treat tRPC as a transport, not the application architecture. Inline shared authentication, coarse transport gates/context enrichment, lifecycle logging, and `AppError` conversion middleware in the base procedure setup. Preserve domain errors as causes. Let procedures validate input and call capability controllers; services/use cases retain capability authorization.

Keep a capability router with its owning module at `src/lib/modules/<module>/<module>.router.ts`. Keep only tRPC initialization, shared middleware/context, and the root router under `src/lib/shared/infra/trpc/`. Do not create a parallel `src/server/trpc/` application tree.

Use a module-owned session resolver in tRPC context. Do not construct Supabase repositories or swallow infrastructure failures there.

For OpenAPI, generate schemas from canonical Zod contracts and route operations to the same controllers. Maintain parity tests while transports coexist.

## Supabase

- Use request-scoped publishable-key clients for authenticated user operations.
- Isolate secret-key clients in explicit privileged server-only factories.
- Put Auth, Storage, and database SDK mechanics behind ports/adapters.
- Translate provider errors before they cross inward.
- Keep storage paths scoped and validate uploads before adapter calls.
- Use Drizzle repositories for application persistence and RLS for direct user-scoped Supabase access according to the chosen boundary.

## Pino

Implement the kernel `AppLogger` port without exposing Pino types inward. Merge active correlation at the adapter, configure recursive/nested redaction, and ensure sink failure cannot change application behavior.

## Runtime and Deployment Checks

- Confirm library/framework versions from the target package manifest before applying version-sensitive examples.
- Reuse serverless-safe singleton infrastructure only when it holds no request-scoped state.
- Construct cookie/header/session-dependent dependencies per request.
- Keep database connection pooling and cache invalidation consistent with the deployment topology.
- Test the real adapter boundary in addition to procedure/controller unit tests.

## Review Checklist

- Only installed/requested adapters influence the design.
- Framework and provider types stop at infrastructure boundaries.
- Request-scoped state cannot leak through global singletons.
- All adapters share controllers, contracts, and central error policy.
- Capability authorization remains effective through HTTP, workers, CLIs, and other transports.
- Version-sensitive Next.js/tRPC/Supabase behavior is verified against the target dependencies.
- Next.js configuration is validated at its consuming build/runtime lifecycle and injected narrowly; public exposure is explicit.
- NestJS configuration uses framework-native outer composition without leaking generic configuration lookup inward.
- Privileged provider paths are explicit and server-only.
- Runtime tests cover actual parsing, context, serialization, and error formatting.

## Official Implementation References

- [Node.js API documentation](https://nodejs.org/docs/latest/api/)
- [Next.js documentation](https://nextjs.org/docs)
- [Express documentation](https://expressjs.com/)
- [Hono documentation](https://hono.dev/docs/)
- [NestJS documentation](https://docs.nestjs.com/)
- [tRPC documentation](https://trpc.io/docs)
- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
- [Supabase documentation](https://supabase.com/docs)
- [Pino documentation](https://getpino.io/#/)
- [T3 Env documentation](https://env.t3.gg/docs/nextjs)

These libraries are reference specializations at the outer adapter and runtime boundary. Preserve their architectural roles and selection rationale while deriving exact middleware, handler, configuration, and SDK syntax from the target repository, installed versions, and current official documentation.

## Derivation Sources

Derived from all documents under `server/runtime/`, plus the core controller, contract, error, transaction, security, and telemetry rules those adapters extend. Exact paths and fingerprints are maintained outside the portable skill package.
