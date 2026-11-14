# AI Model, Agent, and Workflow Boundaries Convention

Load for model calls, agent or MCP tools, and workflow-engine steps. Read the parent [operations](../operations.md) and [security](../security.md). Add [AI SDK](../runtimes/ai-sdk.md) or [Mastra](../runtimes/mastra.md) only when present or selected.

## Apply

- Choose the smallest suitable combination: a gateway call for simple generation, a workflow for explicit multi-step control flow, and an agent for model-directed tools. A workflow may contain a bounded agent task. Verify durability instead of assuming it from a workflow definition.
- Keep framework/SDK types in outer adapters. AI tools and workflow business steps call framework-neutral controllers, which call one use case or service. Repositories remain behind services. Internal operation controllers need not expose HTTP routes or browser-shared contracts. Pure mapping, branching, and suspension need no controller.
- Reuse the same controller and contract when a tool/step exposes an existing capability. Inject narrow controller factories; never select services through a builder or give tools database handles.
- Resolve actors from authenticated context. Model arguments and client-writable context never establish identity or authorization.
- A workflow step has no session. Build its actor from persisted run scope as an execution identity: a system principal acting for the recorded initiator, or for the scheduled capability that owns the run. Re-authorize that initiator in every business step so revoked access ends the run with its own outcome.
- Treat a step as one retry unit. Split work where a failure should not repeat earlier paid or external calls; run per-item model/provider work through native iteration with bounded concurrency, one item per business step. Run cheap deterministic checks before paid model calls.
- Prefer native sequencing, parallelism, retries, suspension, streaming and agent loops. Application services own policy, idempotency and atomic writes. A run record is not a replacement scheduler.
- In TypeScript, centralize each semantic contract in one module-owned Zod schema and infer its types. Public wire schemas are shared; internal operation/generated-output schemas stay with their server modules. Adapters import them, never the reverse; no shared contract derives from ORM tables.
- Validate at trust/serialization boundaries. Native validation may satisfy the boundary if it applies the canonical schema; avoid duplicate parsing of already accepted values. Distinguish partial/fallback/rejected results. Shape validity does not establish facts, permissions, or duplicate identity. Validate embedding shape/dimensions and representation compatibility.
- Preserve strict public output contracts and translate both returned and thrown failures without leaking internal causes. If a write commits before response validation/delivery fails, use operation idempotency to recover the same result on retry.
- Application model calls go through one shared gateway port per deployable; modules own prompts, schemas and model choices. Framework-owned agent loops can use native model routing or supported injected models selected at composition. Do not reimplement the loop inside the gateway or permit SDK imports in services.
- Report known/unknown usage and provider request identity for both model paths without double-counting. Select credentials/retry policy from validated deployable configuration. Model calls remain outside database transactions and may repeat on retry.
- Engine state/snapshots own execution/recovery and diagnostics; application records own business progress, decisions and results. Adapters may inspect engine state for reconciliation. Product screens and services do not use snapshot payloads as business records.
- For tracked/resumable work, create the application run first and use its id for the engine. The id grants no authority and does not ensure exactly-once execution. Explicit fire-and-forget work may retain only diagnostic correlation.
- Verify storage, dispatch, checkpoint and crash-restart behavior independently. Use the application outbox for committed business handoffs, not to duplicate engine retry scheduling.
- Record retry attempts separately from terminal run failure. Keep required business writes in reliable operations rather than solely lifecycle hooks, and reconcile stale runs after crashes.
- Resume human decisions through an authorized controller and declared contract. Native suspension carries minimal identifiers; business decisions remain application records.
- Use native memory/retrieval where appropriate behind access-scoped boundaries. Conversation context is not business authority; retrieval supplies evidence, not a duplicate verdict. Framework utility tools must not bypass application operations.
- Reuse supported tracing and quality-evaluation facilities with application correlation, redaction and module-owned quality criteria. Evals supplement deterministic tests; cost estimates do not replace budgets/settlement.
- Framework-owned chat/stream protocols retain their wire format outside the business envelope. Authentication runs first; application tools still use controllers.

## Verify

Before the rules bind a project, prove them on its installed engine version with a small spike: one tool, one workflow with an iterated stage and a suspension, and a process kill mid-run. Record guarantees the engine cannot meet.

Cover controller parity, forged identity, access revoked between steps, one failed item in an iterated stage, native validation/fallback outcomes, committed-write response failure, direct engine entrypoint access, repeated starts/steps, retries, cancellation, restart/resume, stale-run reconciliation, and provider outage handling. Test application invariants deterministically; evaluate generated-output quality separately.
