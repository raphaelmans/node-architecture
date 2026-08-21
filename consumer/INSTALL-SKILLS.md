# Install Architecture Skills

The legacy `guides/` copy workflow is disabled. Client, server, and cross-package workspace architecture are distributed as the `$client`, `$server`, and `$monorepo` skills.

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

```text
Use $skill-installer to install the skill from
https://github.com/raphaelmans/node-architecture/tree/main/monorepo/skill
with the destination name monorepo.
```

The explicit destination names matter because the source folders are named `skill`, while the installed invocations are `$client`, `$server`, and `$monorepo`.

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

.agents/skills/monorepo/
  SKILL.md
  agents/openai.yaml
  references/
```

Copy or vendor the directory only after confirming the destination does not contain local changes. Do not install only `SKILL.md`; the router requires its references.

## Server Scaffolding

Scaffolding remains an action of the installed `$server` router:

```text
$server scaffold foundation
$server scaffold <feature>/<operation>
$server scaffold <feature>/<operation> using canonical layout
```

It applies the generic foundation and capability contract to listed and unlisted runtimes/frameworks. The skill completes repository, authoritative-source, and dependency preflight before writing; documented Node.js adapters are specializations rather than an allowlist, and it does not bootstrap an arbitrary application or framework merely to fit an example.

## Monorepo Scaffolding

Use `$monorepo` when foundation or vertical-slice work creates or changes workspace packages:

```text
$monorepo scaffold foundation
$monorepo scaffold slice <module>/<operation>
```

It owns package creation, manifests, exports, dependency edges, shared task coordination, and atomic cross-package changes. Client/server skills own work inside the resolved packages. Turborepo is the first supported thin specialization; exact behavior is retrieved from official sources matching the target version rather than frozen into the skill.

## Updating

The installer intentionally refuses to overwrite an existing skill. Review local changes, remove or archive the old installed directory deliberately, and reinstall from the desired repository revision.

The source architecture docs remain under `client/core/`, `client/frameworks/`, `server/core/`, `server/runtime/`, `monorepo/core/`, and `monorepo/build-systems/`. Installed references are curated derivatives and are checked for source drift in this repository.

Standalone HTML companions and historical guides are not bundled into the skills. They remain available in the source repository.
