# Mastra concepts and Zod reconciliation

Date: 2026-11-14

- Reviewed the current official Mastra coding/Factory skills and primary conceptual documentation; added the evidence and proposal report under `docs/proposals/`.
- Kept distinct agent/tool/workflow adapter folders and centralized each Zod contract in its owning application module.
- Applied the requested controller boundary to AI tools and workflow business steps, including internal operations. Pure engine control steps remain controller-free.
- Reconciled native execution, agent model routing, schema validation, engine state, retry outcomes, crash recovery, memory/retrieval, tracing and evaluation with our application ownership rules.
- Clarified the model gateway and workflow-step glossary entries and ADR 0008's business-state decision.
- Updated the Daily Brief example, call tree, and affected portable references. Exact vendor API/configuration syntax remains implementation-time work.
- All changes remain uncommitted. External application repositories and installed skills were not modified.

## Validation

- All four skill drift checks and official skill validators pass.
- Local links/anchors in changed Markdown and whitespace checks pass.
- Visual syntax and interaction checks pass across all six views and four candidate outcomes.
- The external Ample working tree remains clean. Application acceptance criteria are documented, not executed.
