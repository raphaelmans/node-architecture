# Initialize the Architecture Reference Index

Run `/development init` (also `$development init`) in the consuming repository.

It maintains two levels of navigation: a minimal pointer in the existing agent instruction file, followed by a sectioned `ARCHITECTURE.md` index. The index points directly to authoritative references with task triggers and prerequisites. Readers load the relevant skill router once for the task, then only the required references.

## What Init Produces

The entry point briefly explains when to consult the index. Init preserves an equivalent existing pointer and unrelated instructions; if no entrypoint exists, it creates root `AGENTS.md` with the pointer.

The index contains a short purpose, navigation where useful, and sections grouped by applicable engineering concerns. Its rows provide direct links, applicability and required related reading. Concern names follow the project; Client, Server, Monorepo and Development are examples, not a fixed template.

Conventions stay in one authoritative location. The index contains no rule summaries, implementation details, package inventories, research history, findings or generation instructions. Repository packages and adopted dependencies help init select relevant guidance; that discovery is not copied into the index.

## How Guidance Is Selected

Init inspects installed skill descriptions, relevant routers, existing project convention documents and package evidence. It follows routing and prerequisite relationships rather than listing every installed skill. Discovery includes configured and evidenced roots such as `agents/skills`, `.agents/skills` and `.skillshare/skills`, including symlinks. Existing verified links are preserved where possible.

For each task, readers load the applicable router once before selected references. The index names and links additional parent, conditional and cross-concern prerequisites. Direct links make references easy to find; they do not bypass the router's common rules.

Missing or broken authoritative references are reported separately. Init does not create new convention documents, install skills, execute discovered workflows or silently turn existing implementation into an architectural rule. Verifiable independent concerns can still be indexed without claiming complete coverage.

## Refresh and Validation

Run the same command when guidance or repository applicability changes. Init preserves unselected scopes and human-authored decisions, updates confirmed stale links and triggers, and avoids duplicate entries or timestamp-only churn. Existing unique rules without an authoritative owner are preserved and reported for separate cleanup.

Validation checks links and section anchors, then traces representative tasks from the entrypoint through the index, router and prerequisites. It checks narrow tasks, tasks crossing concerns and conditional requirements where applicable. Success means finding all relevant guidance without requiring unrelated reading; it does not require executing those engineering tasks.

Canonical contract: [Development Architecture Initialization](../development/core/initialization.md).
