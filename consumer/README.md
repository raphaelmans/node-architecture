# Architecture Guides

> **STOP — These files are generated. Do not edit them directly.**

All files under `guides/` are copied from the source `node-architecture` repository by `copy-guides.sh`.
Any direct edits inside `guides/` will be overwritten the next time the guides are synced.

## What Gets Copied

```text
guides/
  client/                  canonical frontend docs
  server/                  canonical backend docs
  legacy/                  historical reference docs
  README.md                this file
  AGENTS-MD-ALIGNMENT.md   agent include/template guidance
  UPDATE-ARCHITECTURE.md   source-repo update workflow
  OPENCODE-INTEGRATION.md  OpenCode integration patterns
```

## How to Make Changes

1. Edit the source `node-architecture` repository, not `guides/`.
2. Follow `guides/UPDATE-ARCHITECTURE.md` for the update workflow.
3. Re-run `copy-guides.sh` from the source repo root:

```bash
./copy-guides.sh /absolute/path/to/this/repo
```

## What To Read First

- `guides/client/` and `guides/server/` are canonical.
- `guides/legacy/` is reference-only and not source of truth.
- `guides/AGENTS-MD-ALIGNMENT.md` explains how to wire the guides into `AGENTS.md` / `CLAUDE.md`.
- `guides/OPENCODE-INTEGRATION.md` explains a thinner OpenCode-specific integration model.
