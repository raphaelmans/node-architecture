# Node.js Server Scaffolding

This guide implements the [server scaffolding contract](../../core/scaffolding.md) for an existing Node.js repository. It is a known specialization, not a requirement for other runtimes or languages.

When Node.js is inside a workspace, apply server roles within the resolved app/capability/adapter packages. `$monorepo` coordinates package creation, exports, workspace dependency edges, task ownership, and cross-package atomicity before Node.js-specific files are written.

## Preflight

In addition to core preflight:

1. Detect the installed Node.js version, JavaScript or TypeScript mode, module format, package manager, workspace package, source root, aliases, and build output.
2. Detect the web framework/transport, runtime host, validation, error/envelope, logging, observability, authentication, persistence, transaction, API-description/RPC, and test capabilities.
3. Inspect the lockfile and installed type declarations for exact current state.
4. Retrieve version-applicable official documentation for Node.js, the selected framework, and every activated package when configuration, lifecycle, module loading, peer compatibility, or deployment behavior affects the scaffold.

JavaScript and TypeScript repositories may both apply the core contract. Preserve the repository's established language mode; do not add TypeScript or convert module format merely to match examples.

## Canonical Role Mapping

Adaptive mode preserves compatible placement. For a TypeScript repository that explicitly requests the documented Node.js canonical layout, map roles to:

```text
src/
├── lib/
│   ├── shared/
│   │   ├── kernel/             # errors, logger, response, ports
│   │   └── infra/              # runtime adapters and composition
│   └── modules/<module>/
│       ├── shared/contracts/
│       ├── controllers/
│       ├── services/
│       ├── use-cases/          # capability-driven only
│       ├── repositories/       # persistence-driven only
│       ├── providers/          # integration-driven only
│       └── factories/
└── __tests__/                  # mirrors generated boundaries
```

Framework entry points use the selected adapter specialization. JavaScript repositories adapt extensions and type mechanisms without changing role ownership.

## Capability Resolution

Prefer compatible existing packages and primitives. When absent and required, verify current versions and peers before proposing an exact installation:

| Capability | Node.js specialization |
| --- | --- |
| Runtime wire validation | Repository standard; Zod is the documented TypeScript default |
| Test tooling | Existing runner; Vitest is the documented TypeScript fallback |
| Operational logging | Existing logger; otherwise structured `console` behind `AppLogger` |
| Request/trace context | `AsyncLocalStorage` when supported by the installed Node.js version |
| Request IDs | `crypto.randomUUID` when supported by the installed Node.js version |
| Outbound HTTP | Existing client; otherwise Node's supported `fetch` behind a provider port |
| Persistence | Existing ORM/database; new production selection requires approval |
| Framework adapter | Detected framework or evidence-derived adapter |
| API description/RPC | Existing or explicitly requested OpenAPI/tRPC integration |
| Product analytics | Existing/requested provider behind `ProductAnalytics` |

Do not activate authentication, analytics, transactions, outbox, rate limiting, Pino, OpenAPI, tRPC, or persistence merely because a package is installed.

Optional fallbacks are narrow:

- no logger dependency may use structured `console` behind `AppLogger`;
- no HTTP dependency may use a version-supported native `fetch` behind a provider port;
- no tracing SDK may use a verified `AsyncLocalStorage` correlation adapter;
- declined optional analytics may be omitted or use an existing typed no-op adapter.

A serialized contract, complete capability, public adapter, or durable operation remains blocked if its required validation, tests, framework integration, or persistence cannot be resolved.

## Foundation Mapping

Create only missing Node.js implementations of core roles:

```text
shared/kernel/errors        AppError kinds + safe public/private detail split
shared/kernel/logger        AppLogger port
shared/kernel/response      compatible response contracts
shared/infra/logger         structured runtime adapter
shared/infra/observability  AsyncLocalStorage implementation when activated
shared/infra/http           centralized transport error/envelope helpers
app-owned environment      activated lifecycle schemas + normalized configuration mapping
composition root            application-scoped construction and wiring
tests                       focused tests for every created boundary
```

Use explicit factories. Create an environment boundary only for variables the deployable consumes, validate them at their build/runtime lifecycle, and permit unrelated ambient variables. Keep validated configuration, pools, stateless provider clients, and logger adapters application-scoped. Create request scope only for captured cookies, sessions, actors, headers, or request-bound clients. Correlation comes from the active async scope, never business DTOs or transaction options.

## Capability Mapping

For TypeScript repositories, the conventional role mapping is:

```text
modules/<module>/shared/contracts/<operation>.contract.ts
modules/<module>/controllers/<operation>.controller.ts
modules/<module>/services/<module>.service.ts
modules/<module>/use-cases/<operation>.use-case.ts        # orchestration only
modules/<module>/repositories/<module>.repository.ts     # persistence only
modules/<module>/providers/<provider>.ts                 # integration only
modules/<module>/factories/<operation>.factory.ts
<selected framework entry point>
__tests__/<mirrored boundary>.test.ts
```

Controllers are plain TypeScript/JavaScript and import no framework request/response types. Framework adapters authenticate and apply transport-wide gates; services/use cases enforce ownership, tenant, domain-role, and operation-specific authorization.

## Adapter Specializations

- [Next.js](./metaframeworks/nextjs/scaffolding.md)
- [Express](./metaframeworks/express/scaffolding.md)
- [Hono](./metaframeworks/hono/scaffolding.md)

These adapters are examples, not an allowlist. For another Node.js framework, inspect its existing integration and retrieve current official documentation before deriving the adapter. A public capability remains atomic: if the adapter cannot be resolved, do not write inward capability files.

## Verification

Run focused contract, controller, application, authorization, framework-adapter, and generated infrastructure tests. Then run the repository's typecheck or static checks, touched-file lint/format checks, and production build. Verify module-format and runtime-host behavior with the actual configured commands.
