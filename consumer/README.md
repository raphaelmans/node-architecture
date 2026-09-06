# Architecture Skill Consumers

The generated `guides/` bundle is deprecated and `copy-guides.sh` is disabled.

Use [INSTALL-SKILLS.md](./INSTALL-SKILLS.md) to install `$client`, `$server`, `$monorepo`, and `$development`.

Then use [Architecture Initialization](./ARCHITECTURE-INIT.md) with `/development init` to create a sectioned reference index and lightweight entry point. Detailed conventions remain in their authoritative references and load only when relevant.

## Source Model

- `development/core/`, `development/tools/`, `development/frameworks/`, and `development/runtimes/` own local development guidance; `development/skill/` packages it and `development/skill-maintenance/` checks source drift.

- `client/core/` and `client/frameworks/` remain the canonical authoring documents.
- `server/core/` and `server/runtime/` remain the canonical server authoring documents.
- `client/skill/references/` contains portable, concern-based derivatives for agents.
- `server/skill/references/` contains the matching server derivatives.
- The sibling `client/skill-maintenance/` and `server/skill-maintenance/` directories flag references that require review after source-doc changes; they are not installed with the skills.

Legacy integration files in this directory now provide migration pointers only; they are no longer copied into consumer repositories.
