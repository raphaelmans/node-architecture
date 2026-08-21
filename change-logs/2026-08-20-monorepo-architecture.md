# Monorepo Architecture

Date: 2026-08-20

## Summary

Added monorepo architecture as an equal canonical topology alongside the existing single-project client and server mappings. The new guidance preserves clean/onion dependency direction while using workspace packages only for justified ownership, reuse, runtime-isolation, and build boundaries.

## Architecture

- Added tool-, package-manager-, language-, framework-, and runtime-agnostic monorepo core guidance.
- Defined deployable applications as composition roots and package-graph endpoints.
- Defined activation rules separately from placement: new monorepo modules use capability/adapter packages by default, existing cohesive app-local modules remain until explicitly migrated, and unused roles remain absent.
- Allowed every app/package to consume shared config through declared tooling dependencies without weakening runtime onion boundaries.
- Kept clients isolated from server capability and infrastructure packages.
- Established inward package/source dependencies, public exports, app-owned environment configuration, package-owned tasks, and layered boundary enforcement.
- Established the sequence `monorepo foundation -> explicit application foundations -> vertical slices` without generating placeholder applications or packages.

## Turborepo Specialization

- Added Turborepo as the first supported thin build-system specialization.
- Kept exact configuration fields, commands, cache semantics, CI filtering, boundary features, and remote-cache behavior out of canonical core.
- Required detection of the installed or selected version and retrieval of matching official documentation before tool-sensitive changes.
- Kept CI-provider setup and remote caching opt-in.

## Skills and Coordination

- Added the portable `$monorepo` skill with `foundations`, `packages`, `scaffolding`, and `turborepo` slices.
- Added source-drift tracking for the monorepo skill.
- Added topology-aware `workspace` slices to `$client` and `$server`.
- Assigned cross-package manifests, exports, dependencies, task coordination, and atomicity to `$monorepo`; `$client` and `$server` continue to own architecture inside resolved package boundaries.

## Repository Alignment

- Added glossary terms and ADRs for equal canonical topologies and thin version-resolved specializations.
- Updated root, contribution, installation, client, and server guidance to recognize both physical mappings.
- Preserved unlisted frameworks, runtimes, package managers, and build systems as supported through generic core conventions plus current authoritative resources.
