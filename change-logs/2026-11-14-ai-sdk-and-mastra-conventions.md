# AI SDK and Mastra Conventions

Date: 2026-11-14

## Changes

- Added the stack-neutral core guide `server/core/ai-boundaries.md`: agent tools, MCP tools, and workflow steps are framework adapters over the existing controller, service, and use-case flow; model calls go through an application-owned model gateway; workflow steps rebuild dependencies from persisted scope; run state lives in application records.
- Added thin Node.js specializations for the AI SDK (`server/runtimes/nodejs/libraries/ai-sdk/`) and Mastra (`server/runtimes/nodejs/libraries/mastra/`). Both defer version-sensitive syntax to matching official documentation.
- Added three `$server` convention leaves, `operations/ai-boundaries`, `runtimes/ai-sdk`, and `runtimes/mastra`, with router triggers and parent-slice pointers.
- Made the existing Zod-first contract standard explicit at AI boundaries: application-owned output and workflow schemas, shared public wire contracts, embedding validation, private persistence representations, and the separation of structural validation from authorization and duplicate policy.
- Added six glossary terms under "AI and workflows" and recorded ADR 0008, which keeps workflow state in application records instead of the workflow engine.
- Set three rules beyond what the source projects already do consistently: prefer a model gateway call over a workflow and a workflow over an agent; one shared model gateway port per deployable with module-owned prompts, schemas, and model choice; and an application run record, sharing its identity with the engine, whenever a run must be found again.
- Derived from the conventions in two application repositories: the Mastra app in the Turborepo boilerplate (injected controller factory, shared tool helper, auth and MCP bridge) and the campaign and studio workflows in a lead-processing application (model gateway, scoped step dependencies, suspend and resume).

## Not covered

- Follow-up reconciliation now captures conceptual roles for native tracing/cost estimates, memory/retrieval, and evaluation. Concrete implementation mappings, client-side AI SDK UI, and application budget/settlement mechanics remain outside this change.
- The source projects were read, not changed. Where they differ from this guidance (a module-wide controller, a module-local model gateway, direct environment access when composing Mastra), this repository records the intended convention.

## Validation

- Mapped the three new guides in the server source map and refreshed the affected fingerprints; all four drift checks report current.
- Checked local Markdown links and confirmed every external documentation link resolves.
