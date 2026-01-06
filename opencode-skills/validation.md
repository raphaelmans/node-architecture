# Skill Validation Guide

How to validate OpenCode skills using the `skills-ref` reference implementation.

## Prerequisites

- Python 3.11+
- uv (recommended) or pip

```bash
# Check versions
python3 --version  # 3.11+
uv --version       # any recent version
```

## Setup skills-ref

Clone and install the reference implementation:

```bash
# Clone repo
cd /tmp
git clone --depth 1 https://github.com/agentskills/agentskills.git

# Install with uv
cd agentskills/skills-ref
uv sync
source .venv/bin/activate
```

Or with pip:

```bash
cd /tmp/agentskills/skills-ref
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Validation Commands

### Validate a Single Skill

```bash
skills-ref validate path/to/skill
```

Example:

```bash
skills-ref validate ~/.config/opencode/skill/backend-module
# Output: Valid skill: /Users/you/.config/opencode/skill/backend-module
```

### Validate All Installed Skills

```bash
for skill in ~/.config/opencode/skill/*/; do
  echo "=== Validating: $skill ==="
  skills-ref validate "$skill"
done
```

### Validate Skills in This Repo

```bash
for skill in opencode-skills/*/; do
  if [ -f "$skill/SKILL.md" ]; then
    echo "=== Validating: $skill ==="
    skills-ref validate "$skill"
  fi
done
```

## Reading Skill Properties

Get skill metadata as JSON:

```bash
skills-ref read-properties ~/.config/opencode/skill/backend-module
```

Output:

```json
{
  "name": "backend-module",
  "description": "Create new backend modules with layered architecture..."
}
```

### Read All Skills Properties

```bash
for skill in ~/.config/opencode/skill/*/; do
  skills-ref read-properties "$skill"
done
```

## Generate Prompt XML

Generate the `<available_skills>` XML for agent system prompts:

```bash
skills-ref to-prompt ~/.config/opencode/skill/*/
```

Output:

```xml
<available_skills>
<skill>
<name>backend-module</name>
<description>Create new backend modules...</description>
<location>/Users/you/.config/opencode/skill/backend-module/SKILL.md</location>
</skill>
<!-- ... more skills -->
</available_skills>
```

## Verify OpenCode Can Load Skills

### 1. Check Installed Skills

```bash
ls ~/.config/opencode/skill/
```

### 2. Test in OpenCode

In an OpenCode session, ask the agent to load a skill:

```
Load the backend-module skill
```

Or check if the `skill` tool shows available skills in the system prompt.

### 3. Confirm via skill Tool

The agent should see skills listed in its tool description:

```xml
<available_skills>
  <skill>
    <name>backend-module</name>
    <description>Create new backend modules...</description>
  </skill>
</available_skills>
```

## Common Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `SKILL.md not found` | Missing or misnamed file | Ensure file is `SKILL.md` (uppercase) |
| `Invalid name` | Name doesn't match folder | Name in frontmatter must match folder name |
| `Missing description` | No description field | Add `description:` to frontmatter |
| `Name too long` | Name > 64 chars | Shorten the skill name |
| `Invalid name format` | Invalid characters | Use lowercase alphanumeric with single hyphens |

## Validation Checklist

- [ ] File is named `SKILL.md` (uppercase)
- [ ] Frontmatter has `name` field
- [ ] Frontmatter has `description` field (1-1024 chars)
- [ ] Name matches folder name exactly
- [ ] Name is lowercase alphanumeric with single hyphens
- [ ] Name is 1-64 characters
- [ ] No consecutive hyphens (`--`)
- [ ] No leading/trailing hyphens

## Quick Reference

```bash
# One-liner: clone, install, validate all
cd /tmp && \
  git clone --depth 1 https://github.com/agentskills/agentskills.git && \
  cd agentskills/skills-ref && \
  uv sync && \
  for skill in ~/.config/opencode/skill/*/; do \
    .venv/bin/skills-ref validate "$skill"; \
  done
```

## Resources

- [Agent Skills Specification](https://agentskills.io/specification)
- [Integration Guide](https://agentskills.io/integrate-skills)
- [OpenCode Skills Docs](https://opencode.ai/docs/skills)
- [skills-ref Source](https://github.com/agentskills/agentskills/tree/main/skills-ref)
