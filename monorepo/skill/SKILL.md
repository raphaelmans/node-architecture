---
name: monorepo
description: Apply this repository's portable monorepo architecture when designing, explaining, reviewing, scaffolding, testing, implementing, or refactoring multi-package workspaces. Use for workspace foundations, application/package topology, internal package extraction, dependency boundaries, cross-package vertical slices, task and cache conventions, environment ownership, CI scope, or build-system integration. Turborepo is a thin supported specialization, not an allowlist or a frozen configuration manual.
---

# Monorepo Architecture

Route workspace work through the smallest relevant architecture slices. Preserve the user's requested operation and do not turn explanation, diagnosis, review, or planning into repository mutation.

## Start

1. Inspect the target repository, instructions, dirty files, manifests, lockfile, applications, packages, exports, dependencies, tasks, environment ownership, and build system.
2. Determine whether the target uses a single-project or monorepo topology; both are canonical and architecture roles do not change.
3. Select the smallest relevant slice set from the routing table and read every selected reference completely.
4. Preserve cohesive existing module ownership. For a new monorepo module, place activated roles through the package convention unless the user explicitly requests app-local scope; never migrate or split an existing module implicitly.
5. Retrieve authoritative documentation matching every detected or selected tool version before making version-sensitive decisions.
6. When a change activates client or server roles, load the relevant installed `$client` or `$server` guidance when available and keep role-specific work inside the boundaries resolved here.
7. Verify package and onion boundaries, package/task graphs, outputs, environment inputs, focused behavior, and affected builds.

## Route Slices

| Slice | Load when the task involves | Reference |
| --- | --- | --- |
| `scaffolding` | `$monorepo scaffold`, workspace foundation, application coordination, or cross-package vertical slices | [references/scaffolding.md](references/scaffolding.md) |
| `foundations` | topology selection, deployable applications, onion alignment, composition roots, or workspace architecture | [references/foundations.md](references/foundations.md) |
| `packages` | package extraction, contracts/domain/capabilities/adapters/UI/config, exports, dependencies, tasks, environment, or boundaries | [references/packages.md](references/packages.md) |
| `turborepo` | Turborepo detection, task/cache mapping, development, affected CI, boundary checks, or migration | [references/turborepo.md](references/turborepo.md) |

Treat `workspace`, `topology`, and `architecture` as aliases for `foundations`; `library`, `internal package`, `dependency`, `exports`, `task`, `environment`, and `boundary` as aliases for `packages`; and `turbo`, `cache`, `affected`, and `task graph` as aliases for `turborepo`.

Examples:

- `$monorepo scaffold foundation`: `scaffolding` + `foundations` + `packages`; add `turborepo` only when detected or requested.
- `$monorepo scaffold slice users/create`: `scaffolding` + `foundations` + `packages`; add client/server guidance and the selected build-system slice for activated boundaries.
- Review package imports: `packages`; add `foundations` when the problem involves onion direction.
- Configure current Turborepo caching or CI: `turborepo` + `packages`, then retrieve matching official docs.

When invoked without a task, show the slice menu and two or three context-aware examples. Do not automatically audit or mutate the repository.

## Scaffolding Commands

```text
$monorepo scaffold foundation
$monorepo scaffold slice <module>/<operation>
```

Foundation scaffolding establishes only missing workspace roles. It never invents deployable applications, business modules, placeholder packages, root environment files, CI providers, or remote-cache accounts.

A slice is one complete operation across every activated boundary. Cross-package changes are atomic: resolve manifests, exports, dependency edges, implementations, composition, and verification before writing.

## Preserve These Invariants

- Single-project and monorepo topologies are equal canonical mappings.
- Deployable applications are package-graph endpoints and own composition.
- For a new monorepo module, activated capability and adapter roles use package placement by default even with one deployable consumer; unused roles remain absent.
- Preserve cohesive existing app-local modules until migration is explicit. Packages remain stable module/role boundaries—not one package per operation or onion layer.
- Client apps may import contracts, explicit cross-runtime domain packages, and UI packages; they never import server capabilities or infrastructure adapters.
- Capabilities depend inward on contracts/domain and ports; concrete adapters depend on and implement inward-owned ports.
- Packages use declared workspace dependencies and intentional exports; never traverse into another package's files.
- Apps and packages may consume config packages through declared tooling/dev dependencies; config packages never import runtime application packages.
- Package tasks own task logic; the workspace root coordinates them. Parallel checks remain cache-correct when dependency sources change.
- Deployable applications own and validate environment configuration; reusable packages receive narrow injected values and never read a shared root environment.
- Experimental build-system checks supplement rather than replace stable package and source-boundary enforcement.
- Tool specializations remain thin. Official sources matching the target version own current syntax and behavior.

## Coordination Boundary

`$monorepo` owns package creation, manifests, exports, workspace dependency edges, shared task coordination, and changes spanning packages. `$client` and `$server` own architecture inside resolved app/package boundaries.

If client or server scaffolding discovers a required cross-package change, stop before partial writes, resolve it through this contract, then resume role-specific scaffolding.

## Review and Change Discipline

For reviews, report evidence with file and line references, separate violations from optional improvements, and do not implement fixes without authorization.

For implementation, preserve unrelated changes, classify every boundary as `reuse`, `create`, `patch`, `blocked`, or `not-needed`, obtain dependency/integration approvals, run focused validation first, and report detected versions plus authoritative sources used.
