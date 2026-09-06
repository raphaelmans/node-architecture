# Client, Server, Monorepo, and Development Architecture Documentation

> Source repository for portable architecture guides and installable agent skills derived from them.

This repo documents patterns and conventions, not package versions. Check the target project's `package.json` for actual versions.

## Repo Surfaces

| Surface | Purpose |
| ------- | ------- |
| [server/README.md](./server/README.md) | Canonical backend architecture docs |
| [client/README.md](./client/README.md) | Canonical frontend architecture docs |
| [monorepo/README.md](./monorepo/README.md) | Canonical workspace topology and package-boundary docs |
| [development/README.md](./development/README.md) | Canonical architecture initialization, local startup and origin guidance |
| [development/skill/SKILL.md](./development/skill/SKILL.md) | Installable `$development init` and local setup skill |
| [client/skill/SKILL.md](./client/skill/SKILL.md) | Installable `$client` router derived from the client docs |
| [server/skill/SKILL.md](./server/skill/SKILL.md) | Installable `$server` router derived from the server docs |
| [monorepo/skill/SKILL.md](./monorepo/skill/SKILL.md) | Installable `$monorepo` router derived from the monorepo docs |
| [legacy/README.md](./legacy/README.md) | Historical, non-canonical reference material |
| [consumer/INSTALL-SKILLS.md](./consumer/INSTALL-SKILLS.md) | Install and update the architecture skills in another repository |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Source-doc and derived-skill maintenance rules |
| [copy-guides.sh](./copy-guides.sh) | Disabled legacy entrypoint with migration guidance |
| [assets/server-architecture-guide.html](./assets/server-architecture-guide.html) | Standalone interactive server architecture guide |
| [assets/client-architecture-guide.html](./assets/client-architecture-guide.html) | Standalone interactive client architecture guide |

## Technology Stack

| Layer | Technologies |
| ----- | ------------ |
| Server | Next.js, tRPC, Drizzle ORM, PostgreSQL, Zod, Pino |
| Client | Next.js/React, TanStack Query, Zod, adapter-based API/telemetry ports, `debug`, optional Sentry |
| Monorepo | Tool-agnostic workspace conventions with a thin, version-resolved Turborepo specialization |
| Testing | Vitest (unit), Playwright (E2E) |
| Auth | Supabase Auth or custom auth |
| Storage | Supabase Storage or custom storage |

## Source Tree

```text
node-architecture/
  client/       canonical frontend docs + portable skill + maintenance metadata
  server/       canonical backend docs + portable skill + maintenance metadata
  monorepo/     canonical workspace docs + thin build-system mappings + portable skill
  development/  architecture initialization + local startup contracts + framework mappings + skill
  legacy/       historical references, not source of truth
  consumer/     skill installation and migration guidance
  assets/       supplemental artifacts
  change-logs/  documentation change history
```

## Quick Start

### Editing Architecture Docs

1. Read [CONTRIBUTING.md](./CONTRIBUTING.md).
2. Start with the relevant canonical index:
   [client/core/README.md](./client/core/README.md), [server/core/README.md](./server/core/README.md), or [monorepo/core/README.md](./monorepo/core/README.md).
3. Keep framework/runtime details inside framework/runtime folders; keep core docs agnostic.
4. Treat [legacy/](./legacy/README.md) as reference-only material.

### Installing the Architecture Skills

1. Read [consumer/INSTALL-SKILLS.md](./consumer/INSTALL-SKILLS.md).
2. Install GitHub path `client/skill` from `raphaelmans/node-architecture` with destination name `client`.
3. Install GitHub path `server/skill` with destination name `server`.
4. Install GitHub path `monorepo/skill` with destination name `monorepo` when working across workspace packages.
5. Invoke `$client`, `$server`, or `$monorepo` with a concern or task, such as `$server contracts review this route` or `$monorepo scaffold slice users/create`.
6. Install `development/skill` with destination name `development`. Use `/development init` to create a sectioned `ARCHITECTURE.md` reference index and minimal agent-entrypoint pointer from applicable installed guidance, or `$development setup nextjs` for dependency installation, scripts, and worktree-aware local origins.

`copy-guides.sh` is disabled. Installable skills are the supported agent-facing distribution path.

## Repository Topology Contract

Single-project and monorepo topologies are equal canonical mappings. The roles and dependency direction stay fixed; physical placement follows repository evidence and the applicable topology guide.

### Single-project mapping

```text
src/
  <routes>/                    metaframework-owned routes (Next.js: app/)
  features/<feature>/          client feature modules
  components/                  shared UI components
  common/                      cross-feature client contracts/utilities
  lib/modules/<module>/shared/contracts/ canonical client/server Zod wire contracts
  lib/modules/<module>/shared/ shared pure domain transforms
  lib/modules/<module>/controllers/ framework-neutral server capability boundaries
```

### Monorepo mapping

```text
apps/<client|server|worker>/     deployable application composition roots
packages/contracts/<module>/     serialized client/server contracts when cross-package
packages/domain/<module>/        optional cross-runtime pure domain rules
packages/capabilities/<module>/  portable server application behavior and ports
packages/adapters/<module>-<provider>/ concrete infrastructure implementations
```

See [Monorepo Architecture](./monorepo/core/architecture.md) for activation and dependency rules. A workspace package is not automatically one onion layer.

## Principles

| Principle | Description |
| --------- | ----------- |
| Explicit over implicit | No magic, clear dependency flow |
| Feature-based organization | Co-locate code by domain |
| Type-safe end-to-end | Zod-backed contracts across boundaries |
| Layered architecture | Clear client/server/runtime responsibilities |
| Composition over inheritance | Small focused units composed together |
