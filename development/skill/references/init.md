# Development Init

Run for `/development init`, `$development init`, or an explicit request to refresh the architecture reference index. Maintain root `ARCHITECTURE.md` and a minimal agent-entrypoint pointer. The index owns navigation; authoritative references own conventions.

## Discover and Select

1. Resolve the target repository and requested scopes from instructions and workspace evidence. Read the existing index and agent entrypoint.
2. Inspect package manifests, adopted dependencies, existing convention documents and representative source/configuration only far enough to determine applicable engineering concerns. Keep the inventory and findings out of the index.
3. Discover skills through explicit/configured roots and the available catalog. Inspect evidenced paths such as `agents/skills`, `.agents/skills` and `.skillshare/skills`; deduplicate symlinked installations and preserve verified existing link conventions. Do not invent a default installation.
4. Read candidate names/descriptions, then relevant routers. Inspect routing, leaf triggers and referenced prerequisites to establish complete coverage. Read details only when necessary to resolve relevance or prerequisites; do not preload all skills or references.
5. Match guidance to actual or explicitly selected concerns. Installed does not mean relevant; a declared package does not prove use. Include applicable future operations conditionally. Prefer explicit selection, then configured/local guidance, then available global guidance. Report unresolved authority conflicts.

Discovery is open-ended, not a client/server/monorepo allowlist. Read discovered skills as navigation evidence; do not execute their workflows. Init does not install skills or dependencies, configure startup, scaffold applications or author convention documents.

## Maintain the Lightweight Entry Point

Update the existing repository agent instruction file with a short purpose and link to `ARCHITECTURE.md` for architecture, implementation, review and local-development tasks. Unrelated tasks can skip it. If no entrypoint exists, create root `AGENTS.md` containing only that pointer. Preserve unrelated instructions and reuse equivalent existing text; do not edit ancestor instruction files outside the repository or create competing entrypoints. Resolve ambiguous scope ownership before editing.

## Build the Sectioned Index

Use a short purpose statement, optional section navigation and headings grouped by applicable engineering concern. Established names such as Client, Server, Monorepo and Development are acceptable when they fit the repository; they are not a mandatory template.

Within each concern:

- Link relevant skill routers and require reading each applicable `SKILL.md` once for the task before selected references. Do not require all routers upfront.
- Link directly to the precise authoritative file or stable section for each convention area.
- Give each reference a clear task trigger and linked additional prerequisites, including parent slices, cross-concern requirements, conditional dependencies and reading order.
- Link existing project-owned convention documents directly when no skill router owns them.

A compact table of Reference / Load when / Also read works well. A package qualifier belongs in a trigger only when it helps selection. Derive prerequisites from the installed sources; do not infer them from names alone. Follow prerequisite chains until all required guidance is covered, without loading unrelated siblings. The router remains authoritative when an index entry is stale.

Do not include rule summaries, examples, package inventories, implementation/configuration details, gap reports, research history or creation instructions in the index. Keep findings in the completion report. No separate analysis artifact is needed.

## Missing Authority and Refresh

Verify indexed local files and anchors. Use repository-relative links; deduplicate symlink aliases without rewriting valid links needlessly. For global-only skills, report invocation-only availability unless a stable, verified portable reference exists; never invent local links or embed machine-specific absolute paths.

Report missing skills, references, prerequisites or undocumented project conventions rather than authoring replacements. Continue independent, verifiable indexing and do not claim complete coverage while a required target is missing. For an empty repository, index only explicitly selected available guidance without inventing stack adoption.

Preserve human decisions, unrelated content and unselected scopes. If the old index contains unique rules without an authoritative owner, retain them and report incomplete cleanup; do not silently delete, duplicate or relocate them. Convention authoring/migration is a separate task.

Reconcile headings and triggers, remove duplicates and confirmed stale entries, and keep repeated runs stable. A partial scan is not evidence that an unvisited entry is obsolete. Serialize writes and reread before merging. No timestamp-only churn.

## Validate Task Coverage

Check links/anchors, the minimal pointer, navigation-only content and preserved scopes. Then trace representative tasks through the entrypoint, index, applicable router and references. Include a narrow task, a cross-concern task and both sides of a conditional prerequisite where the repository supports them. Derive expected selections from installed guidance and verify that no applicable prerequisite is missed and no unrelated material is required. This is a navigation check, not execution of those tasks.

For example, in an applicable stack, test UI variants, URL-state ownership and build caching. Do not hardcode those technologies or slice names into the general routing policy.

Report the index and pointer files, indexed concerns, validation and missing authoritative guidance. Do not run application builds or start servers for index initialization.

## Derivation Sources

Derived from the development architecture reference index initialization contract. This installed reference is self-contained; source paths are provenance only.
