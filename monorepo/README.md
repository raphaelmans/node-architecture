# Monorepo Architecture Documentation

> Canonical guidance for applying the client and server architecture across deployable applications and reusable workspace packages.

Single-project and monorepo topologies are equal canonical mappings. This surface defines what changes when roles cross package boundaries without replacing the client or server architecture contracts.

## Source of Truth

| Surface | Owns |
| --- | --- |
| [Core](./core/README.md) | Tool-agnostic topology, package ownership, dependency direction, and scaffolding contracts |
| [Build Systems](./build-systems/README.md) | Thin mappings from core conventions to detected build systems |
| [Turborepo](./build-systems/turborepo/README.md) | Current supported build-system specialization and version-matched source resolution |
| [Monorepo Skill](./skill/SKILL.md) | Installable `$monorepo` router derived from these docs |

Rules:

- Architecture roles and dependency direction do not change between topologies.
- Workspace packages are ownership and reuse boundaries, not automatic onion layers.
- Deployable applications are composition roots and endpoints of the package graph.
- Cross-package scaffolding is coordinated here; client and server scaffolding own work inside resolved boundaries.
- Version-sensitive tool syntax comes from authoritative sources matching the detected or selected version.

## Canonical Reading Order

1. [Core Architecture](./core/architecture.md)
2. [Package Boundaries](./core/package-boundaries.md)
3. [Environment Ownership](./core/environment.md)
4. [Scaffolding Contract](./core/scaffolding.md)
5. The detected build-system specialization, currently [Turborepo](./build-systems/turborepo/README.md)
