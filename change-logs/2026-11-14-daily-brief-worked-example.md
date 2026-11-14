# Daily Brief worked example

Date: 2026-11-14

- Captured Ample's personal and target-customer daily brief behavior from a read-only local source inspection, with a commit and source references.
- Added `docs/examples/daily-brief.md` and an interactive method call tree at `assets/daily-brief-call-stack.html`.
- Distinguished observed behavior (title-based deduplication and embeddings after persistence) from the proposed normalize → embed → duplicate decision → accept flow.
- Mapped the product feature to public controllers, internal workflow adapters, application use cases/services, model/search ports, repositories, application run state, and optional delivery through an outbox.
- Added a Zod ownership map and validation call trace for public contracts, internal workflow inputs, news candidates, generated interview/copy output, and embedding results; distinguished the proposed module-owned contracts from the source's Mastra-owned/database-derived schema dependencies.
- Kept this an example under the existing contracts. No external application was modified or run; no changes were committed.

## Validation

- All four skill source-drift checks report current.
- New documentation links resolve; whitespace and visualization JavaScript syntax checks pass.
- HTML previews at desktop and mobile widths render without console messages.
- Ample's working tree remains clean. Application acceptance scenarios are documented, not executed.
