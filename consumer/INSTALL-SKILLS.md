# Install Architecture Skills

The legacy `guides/` copy workflow is disabled. Client and server architecture are distributed as the `$client` and `$server` skills.

## Codex Installation

Ask the built-in skill installer:

```text
Use $skill-installer to install the skill from
https://github.com/raphaelmans/node-architecture/tree/main/client/skill
with the destination name client.
```

```text
Use $skill-installer to install the skill from
https://github.com/raphaelmans/node-architecture/tree/main/server/skill
with the destination name server.
```

The explicit destination names matter because both source folders are named `skill`, while the installed invocations are `$client` and `$server`.

The installer places the package under the active Codex skills directory. The skill becomes available on the next turn.

## Repository-Local Installation

For tools that discover project skills under `.agents/skills/`, place the complete source directory at:

```text
.agents/skills/client/
  SKILL.md
  agents/openai.yaml
  references/

.agents/skills/server/
  SKILL.md
  agents/openai.yaml
  references/
```

Copy or vendor the directory only after confirming the destination does not contain local changes. Do not install only `SKILL.md`; the router requires its references.

## Updating

The installer intentionally refuses to overwrite an existing skill. Review local changes, remove or archive the old installed directory deliberately, and reinstall from the desired repository revision.

The source architecture docs remain under `client/core/`, `client/frameworks/`, `server/core/`, and `server/runtime/`. Installed references are curated derivatives and are checked for source drift in this repository.

Standalone HTML companions and historical guides are not bundled into either skill. They remain available in the source repository.
