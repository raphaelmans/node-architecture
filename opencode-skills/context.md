# OpenCode Skills Context

This document describes how to create and maintain OpenCode skills from the architecture documentation in this repo.

## What Are Skills?

Skills are reusable instructions that OpenCode can load on-demand. They live in `~/.config/opencode/skill/<name>/SKILL.md` and are available globally across all projects.

## Skill Format

Each skill is a folder containing a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: skill-name
description: Short description (1-1024 chars) for agent to choose correctly
---

# Skill Title

Content with step-by-step instructions, code examples, and checklists.
```

### Naming Rules

- Lowercase alphanumeric with hyphens: `backend-module`, `frontend-form`
- No consecutive hyphens, no leading/trailing hyphens
- Must match the folder name

## Current Skills

| Skill | Description |
|-------|-------------|
| `user-stories` | Create user stories from PRD with acceptance criteria, edge cases, and checkpoints |
| `user-story-pdf` | Generate professional PDF documents from user story checkpoints for product teams |
| `agent-plan` | Create implementation plans derived from user stories with API specs, UI mockups, and checklists |
| `agent-context` | Log progress and update agent context files with versioned naming |
| `backend-module` | Create new modules (repository, service, factory, router, DTOs, errors) |
| `backend-feature` | Add endpoints, fields, use cases to existing modules |
| `backend-webhook` | Inbound webhooks with signature verification |
| `backend-supabase-auth` | Supabase Auth with tRPC, user roles, middleware |
| `backend-logging` | Structured logging with Pino, request tracing, business events |
| `frontend-feature` | New features with components, schemas, hooks, pages |
| `frontend-form` | Forms with StandardForm, Zod, react-hook-form |
| `frontend-data` | tRPC queries, mutations, cache invalidation |
| `frontend-state` | nuqs URL state + Zustand stores |
| `nextjs-auth-routing` | Type-safe routes + proxy-based auth guarding in Next.js 16 |

## Source Documentation

Skills are derived from the architecture docs in this repo:

```
/server/
├── core/           # Core patterns (logging, errors, transactions)
├── references/     # Detailed reference docs
└── supabase/       # Supabase-specific patterns

/client/
├── core/           # Core patterns (forms, components)
└── references/     # Detailed reference docs
```

## Creating a New Skill

### 1. Identify the Pattern

Look for new or updated docs in `/server/` or `/client/`. Good candidates:
- New integration (e.g., Stripe, Clerk, Resend)
- New architectural pattern
- Significant updates to existing patterns

### 2. Create the Skill File

```bash
mkdir -p opencode-skills/<skill-name>
```

Write `opencode-skills/<skill-name>/SKILL.md`:

```markdown
---
name: <skill-name>
description: <1-2 sentence description for agent selection>
---

# Title

Use this skill when <trigger conditions>.

## Architecture / Overview

Brief architecture diagram or table.

## Step-by-Step

### 1. First Step

Code examples with context.

### 2. Second Step

More examples...

## Checklist

