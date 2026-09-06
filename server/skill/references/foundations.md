# Foundations Slice

Use this slice for server layering, framework-neutral controllers, module structure, dependency direction, factories, dependency injection, kernel placement, and architectural reviews.

## Contents

- [Canonical flow](#canonical-flow)
- [Layer ownership](#layer-ownership)
- [Decision flow](#decision-flow)
- [Folder contract](#folder-contract)
- [Dependency injection](#dependency-injection)
- [Configuration boundaries](#configuration-boundaries)
- [Review checklist](#review-checklist)

## Canonical Flow

For organization-backed product workspaces, membership, invitations, or resource scopes, load [tenancy](foundations/tenancy.md). This is distinct from the monorepo `workspace` slice. Authorization and RBAC are conditional security leaves, not mandatory foundations for every module.

For scaffolding, treat this flow as a portable role contract rather than a universal language syntax or directory tree. A documented runtime specialization may map it to concrete paths; for an unlisted runtime/language, derive and approve that mapping from repository evidence and current official guidance before writing.

Single-project and monorepo topologies are equal canonical mappings. Load `workspace` when roles cross package boundaries; the Node.js/TypeScript tree below is one mapping, not a requirement to colocate deployable apps and reusable packages.

For a new monorepo module, the workspace slice defaults activated capability and adapter roles to packages. The folder tree below still applies to a cohesive existing app-local module until migration is explicitly requested.

```text
framework adapter
  -> framework-neutral controller
    -> one service OR one use case
      -> repository/provider port
        -> infrastructure adapter
```

Return plain typed results in reverse. Keep HTTP, RPC, framework, vendor, and database types at their owning boundaries.

## Layer Ownership

| Layer | Owns | Must not own |
| --- | --- | --- |
| Adapter | request extraction, authentication, coarse transport gates, input parsing, observability scope, status/envelope, transport error mapping | capability authorization, command mapping, domain rules, direct repository calls |
| Controller | shared input-to-command mapping, actor mapping, one application call, null-to-domain-error decisions, public result mapping | framework types, transactions, multi-service orchestration |
| Use case | multi-service workflow, transaction boundary, outbox and post-commit coordination | transport serialization, vendor SDK mechanics |
| Service | one-domain rules, capability authorization, and self-contained reads/writes | framework context, unrelated workflows |
| Repository/provider adapter | persistence or vendor mechanics and known error translation | business policy or transport behavior |

Every public capability enters through a framework-neutral controller. Internal workers may call a use case or service directly when they are not presenting the same public capability.

## Decision Flow

```text
Is this a public transport capability?
  yes -> add/reuse a controller

Does the operation coordinate multiple services, a transaction,
an outbox record, or a distinct post-commit side effect?
  yes -> controller -> use case
  no  -> controller -> one service
```

Do not create pass-through use cases for simple reads or single-domain writes. Do not remove a controller merely because a capability is simple; it still protects public mapping from framework coupling.

## Folder Contract

The following tree is the documented Node.js/TypeScript specialization. Other runtimes and languages map the same roles to their native package, module, composition, and test conventions instead of copying these paths.

```text
src/
  env.ts                                app-owned validated runtime configuration
  app/api/ or routes/                 framework entrypoints
  lib/
    shared/
      kernel/                         dependency-light contracts and ports
      infra/                          database, runtime composition, logger, provider adapters
      utils/                          pure cross-module helpers
    modules/<module>/
      shared/contracts/               isomorphic request/response schemas
      <module>.router.ts               optional module-owned tRPC adapter
      controllers/
      use-cases/
      services/
      repositories/
      factories/
      errors/
      dtos/                            optional server-only commands
  database/migrations/                 logical migration boundary; adapt to the selected persistence tool
```

Keep the shared kernel small. Put a concept there only when multiple modules require it, it is stable, and it does not depend on a framework, ORM, provider SDK, or concrete logger.

Keep domain-specific repository interfaces and implementations under the owning module's `repositories/` folder, even when the implementation uses Drizzle. Reserve `shared/infra/db/` for the shared database client, schema/table definitions, transaction manager, and ORM-wide types; do not place `Drizzle<User|Transfer|Order>Repository` implementations there.

## Dependency Injection

Use constructor injection for application objects and factory functions for composition:

```ts
export function makeCreateUserController(): ICreateUserController {
  return new CreateUserController(
    new CreateUserUseCase(
      makeUserService(),
      getContainer().transactionManager,
      getContainer().appLogger,
      getContainer().productAnalytics,
    ),
  );
}
```

Adapters resolve controller factories only. Services and use cases receive narrow ports, never a service locator. Keep browser/request/runtime lifetimes in the composition root, not hidden inside modules.

## Configuration Boundaries

For local listener setup or worktree-specific origins, add `runtimes` and coordinate with installed `$development` when available. Generic host/port configuration remains deployable-owned; proxy-specific values remain development tooling concerns.

Treat validated environment configuration the same way. The deployable owns separate `PrivateBuildConfig` and `ServerRuntimeConfig` schemas for values genuinely consumed in those lifecycles. Schemas permit unrelated ambient variables, return only declared normalized fields, and remain the source of truth for a checked `.env.example` projection.

Build/runtime composition passes only focused values such as `{ connectionString }` or `{ apiKey }` into infrastructure. Never inject a process environment, complete configuration surface, or environment service locator into controllers or application layers. Framework-native DI may compose focused providers at the outer boundary without coupling portable application code to framework configuration lookup.

Validate each surface at the earliest boundary where its dependent work has the required values. Do not require runtime-only secrets during unrelated builds. Model optional capabilities as explicit modes: a disabled capability requires no provider configuration, while an enabled capability validates every field needed to construct that adapter. A configuration failure blocks only the dependent work unless that dependency is required to start the whole deployable.

Frameworks and hosts may consume undeclared ambient variables freely. Add one to an application schema only when application composition depends on it; schema validation must not attempt to own the entire process environment.

`PrivateBuildConfig` contains only private values that can affect a produced artifact. Credentials that merely authorize publication or deployment belong to a separate side-effect task that still runs when requested after a build cache hit; they do not invalidate the artifact cache.

## Review Checklist

- Framework types stop at the adapter.
- Capability routers stay with their owning module; shared transport setup and the root router stay under shared infrastructure.
- Each controller calls exactly one service or use case.
- Use cases exist only for genuine orchestration.
- Repositories and provider adapters contain no business policy.
- Domain repositories remain module-owned; shared database infrastructure remains domain-neutral.
- Dependencies point inward; domain/application layers do not import infrastructure.
- Shared kernel additions satisfy the stability and cross-module tests.
- Factories make dependency graphs explicit and tests can substitute every boundary.
- Build/runtime configuration is validated at its consuming lifecycle and injected narrowly from composition.
- New abstractions solve current complexity rather than anticipated complexity.

## Derivation Sources

Derived from the server indexes, core README, configuration, conventions, controller, transaction, and runtime-boundary guides. Exact source paths and fingerprints are maintained outside the portable skill package.
