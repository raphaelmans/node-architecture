# OpenCode Integration Guide (Shared Rules + External References)

Primary reference:

- https://opencode.ai/docs/rules/#referencing-external-files

This guide explains how to integrate project rules into OpenCode while minimizing stale instructions and keeping rule reuse easy across many repos.

## What OpenCode Loads (Additive)

OpenCode loads rule text from multiple sources and combines them.

1) `AGENTS.md` (auto-loaded)

- OpenCode searches from the current directory upward.
- The nearest matching file wins for the local slot (`AGENTS.md` preferred over `CLAUDE.md`).
- A global file may also apply: `~/.config/opencode/AGENTS.md`.

2) `opencode.json` `instructions` (explicit includes)

- Any files (or globs) listed in `instructions` are loaded in addition to `AGENTS.md`.
- Remote URLs are supported, fetched with a short timeout (~5s).

Design rule:

- Keep `AGENTS.md` small and repo-specific.
- Put reusable, canonical rules in separate files and include them via `opencode.json`.

## Recommended Pattern

1. Canonical docs live in modular files (one concern per file).
2. Each repo keeps a thin `AGENTS.md` for repo facts + caveats.
3. Each repo uses `opencode.json` `instructions` to include canonical docs.

Avoid:

- Duplicating the same policy text across multiple files.
- A large `AGENTS.md` that drifts from the canonical docs.

## Using `opencode.json` (Preferred)

Example (repo-relative paths):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "CONTRIBUTING.md",
    "docs/rules/*.md",
    "packages/*/AGENTS.md"
  ]
}
```

Notes:

- `instructions` accepts file paths, glob patterns, and remote URLs.
- Remote URLs are best-effort due to the short timeout; keep critical rules local.

## Referencing External Files ("@...") and Lazy Loading

OpenCode does not automatically parse `@file.md` references inside `AGENTS.md`.
If you want an `@...` "read on demand" workflow, you must explicitly instruct the agent to treat `@...` references as files to read lazily.

Minimal `AGENTS.md` snippet:

```md
## External File Loading (Lazy)
CRITICAL: When you encounter a reference like `@path/to/rules.md`, use your Read tool to load it only if it is relevant to the current task.
- Do not preload every referenced file.
- When loaded, treat it as mandatory instructions.
```

Implementation detail:

- In some OpenCode templates (commands/agents), `@...` tokens may be resolved automatically. Do not rely on this behavior for `AGENTS.md`.

## Sharing Rules Across Repos (Options)

1) Git submodule (recommended)

- Add this repo as a submodule, for example `vendor/node-architecture/`.
- Use repo-relative globs in `opencode.json`.

Pros: portable, versionable, CI-friendly; enables recursive `**` globs.
Cons: submodule workflow overhead.

2) Symlink (local-only)

- Symlink a shared rules directory into the repo.

Pros: quick locally.
Cons: often breaks across OS/CI; not reliably shareable.

3) Remote URL (org-wide baseline)

```json
{
  "instructions": [
    "https://raw.githubusercontent.com/my-org/shared-rules/<sha>/entry.md"
  ]
}
```

Pros: centralized updates.
Cons: 5s timeout; availability risk; pin to SHA/tag.

4) Absolute paths (last resort)

- Useful for one machine; not portable across team/CI.

## Globs: Relative vs Absolute (Important)

Relative globs are the safest and most powerful (including recursive `**`).

Absolute-path `instructions` have a limitation:

- Globbing only applies to the basename (final path segment).
- Do not use wildcards in the directory portion.

Works:

- `/Users/you/rules/*.md`

Does not work as intended:

- `/Users/you/rules/**/core/*.md`
- `/Users/you/**/rules/*.md`

If you need recursion (`**`), use repo-relative patterns (submodule/vendor) so `**` applies.

## This Repo (node-architecture) Canonical Docs

- Client core: `client/core/*.md`
- Client framework specifics: `client/frameworks/*`
- Server core: `server/core/*`
- Server runtime specifics: `server/runtime/*`

## New Project Bootstrap

1. Add/confirm a thin project `AGENTS.md`.
2. Add `opencode.json` with `instructions` pointing at canonical docs.
3. Validate by starting OpenCode in the repo and confirming expected instructions are present.

## Stale-Prevention Checklist

- [ ] One canonical file per concern
- [ ] `opencode.json` contains pointers only
- [ ] `AGENTS.md` contains repo facts + minimal loader rules
- [ ] Shared rules are referenced via relative paths (preferred) or pinned URLs

## References

- OpenCode Rules: https://opencode.ai/docs/rules/
- OpenCode Config: https://opencode.ai/docs/config/#instructions
