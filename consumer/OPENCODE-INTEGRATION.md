# OpenCode Integration

The former OpenCode integration depended on a copied `guides/` tree. That distribution path is disabled.

## Project-Local Skill

Place the complete skills at:

```text
.agents/skills/client/
.agents/skills/server/
```

Each directory must include `SKILL.md`, `agents/openai.yaml`, and `references/`. Invoke them as `$client` and `$server` when the active OpenCode version supports Agent Skills.

## Fallback for Environments Without Skill Support

Reference the canonical source repository directly from a small project `AGENTS.md` or `opencode.json`. Keep includes selective and stack-specific; do not recreate the former all-documents bundle.

- Framework-agnostic client rules: `client/core/*.md`
- React additions: `client/frameworks/reactjs/*.md`
- Next.js additions: `client/frameworks/reactjs/metaframeworks/nextjs/*.md`
- Framework-agnostic server rules: `server/core/*.md`
- Runtime and adapter additions: `server/runtime/**/*.md`

The skills are the preferred portable interfaces. Direct document includes remain a compatibility fallback, not a second generated distribution system.
