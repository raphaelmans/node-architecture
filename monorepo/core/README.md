# Monorepo Core

This directory defines portable monorepo architecture conventions. It does not prescribe a build system, package manager, language, framework, runtime, or version-sensitive configuration syntax.

## Documents

| Document | Purpose |
| --- | --- |
| [Architecture](./architecture.md) | Equal canonical topologies, application/package roles, and onion alignment |
| [Package Boundaries](./package-boundaries.md) | Package activation, exports, dependency matrix, tasks, and environment ownership |
| [Scaffolding](./scaffolding.md) | Foundation and vertical-slice workflow, evidence, atomicity, coordination, and verification |

## Core Invariants

- A single-project path and a workspace package may realize the same architecture role.
- Dependencies point toward stable application and domain policy.
- Applications select concrete adapters in composition roots; inward packages never select outward infrastructure.
- New monorepo modules place activated capability and adapter roles in packages by default; unused roles remain absent, and cohesive existing app-local modules remain until explicitly migrated.
- Packages are stable module/role ownership boundaries—not one package per operation or onion layer.
- Tool specializations retrieve version-matched official guidance instead of embedding vendor manuals.
