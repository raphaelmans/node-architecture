# OpenCode Integration Guide

This guide explains how to integrate project rules into OpenCode for new projects while minimizing stale instructions.

Primary reference:

- https://opencode.ai/docs/rules/#custom-instructions

## Goal: Avoid Stale Instructions

Use one canonical source of truth for architecture and coding rules, then reference those files from OpenCode config.

Recommended precedence for maintainability:

1. `opencode.json` `instructions` field (primary)
2. `AGENTS.md` explicit external-file loader instructions (fallback / compatibility)

Rule:

- Avoid duplicating long policy text in multiple files.
- Keep `opencode.json` and `AGENTS.md` as pointer layers that reference canonical docs.

## Using `opencode.json`

This is the recommended approach from OpenCode docs.

`opencode.json` example:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "CONTRIBUTING.md",
    "client/core/onboarding.md",
    "client/core/overview.md",
    "client/core/conventions.md",
    "server/core/overview.md"
  ]
}
```

Why this is best for freshness:

- You update canonical docs once.
- OpenCode loads current instructions from file paths/globs.
- Teams share the same committed instruction map.
- Instruction files from `instructions` are combined with `AGENTS.md` files at runtime, so keeping `AGENTS.md` thin avoids drift.

Also supported by OpenCode:

- globs (for example `docs/rules/*.md`)
- remote URLs in `instructions` (useful for shared org-wide standards)

Operational note:

- Remote instruction fetch uses a short timeout, so keep critical core rules in local files.

## Manual Instructions in `AGENTS.md`

OpenCode does not automatically parse file references in `AGENTS.md`; use explicit instructions that tell the agent when and how to load files.

`AGENTS.md` example:

```md
# Project Rules Loader

## External File Loading

CRITICAL: When a task references a rule file, read it using the Read tool on a need-to-know basis.

Instructions:

- Do not preload every referenced file.
- Load only files relevant to the current task.
- Treat loaded files as mandatory project instructions.

Core references:

- @CONTRIBUTING.md
- @client/core/onboarding.md
- @client/core/overview.md
- @client/core/conventions.md
- @server/core/overview.md
```

Use this approach when:

- you cannot rely on `opencode.json` yet
- you need explicit lazy-loading behavior in project-level instructions
- you want to keep `AGENTS.md` concise while referencing modular rule files

## Best-Practice Pattern for This Repo

Canonical contracts live in:

- Client core: `client/core/*`
- Client framework specifics: `client/frameworks/*`
- Server core: `server/core/*`
- Server runtime specifics: `server/runtime/*`

Pointer layers should stay minimal:

- `opencode.json` points to canonical docs
- `AGENTS.md` instructs how to load canonical docs

## New Project Bootstrap

1. Create canonical architecture docs first (`core` + framework/runtime docs).
2. Add `opencode.json` with `instructions` pointing to those docs.
3. Add minimal `AGENTS.md` fallback loader instructions if needed.
4. Validate by running a task and confirming OpenCode reads the intended files.

## Stale-Prevention Checklist

- [ ] One canonical file per rule/concern
- [ ] `opencode.json` contains only pointers (no duplicated policy text)
- [ ] `AGENTS.md` contains loading behavior + pointers only
- [ ] Canonical docs are updated first when rules change
- [ ] Periodic consistency audit checks for contradictory guidance

## References

- OpenCode Rules: https://opencode.ai/docs/rules/#custom-instructions
- OpenCode Rules (full page): https://opencode.ai/docs/rules/
