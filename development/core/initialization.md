# Architecture Reference Index Initialization

`/development init` (also `$development init`) creates or refreshes root `ARCHITECTURE.md` as a sectioned reference index and maintains a lightweight agent entry point. Its purpose is to make applicable engineering conventions discoverable without loading unrelated guidance or copying authoritative rules.

## Scope and Authority

Initialization owns navigation: the index and its minimal instruction-file pointer. It does not author conventions, scaffold code, install skills or dependencies, migrate applications, configure startup, or execute workflows from discovered skills. Read those skills to determine applicability and prerequisites, not as commands to run their setup flows.

Resolve the target repository root from the user's target, instructions and workspace evidence. A package-local working directory does not imply a separate artifact root. Honor a requested application/package scope while retaining one root index and preserving unselected entries. Ask only when the target or conflicting instructions cannot be resolved from evidence.

Each convention stays in one authoritative location: an installed skill reference or an existing project-owned convention document. `ARCHITECTURE.md` owns navigation only. Missing authority is a finding to report, not permission to invent a rule or create a new convention document.

## Discover Relevant Guidance

Inspect existing agent instructions, the index, project convention documents, workspace manifests, declared dependencies and representative configuration/source usage. Use packages and adopted tools to establish applicability; do not turn discovery into a comprehensive implementation audit. A dependency declaration alone does not prove adoption.

Discover installed skills from explicit paths, configured repository roots and the current environment's skill catalog. Check evidenced local locations such as `agents/skills`, `.agents/skills` and `.skillshare/skills`; resolve symlinks to recognize the same installation. Honor explicit path choices, otherwise preserve an existing verified repository-local link convention. Do not impose a default path that does not exist, scan unrelated home directories, or install missing skills.

Read names and descriptions first, then relevant routers. Follow their routing tables, leaf triggers and prerequisite links far enough to establish complete task coverage. Read detailed references where needed to resolve those relationships; do not preload every installed reference. Selection is open-ended and concern-based, not restricted to client, server and monorepo skill names.

Prefer explicit selection, then the configured/local installation, then available global guidance. Deduplicate the same installed skill reached through symlinks. Report unresolved duplicate-name or authority conflicts without choosing a new convention. Irrelevant installed skills and inactive specializations remain unindexed. Relevant future operations such as scaffolding can still have conditional entries; a missing implementation does not make its established guidance irrelevant.

## Lightweight Entry Point

Find the repository's existing agent instruction entry point. Create or update only a short architecture-navigation pointer there, preserving unrelated instructions. If none exists, create root `AGENTS.md` with the pointer. Do not edit an ancestor instruction file outside the target repository or create competing entry points when an established one already serves the repository.

The pointer states the purpose, directs architecture-sensitive work to `ARCHITECTURE.md`, and permits unrelated tasks to skip it. For example:

```markdown
For architecture, implementation, review or local-development work, read
[ARCHITECTURE.md](ARCHITECTURE.md) and select the guidance relevant to the task.
For unrelated tasks, skip the architecture index.
```

Use a link relative to the actual instruction file. Reuse a semantically equivalent existing pointer instead of appending another. If several entrypoints serve different scopes, preserve that structure and update only the applicable pointer; ask when ownership cannot be determined.

## Sectioned Index

Keep a short purpose statement, section navigation when helpful, and headings for applicable engineering concerns such as frontend, backend, workspace architecture and development. Names may match established skill families when that makes navigation clear; do not force a fixed section list or one section per installed skill.

For each concern, link the relevant skill router and state that it must be read once for that task before its selected references. For project-owned guidance that has no skill router, link its authoritative document directly. Readers do not load all routers upfront.

Use compact rows with a direct reference link, a clear applicability trigger, and any additional prerequisites. Link to the precise file or stable section that owns the detail. List the parent slice for a convention leaf and preserve conditional, cross-slice and cross-skill prerequisites from authoritative routing. Include reading order where it matters. Link prerequisites directly; do not rely on unexplained names or a vague “see related guidance.”

A prerequisite describes required reading, not duplicated architecture rules. The router remains authoritative if routing changes; refresh the index instead of maintaining a competing routing policy. When index and router conflict, consult the router and report the stale index entry.

The index must not contain rule summaries, implementation examples, package inventories, configuration recipes, gap reports, research history or the instructions/prompts used to generate it. A brief package qualifier in an applicability trigger is appropriate when it prevents ambiguity. Keep discovery evidence and unresolved findings in the completion report, not in a new report artifact.

## Links and Missing Guidance

Use repository-relative Markdown links and verify every indexed local document and section anchor. Resolve local symlinks without creating duplicate entries or unnecessarily rewriting valid links. Do not fabricate local links or embed machine-specific absolute paths for globally installed skills; label global invocation-only availability in the completion report. Link a global source only when a stable, verified, portable reference is available.

If a skill, reference, prerequisite or project convention has no usable authoritative target, report the missing coverage. Publish verifiable entries for independent concerns without claiming complete coverage. Do not create replacement conventions or an installation workflow as part of init. An empty repository can index explicitly selected, available guidance with conditional triggers; it must not invent an adopted stack.

If an existing index contains unique rules or decisions, preserve them until their authoritative owner is identified. Link an existing owner when possible; report that index cleanup is incomplete rather than silently deleting or relocating human decisions. Do not duplicate those rules into new index sections. Authoring or relocating convention documents is a separate task.

## Refresh and Validate

Preserve human-authored navigation and unselected scopes. Reconcile equivalent headings, update confirmed stale targets and triggers, remove duplicates, and remove entries only when the inspected scope proves them obsolete. A partial scan does not prove absence. Identical evidence should produce no semantic change or timestamp-only churn. Reread before merging edits and keep artifact writes serialized.

Validate both link integrity and usefulness. Select representative tasks from the detected concerns, including a narrow task, a task crossing concerns, and a task with conditional prerequisites where available. Trace each task from the entry point through the index to the relevant router, references and all applicable prerequisites. Check that the selected guidance is complete and unrelated material is excluded; do not execute the sample tasks.

For a Next.js/Turborepo repository, useful cases include UI variants, URL-state ownership and caching/CI changes. Derive expected routing from the installed sources: do not freeze these example tools or slice names as universal prerequisites. Check both sides of conditional triggers so prerequisites are neither missed nor always loaded unnecessarily.

Verify the pointer and index diff, links/anchors, no duplicated convention content, scope preservation, and representative-task coverage. Report changed files, indexed concerns, verification and missing authority. No application build or development server is required.
