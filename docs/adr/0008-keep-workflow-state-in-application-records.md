---
status: accepted
---

# Keep workflow state in application records

A workflow engine such as Mastra can persist execution snapshots, and it is tempting to treat those snapshots as the business record of what happened. We instead keep business progress, candidates, decisions, and results in the application's own records, use the application record's identity as the engine's run identity, and let the engine own execution and recovery state. This costs an application run record for tracked work and explicit idempotency, and buys business state that is queryable, authorized, and migrated like any other data. Engine replacement still needs a plan for in-flight runs and snapshots, but the business record does not depend on their format.

## Consequences

- Every workflow input names its organization or access scope, and each step rebuilds its dependencies from that persisted scope rather than from a live request.
- A run that suspends, is resumed, or shows progress has an application run record whose identity is the engine's run identity. A fire-and-forget run needs none.
- The engine's run id authorizes nothing. Resuming a suspended run is a protected application operation.
- Engine storage is infrastructure with its own schema and credentials, never read by application code for business state.
- Engine-native state, retry bookkeeping, and snapshots remain available to framework adapters and operator diagnostics. Application records do not replace the workflow scheduler.
- Snapshot persistence and restart guarantees depend on the configured runner and storage; shared identity alone does not provide exactly-once execution.
