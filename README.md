# Node.js Architecture Documentation

> Source repository for the client/server architecture guides and the downstream `guides/` bundle.

This repo documents patterns and conventions, not package versions. Check the target project's `package.json` for actual versions.

## Repo Surfaces

| Surface | Purpose |
| ------- | ------- |
| [server/README.md](./server/README.md) | Canonical backend architecture docs |
| [client/README.md](./client/README.md) | Canonical frontend architecture docs |
| [legacy/README.md](./legacy/README.md) | Historical, non-canonical reference material |
| [consumer/README.md](./consumer/README.md) | Downstream `guides/` bundle docs and agent-integration templates |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Source-repo maintenance rules |
| [copy-guides.sh](./copy-guides.sh) | Copies the docs and standalone HTML artifacts into another repo's `guides/` directory |
| [assets/server-architecture-guide.html](./assets/server-architecture-guide.html) | Standalone interactive server architecture guide |
| [assets/client-architecture-guide.html](./assets/client-architecture-guide.html) | Standalone interactive client architecture guide |
| [assets/architecture-guide.html](./assets/architecture-guide.html) | Standalone interactive full-stack architecture guide |

## Technology Stack

| Layer | Technologies |
| ----- | ------------ |
| Server | Next.js, tRPC, Drizzle ORM, PostgreSQL, Zod, Pino |
| Client | Next.js/React, TanStack Query, Zod, adapter-based API/telemetry ports, `debug`, optional Sentry |
| Testing | Vitest (unit), Playwright (E2E) |
| Auth | Supabase Auth or custom auth |
| Storage | Supabase Storage or custom storage |

## Source Tree

```text
node-architecture/
  client/       canonical frontend docs
  server/       canonical backend docs
  legacy/       historical references, not source of truth
  consumer/     files copied into downstream guides/
  assets/       supplemental artifacts
  change-logs/  documentation change history
```

## Quick Start

### Editing Architecture Docs

1. Read [CONTRIBUTING.md](./CONTRIBUTING.md).
2. Start with the relevant canonical index:
   [client/core/README.md](./client/core/README.md) or [server/core/README.md](./server/core/README.md).
3. Keep framework/runtime details inside framework/runtime folders; keep core docs agnostic.
4. Treat [legacy/](./legacy/README.md) as reference-only material.

### Publishing to a Consumer Repo

1. Read [consumer/UPDATE-ARCHITECTURE.md](./consumer/UPDATE-ARCHITECTURE.md).
2. Run `./copy-guides.sh /absolute/path/to/target-repo`.
3. In the consumer repo, follow `guides/AGENTS-MD-ALIGNMENT.md`.

## Project Folder Contract

This documentation assumes a core-aligned application structure. It is a reference contract, not a literal required tree.

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

## Principles

| Principle | Description |
| --------- | ----------- |
| Explicit over implicit | No magic, clear dependency flow |
| Feature-based organization | Co-locate code by domain |
| Type-safe end-to-end | Zod-backed contracts across boundaries |
| Layered architecture | Clear client/server/runtime responsibilities |
| Composition over inheritance | Small focused units composed together |
