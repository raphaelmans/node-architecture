# Architecture Guides

> **STOP — These files are generated. Do not edit them directly.**

---

## DO NOT EDIT FILES IN THIS DIRECTORY

All files under `guides/` are **generated** by `copy-guides.sh` from the
[node-architecture](https://github.com/your-org/node-architecture) source repository.

Any direct edits made here **will be overwritten** the next time `copy-guides.sh` is run.

This includes:

- `guides/client/`
- `guides/server/`
- `guides/AGENTS-MD-ALIGNMENT.md`
- `guides/UPDATE-ARCHITECTURE.md`
- This file

---

## How to Make Changes

All architecture updates must be made in the **source repository**, then synced here.

1. Open the `node-architecture` repo on your machine.
2. Follow `guides/UPDATE-ARCHITECTURE.md` for the update workflow.
3. Re-run `copy-guides.sh` to push the changes to this repo:

```bash
# From the node-architecture repo root:
./copy-guides.sh /absolute/path/to/this/repo
```

---

## Setting Up Your AGENTS.md / CLAUDE.md

If you have not yet wired these guides into your AI agent configuration, see:

```
guides/AGENTS-MD-ALIGNMENT.md
```

It contains the mandatory core references, framework selection guide, and a
copy-paste `AGENTS.md` / `CLAUDE.md` template.

---

## Directory Contents

```text
guides/
  client/
    core/          ← MANDATORY for all client work
    frameworks/    ← Opt-in per tech stack (React, Next.js, ...)
  server/
    core/          ← MANDATORY for all server work
    runtime/       ← Opt-in per tech stack (tRPC, Supabase, Next.js, ...)
  AGENTS-MD-ALIGNMENT.md   ← How to configure AGENTS.md / CLAUDE.md
  UPDATE-ARCHITECTURE.md   ← How to update these guides (edit in source repo only)
  README.md                ← This file
```
