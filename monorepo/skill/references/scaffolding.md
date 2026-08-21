# Monorepo Scaffolding Slice

Use this slice for workspace foundations and cross-package vertical slices.

## Commands

```text
$monorepo scaffold foundation
$monorepo scaffold slice <module>/<operation>
```

Foundation creates only missing workspace roles. It does not invent apps, domain packages, root environment files, CI providers, remote caching, or example behavior. Application creation and client/server/worker foundations are explicit steps.

A vertical slice is one complete business operation across activated boundaries; it may span packages but is not itself a package.

## Preflight

1. Detect topology, package manager/version, lockfile, build system/version, workspace/package discovery, apps, packages, manifests, exports, dependencies, tasks, outputs, environment ownership, boundaries, CI, cache, and dirty files.
2. Locate activated client/server roles, cohesive existing module owners, composition roots, contracts, shared domain rules, capability owners, ports, adapters, and tests.
3. Classify every role as `reuse`, `create`, `patch`, `blocked`, or `not-needed`.
4. Retrieve authoritative version-matched sources for every tool-sensitive decision.
5. Show package activation, dependency edges, installs, external integrations, and verification before affected writes.

Preserve unrelated changes and compatible topology. Never overwrite, emit placeholders, persist generator metadata, or leave unresolved imports/exports/composition.

## Foundation Roles

```text
workspace identity and package discovery
root coordination of package-owned tasks
package naming, exports, and dependency rules
shared configs only when multiple packages require them
app-owned environment policy
boundary and cache correctness verification
```

Preserve a detected package manager. When absent, propose the build specialization's supported recommendation and obtain approval before initialization or installation.

## Slice Workflow

1. Resolve `<module>/<operation>`, public contract, consumers, access, application owner, persistence, effects, and runtimes.
2. Activate only roles required by current behavior; unused roles stay absent.
3. Resolve placement in order: explicit scope, cohesive existing ownership, then package defaults for a new monorepo module. Never split an existing module for one operation.
4. Resolve manifests, exports, workspace and tooling dependencies, package tasks, and application composition atomically.
5. Apply installed client/server architecture guidance inside those boundaries.
6. Verify focused behavior, boundaries, task/cache graphs, static checks, tests, and affected builds.

`$monorepo` owns cross-package changes. If `$client` or `$server` encounters one, stop before partial writes, resolve it here, then resume within the resolved package.

## Tool Resolution

Core owns required outcomes. For exact workspace syntax, task mechanisms, cache fields, environment behavior, CI filters, or boundary features, detect the version and retrieve its official documentation. Report the version and sources used; do not preserve a copied vendor manual.
