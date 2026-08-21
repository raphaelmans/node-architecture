# Monorepo Scaffolding Contract

Use this contract when establishing workspace foundations or creating one vertical slice that spans package boundaries. It is build-system-, package-manager-, language-, framework-, and runtime-agnostic.

## Scope

```text
$monorepo scaffold foundation
$monorepo scaffold slice <module>/<operation>
```

`foundation` establishes only missing workspace infrastructure and conventions. It does not invent deployable applications, business modules, example packages, providers, root environment files, CI providers, or remote-cache accounts.

A vertical slice implements one operation across every activated boundary. It may span several applications and packages, but it is not itself a package.

Application creation and application foundations remain explicit:

```text
monorepo foundation
  -> selected client/server/worker application foundations
    -> vertical slices
```

## Safety and Evidence

Before writing:

1. Detect repository topology, package manager, lockfile, workspace discovery, build system and version, application packages, internal packages, package exports, dependency edges, task scripts, environment ownership, boundary checks, CI, and dirty files.
2. Locate client/server architecture roles, cohesive existing module owners, composition roots, wire contracts, shared domain rules, persistence/provider ports, concrete adapters, and tests.
3. Classify every required change as `reuse`, `create`, `patch`, `blocked`, or `not-needed`.
4. Retrieve authoritative version-matched sources for every tool-sensitive decision.
5. Show topology, package activation, dependency edges, dependency installations, and verification plan before affected writes.
6. Obtain approval for dependency installation, package-manager selection, framework/application initialization, CI provider setup, remote caching, or other external integration.

Evidence order:

```text
target repository + manifests + lockfile + installed tool behavior
  -> monorepo/client/server architecture conventions
    -> version-matched official documentation
      -> official release notes or source
```

Fail closed only for the affected boundary when evidence is missing or contradictory. Preserve unrelated and uncommitted work; never overwrite an existing file merely to force canonical placement.

## Foundation Scaffold

Resolve only the missing roles:

```text
workspace identity and package discovery
root task coordination
package-local task ownership
package naming, exports, and dependency policy
shared config packages when multiple packages require them
environment ownership
boundary verification
local cache correctness
```

Preserve the detected package manager. If none exists, propose the specialization's current supported recommendation, explain the consequences, and obtain approval. Do not create empty package or application placeholders.

## Vertical Slice Scaffold

For `<module>/<operation>`:

1. Discover the real operation, public contract, client/server consumers, access policy, application owner, persistence, side effects, and runtime needs.
2. Activate only roles required by current behavior; unused domain, adapter, UI, config, or other roles remain absent.
3. Resolve placement using [Package Boundaries](./package-boundaries.md): explicit scope first, then cohesive existing module ownership, then package defaults for a new monorepo module.
4. Resolve package names, public exports, workspace dependencies, tooling dependencies, and application composition before writing.
5. Apply the client and server scaffolding contracts inside the resolved applications/packages.
6. Write atomically across the complete activated slice; do not split an existing module or leave packages with unresolved imports, exports, adapters, or composition.

## Scaffolding Ownership

```text
$monorepo
  owns package creation, manifests, exports, dependency edges,
  workspace tasks, and changes spanning multiple packages

$client
  owns client architecture inside resolved app/package boundaries

$server
  owns server architecture inside resolved app/package boundaries
```

When client or server scaffolding discovers a required cross-package change, stop before partial writes, apply this coordination contract, then resume role-specific work inside the resolved boundaries.

## Tool-Sensitive Execution

Core specifies outcomes, not vendor syntax. A thin specialization must:

1. Detect the installed or selected tool version.
2. Retrieve official guidance applicable to that version.
3. Select the current supported workspace, task, cache, environment, boundary, development, and CI mechanisms.
4. Apply the smallest configuration consistent with core conventions.
5. Verify behavior with the actual tool and report the version and sources used.

Do not persist copied vendor manuals, frozen schema URLs, exhaustive CLI references, or version-specific feature catalogs in core.

## Verification

Verify, as applicable:

- package discovery and unique package identities;
- declared workspace dependencies and public exports;
- no filesystem traversal across packages;
- dependency and onion boundary checks;
- task ordering, parallel cache invalidation, and real file outputs;
- app-owned environment validation and cache inputs;
- focused contract, domain, capability, adapter, client, server, and composition tests;
- type/static checks, lint/format checks, builds, and affected CI selection;
- no credentials, speculative packages, partial slices, or unrelated rewrites.
- no accidental split between existing app-local ownership and package-default ownership.

Report the detected topology, tool and package-manager versions, consulted sources, package activation decisions, reused/created/patched/blocked roles, dependency edges, verification results, and remaining actions.