- [ ] Item 1
- [ ] Item 2
```

### 3. Install to OpenCode

```bash
cp -r opencode-skills/<skill-name> ~/.config/opencode/skill/
```

Or copy all:

```bash
cp -r opencode-skills/* ~/.config/opencode/skill/
```

### 4. Verify

```bash
ls ~/.config/opencode/skill/
```

## Add Skills to Codex

Codex can load custom skills from:

- `~/.codex/skills`
- `~/.config/codex/skills`

In this machine setup, keep canonical copies in `~/.agents/skills` and symlink into `~/.codex/skills`.

### 1. Install one skill to Codex

```bash
mkdir -p ~/.agents/skills/<skill-name>
cp opencode-skills/<skill-name>/SKILL.md ~/.agents/skills/<skill-name>/SKILL.md
ln -s ../../.agents/skills/<skill-name> ~/.codex/skills/<skill-name>
```

### 2. Install migrated skills (`agent-context`, `agent-plan`, `user-stories`)

```bash
mkdir -p ~/.agents/skills/agent-context ~/.agents/skills/agent-plan ~/.agents/skills/user-stories
cp opencode-skills/agent-context/SKILL.md ~/.agents/skills/agent-context/SKILL.md
cp opencode-skills/agent-plan/SKILL.md ~/.agents/skills/agent-plan/SKILL.md
cp opencode-skills/user-stories/SKILL.md ~/.agents/skills/user-stories/SKILL.md
rm -rf ~/.codex/skills/agent-context ~/.codex/skills/agent-plan ~/.codex/skills/user-stories
ln -s ../../.agents/skills/agent-context ~/.codex/skills/agent-context
ln -s ../../.agents/skills/agent-plan ~/.codex/skills/agent-plan
ln -s ../../.agents/skills/user-stories ~/.codex/skills/user-stories
```

### 3. Verify Codex install

```bash
ls -la ~/.codex/skills | rg 'agent-context|agent-plan|user-stories'
ls -la ~/.agents/skills | rg 'agent-context|agent-plan|user-stories'
```

### 4. Restart Codex

Restart Codex after installing or updating skills so the new skill set is loaded.

### 5. Optional: custom skill directories

If you want Codex to load skills from additional paths, configure `custom_skill_directories` in `~/.codex/config.toml`.

## Codex Troubleshooting

- Broken symlink: run `ls -la ~/.codex/skills/<name>` and recreate symlink if target is missing.
- Duplicate folder + symlink with same name: keep one canonical source (`~/.agents/skills` or direct in `~/.codex/skills`), not both.
- Skill not appearing: verify frontmatter has `name` and `description`, then restart Codex.

## Updating Skills

When architecture docs change:

1. Check git diff for modified files in `/server/` or `/client/`
2. Update the corresponding skill in `opencode-skills/`
3. Re-copy to `~/.config/opencode/skill/`

```bash
git diff server/ client/
# Identify changes, update skills
cp -r opencode-skills/* ~/.config/opencode/skill/
```

## Skill Writing Guidelines

### Keep It Actionable

- Start with "Use this skill when..."
- Provide step-by-step instructions
- Include copy-paste code examples
- End with a checklist

### Be Concise

- Skills should be scannable
- Use tables for quick reference
- Code examples should be minimal but complete
- Avoid verbose explanations

### Match the Architecture

- Use the same terminology as the docs
- Follow the same patterns (layered architecture, factories, etc.)
- Reference actual file paths from the project structure

### Description Matters

The `description` field is what the agent sees to decide whether to load a skill. Make it:
- Specific enough to trigger on relevant requests
- Include keywords users might say ("webhook", "form", "auth", "login")

## File Structure

```
/Users/raphaelm/Documents/Coding/node-architecture/
├── opencode-skills/           # Skill source files
│   ├── context.md             # This file
│   ├── backend-module/
│   │   └── SKILL.md
│   ├── backend-feature/
│   │   └── SKILL.md
│   └── ...
├── server/                    # Backend architecture docs
└── client/                    # Frontend architecture docs

~/.config/opencode/skill/      # Installed skills (copy destination)
├── backend-module/
│   └── SKILL.md
└── ...

~/.agents/skills/              # Canonical custom skills (this setup)
├── agent-context/
│   └── SKILL.md
└── ...

~/.codex/skills/               # Codex-discovered skills (symlink target path)
├── agent-context -> ../../.agents/skills/agent-context
└── ...
```

## Quick Commands

```bash
# Create new skill
mkdir -p opencode-skills/<name>
# ... write SKILL.md

# Install all skills
cp -r opencode-skills/* ~/.config/opencode/skill/

# List installed skills
ls ~/.config/opencode/skill/

# Install migrated skills to Codex
mkdir -p ~/.agents/skills/agent-context ~/.agents/skills/agent-plan ~/.agents/skills/user-stories
cp opencode-skills/agent-context/SKILL.md ~/.agents/skills/agent-context/SKILL.md
cp opencode-skills/agent-plan/SKILL.md ~/.agents/skills/agent-plan/SKILL.md
cp opencode-skills/user-stories/SKILL.md ~/.agents/skills/user-stories/SKILL.md
rm -rf ~/.codex/skills/agent-context ~/.codex/skills/agent-plan ~/.codex/skills/user-stories
ln -s ../../.agents/skills/agent-context ~/.codex/skills/agent-context
ln -s ../../.agents/skills/agent-plan ~/.codex/skills/agent-plan
ln -s ../../.agents/skills/user-stories ~/.codex/skills/user-stories

# Verify Codex skill links
ls -la ~/.codex/skills | rg 'agent-context|agent-plan|user-stories'

# Remove a skill
rm -rf ~/.config/opencode/skill/<name>
rm -rf opencode-skills/<name>
```
