# Server Scaffolding Slice

Date: 2026-08-18

## Summary

Added repository-aware scaffolding to the existing `$server` router. The action bootstraps missing foundations or creates one real vertical capability in listed or unlisted server runtimes without introducing a separate skill, rigid generator, or generator-owned source of truth.

## Commands

```text
$server scaffold foundation
$server scaffold <feature>/<operation>
$server scaffold <feature>/<operation> using canonical layout
```

## Behavior

- Applies the runtime-neutral foundation and capability contract to any detected server stack; Node.js, Next.js, Express, and Hono are documented specializations rather than an allowlist.
- Derives unlisted runtime/framework integration from repository evidence and current primary documentation.
- Requires version-applicable primary-source retrieval for dependency, config, lifecycle, module-format, build, and deployment decisions; missing or contradictory evidence blocks affected writes.
- Defaults to adapting the repository layout; canonical placement requires explicit user intent and never permits overwriting.
- Treats canonical layout as a stack-relative boundary-to-path mapping rather than one universal TypeScript tree.
- Completes runtime, framework, package-manager, contract, access-policy, application-boundary, persistence, dependency, dirty-file, and verification preflight before writing.
- Shows one exact, versioned dependency command and requires approval before installation.
- Preserves the mandatory `framework adapter -> controller -> one service or one use case -> repository/provider port` flow.
- Uses a service for one-domain behavior and a use case only for multi-service transactions, outbox coordination, or post-commit workflows.
- Reuses structural equivalents, reports naming drift, creates only missing files, and never emits placeholder contracts or scaffold metadata.
- Keeps Node.js primitives and package defaults in the Node.js specialization; core names capabilities only.
- Requires explicit endpoint access policy and blocks durable production behavior when no approved persistence adapter exists.
- Keeps authentication and transport-wide gates in adapters while enforcing ownership, tenant, domain-role, and operation-specific capability authorization in services/use cases.
- Keeps observability context separate from opaque database-only `TransactionContext`.
- Requires contract, controller, application, and real framework-adapter tests for public capabilities.

## Artifacts

- Added `server/core/scaffolding.md` as the runtime-agnostic canonical contract.
- Added a Node.js implementation plus Next.js, Express, and Hono adapter specializations under `server/runtime/nodejs/`.
- Added `server/skill/references/scaffolding.md` as the portable execution slice.
- Updated `$server` routing and agent metadata.
- Updated root/consumer discovery, server navigation, core guidance, and the standalone HTML Skills page.
- Added the ninth slice to repository-only source-drift tracking.

## Scope

The router does not bootstrap an arbitrary application or framework merely to fit a documented example. It does not use a rigid generator script, install production persistence without approval, or scaffold authentication, analytics, transactions, outbox, rate limiting, RPC/spec tooling, or a logger vendor unless the capability requires them.
