# AI Model, Agent, and Workflow Boundaries

Use this convention when an application calls a language or embedding model, exposes operations to an agent or MCP client, or runs multi-step work on a workflow engine. It adds no new layer: an AI framework sits in the same outer ring as an HTTP framework, and the [controller](./controllers.md), [authorization](./authorization.md), [transaction](./transaction.md), and [configuration](./configuration.md) contracts apply unchanged. It is independent of the selected model provider, agent framework, and workflow engine.

## Where Each Piece Sits

| Piece | Role | Owns | Never owns |
| --- | --- | --- | --- |
| Agent tool, MCP tool | Framework adapter | Model-facing description, shared input/output contracts, actor resolution, one application call | Business rules, authorization, persistence, service selection |
| Agent | Framework-owned outer component | Instructions, the tool set it may call, the injected model | Data access outside its tools |
| Workflow step | Framework adapter for execution | Step input/output contracts, engine control such as suspension, one controller call for business work | Business rules, direct database access, service selection |
| Model gateway | Provider port and its adapter | The model request, structured-output validation, usage reporting, provider error translation | Prompts' business meaning, persistence, authorization |
| Deployable composition root | Composition | Provider, model, storage, and auth selection from validated configuration | Business behavior |

Capability packages and modules contain no agent-framework, workflow-engine, or model-SDK types. The same capability serves HTTP, an agent tool, and a workflow step.

## Choose the Least Autonomous Piece

Choose the smallest combination that meets the operation's needs. These pieces can compose: a fixed workflow can contain model calls or a bounded agent task.

| Order | Piece | Use when |
| --- | --- | --- |
| 1 | Model gateway call inside a service | One prompt in, one validated result out: classify, extract, summarize, embed |
| 2 | Workflow | The application needs an explicit multi-step sequence, branching, or independently managed stages. Select and verify execution/storage support when it must survive restarts, retry, or wait for a person |
| 3 | Agent with tools | The model must choose which operations to call, as in chat or open-ended requests |

Use an agent when model-directed tool selection earns its additional variability. Do not introduce an agent or workflow engine for work a single model gateway call completes. This is our selection policy, not a claim that a framework forbids other combinations.

## Native Execution and Application Ownership

Use the selected framework's supported sequencing, parallelism, branching, retry, suspension, streaming, and agent-loop mechanisms before writing equivalents. AI tools and workflow business steps enter application code through framework-neutral controllers. Services/use cases behind those controllers own business decisions, authorization, idempotency, and atomic changes; framework adapters translate operation outcomes into engine control flow. A control-only step may map values or suspend without inventing a controller or service.

An application run record is not a second workflow scheduler. Keep authoritative business progress, decisions, and results in application records; let the engine own execution position, technical counters, retry bookkeeping, and recovery snapshots. Adapters and operator tooling may inspect engine state for execution, diagnosis, and reconciliation. Business services and product screens do not use snapshot payloads as their business database.

Workflow definition, durable storage, reliable dispatch, and crash recovery are separate concerns. Verify what the selected runner persists, when it checkpoints, and how interrupted work is restarted. A stored snapshot or a shared run id alone does not guarantee automatic recovery or exactly-once effects. Start dispatch and business-to-external-effect handoffs follow the existing [outbox contract](./async-jobs-outbox.md); do not build a second engine-level retry queue.

## Agent Tools Are Adapters

```text
agent tool / MCP tool
  -> resolve actor from trusted context
  -> injected controller factory
    -> framework-neutral controller
      -> one service or one use case
        -> repository / provider port
```

- A tool that exposes the same operation as the public API reuses that operation's controller and shared contract. Do not write a second implementation for the model to call.
- A tool receives narrow ports, such as a controller factory bound to an actor and a logger. It never receives a container, a database handle, or the environment, and never looks up services through a builder.
- Resolve the actor only from the context the authenticated transport established. Tool arguments, model output, and client-writable context are not identity. An agent is one more caller: ownership, tenant, and permission rules stay in the service or use case, so they hold for every transport.
- Validate the tool result against its output contract and return only the public error code and message. Provider and framework errors, including nested causes, must not reach the model or the client.
- Preserve native schema validation and normalize both returned and thrown failure outcomes at the adapter. If a write commits before output validation or delivery fails, a repeated call must recover the same operation result through application idempotency. Invalid output is not evidence that the write never happened.
- Tool descriptions are part of the contract a model reads. State preconditions the operation enforces, such as optimistic-concurrency versions, rather than relying on the model to guess.

## Schema Ownership and Validation

In TypeScript implementations, apply the [Zod-first contract standard](./api-contracts-zod-first.md) to AI boundaries as well as HTTP boundaries. Zod defines executable data contracts; it is not a separate application layer. Infer TypeScript types from the owning schemas rather than maintaining duplicate interfaces for the same values.

| Boundary | Schema owner | Validation responsibility |
| --- | --- | --- |
| Public operation invoked by HTTP, an agent tool, or MCP | Module-owned shared input/response contracts | Each transport adapter validates input and output using the same contracts; the controller maps typed values to/from application commands and results |
| Structured model output | The application module that owns the prompt and consumes the result | The model gateway validates against the caller's schema before returning an accepted value; the owning service then applies business rules |
| Internal workflow input/output or resume payload | Application-owned internal operation contracts; engine-specific wrappers belong to the workflow adapter | The step/resume boundary validates serialized values, including run and scope identifiers, before invoking the application operation |
| Embedding result | Application-owned model gateway result contract | The gateway adapter checks vector shape, finite values, and expected dimensions; application policy checks model/version compatibility before comparison |
| Database write | Repository adapter's private persistence representation | The repository maps application values to rows; database constraints enforce uniqueness and integrity under concurrency |

Only schemas that actually cross a client/server boundary belong in shared wire contracts. Keep internal model-output and workflow schemas with their owning server modules unless another runtime must consume them. Workflow and model adapters import these contracts; application modules never import their schemas from Mastra or an SDK integration folder. Shared contracts must not derive from ORM tables or import generated database types.

Centralized validation means one canonical definition per semantic contract, reused across tools, workflows, agent output handling, and HTTP where applicable. It does not require a single global schema file. Internal controller contracts can remain server-only; using a controller does not make an operation public.

Validate at trust and serialization boundaries, not mechanically at every method call. A controller/service can accept already validated inferred values. Native SDK/framework validation may fulfill the boundary when it demonstrably applies the application-owned schema; do not run a second identical parse just to satisfy a wrapper. Provider-side output guidance alone is not validation. Distinguish validated results from partial output, fallback values, and rejected output; never silently accept an unvalidated fallback. Schema-valid output does not establish factual accuracy, authorization, source provenance, or semantic identity. Those decisions remain with the application. Translate validation failures through the boundary's error/result policy; do not expose raw provider output or internal validation details to clients or models.

## Model Calls Go Through a Model Gateway

Application code depends on an application-owned model gateway, not on a model SDK. A deployable has one model gateway port, shared like the logger, and one adapter per provider for these application calls. Each module owns what it asks: its prompts, output schemas, and choice of model, which it passes to the gateway. Provider mechanics stay in adapters; business meaning stays with the module that understands it.

- The gateway exposes the few call shapes the application needs, such as structured generation and embedding, with application-owned inputs and results.
- Model output is untrusted input. Request structured output against the caller's schema and validate it. A rejected output is a normal result the caller can record, not a thrown-away failure.
- Report token usage, provider request identity, and whether usage is known, so cost can be recorded and settled by the owning service.
- Select the provider, credentials, and retry policy at composition from validated application configuration. A module names the model it wants; it never reads model credentials or constructs a provider.
- A model call is an external effect: it never participates in a database transaction, and a retry may repeat it. Reserve and settle budgets, and write results, through the owning service's atomic operations.
- Tests substitute the gateway or the injected model. They do not reach the network.

The gateway is the port for application-owned model calls in services and use cases. A framework-owned agent loop may use the framework's supported model routing or an injected model selected at composition. Keep its loop, tool execution, memory, and streaming native rather than rebuilding them inside the gateway. This is an explicit outer-layer integration path: validate configuration at composition, preserve application-owned output contracts, enforce tool access, and capture usage for both paths. It does not permit services to import model SDKs or bypass the gateway.

## Workflow Steps Call Application Operations

A workflow engine sequences, retries, and suspends work. The operation each step performs belongs to a service or use case.

- A step performing business work calls one framework-neutral controller. Reuse the existing capability controller when the operation is the same; otherwise define an internal operation controller with its own application-owned contract. The controller calls one use case or service. This is the stricter AI-adapter rule recorded in [ADR 0009](../../docs/adr/0009-route-ai-adapters-through-controllers.md); the general direct-call allowance for non-AI internal workers does not apply here. A step never queries the database, selects services, or constructs repositories.
- **Persisted scope.** Every workflow input names its organization or other access scope explicitly, and each step rebuilds its dependencies from that persisted scope. A step may run in another process, after a restart, or days later; it cannot depend on a live request, a session, or the user's currently selected organization. A missing or malformed scope fails input validation, and there is no default.
- **Execution identity.** A step has no session. Its adapter builds the actor from the persisted scope: a system execution principal acting for the recorded initiator, or for the scheduled capability that owns a run nobody requested. It is never a replayed session, token, or the engine's own identity. Each business step's operation re-authorizes that initiator against current access rules, so revoked access ends the run with its own terminal outcome instead of finishing on permission that held only at start.
- **Step granularity.** A step is one retry unit. Split work wherever a failure should not repeat earlier paid or external calls. Per-item work that calls a model or provider runs through the engine's iteration with bounded concurrency, one item per business step, not as a loop inside one use case. Run cheap deterministic checks before paid model calls.
- **Application run record.** Business progress, candidates, decisions, and results live in the application's own records. Engine state and snapshots own execution/recovery bookkeeping and may support operator diagnostics; they are not the source of truth for business state. The engine's run id authorizes nothing.
- **Run identity.** When anyone must find a run again, because it suspends, is resumed, or shows progress to a user, create an application run record and use its identity as the engine's run identity, so every caller resumes by an id it already holds. A fire-and-forget run needs no run record; store the engine's run id beside the affected records for diagnostics only.
- **Idempotent steps.** A step may run more than once and a workflow may be started twice. Make each operation safe to repeat through the application's own state and guarded writes, and report whether a repeated commit wrote anything.
- **Failure ownership.** Record an attempt failure without marking the business run terminal while native retries remain. Translate exhausted failure, cancellation, suspension, and completion into guarded application transitions. Keep required business writes in reliable operations, not solely in best-effort lifecycle hooks. Reconcile interrupted/stale runs because a process death may bypass both catches and callbacks.
- **Review suspension.** When a run needs a person, a dedicated step suspends with the minimum data needed to find the run and declares the contract for the resuming decision. Resuming is a protected application operation: authorize the actor against the run's scope before handing the decision to the engine, whether it arrives from the UI, an agent, or an expiry job.
- Step input and output contracts carry identifiers and small values. Large or sensitive material belongs in application records, not engine snapshots.

Engine storage is infrastructure. Give it its own schema and credentials, select it at composition, and do not rely on in-memory storage for suspended or long-running work. Storage separation does not require a different database server; enforce ownership and access boundaries on the selected deployment.

## Memory, Retrieval, and Quality

Conversation memory supplies context, not authoritative permissions or business records. Use native memory only when the feature needs continuity; derive its resource/thread scope from authenticated application identity. Retrieved documents and source content are untrusted evidence. Provider/vector adapters may use native retrieval facilities behind application-owned ports, while services decide which sources are allowed and whether similarity is sufficient for a business decision.

Use native tracing and evaluation facilities where supported. Connect framework traces to the [application observability boundary](./observability.md), redact captured content, and record which model/prompt versions produced results. Evaluations measure output quality; deterministic tests still prove authorization, schema failures, idempotency, and persistence. Usage estimates are operational telemetry, not a substitute for an application-owned budget or settlement record. Native guardrails can supplement these checks but never grant permission to an operation.

## Streaming and Sessions

A chat or stream endpoint that the agent framework serves in its own protocol is a framework-owned transport, comparable to a [provider-managed endpoint](./controllers.md#provider-managed-endpoints): keep its wire format, and do not wrap it in the business response envelope. Authentication still runs first, every tool call still reaches protected application operations, and conversation memory is partitioned by the authenticated actor and scope.

## Verification

- Build the agent, tools, and workflows with injected fakes; no database, provider, or network is required to test wiring.
- Test each tool for anonymous access, forged identity in arguments or client context, output-contract violations, and error redaction.
- Test parity: the tool and the HTTP route produce the same result and the same denial for the same actor.
- Test workflows for a second start, a repeated step, a failure mid-run, one failed item in an iterated stage, access revoked between steps, resume by an unauthorized actor, resume after restart, and expiry.
- Before these rules bind a project, prove them on its installed engine version with a small spike: one tool, one workflow with an iterated stage and a suspension, and a process kill mid-run. Record any guarantee the engine cannot meet.
- Test the model gateway adapter for rejected structured output, unknown usage, and provider outage translation.

## Specializations

- [AI SDK](../runtimes/nodejs/libraries/ai-sdk/README.md) for the model gateway and stream protocol.
- [Mastra](../runtimes/nodejs/libraries/mastra/README.md) for agents, tools, MCP servers, and workflows.

[ADR 0008](../../docs/adr/0008-keep-workflow-state-in-application-records.md) records why business state stays out of the workflow engine. [ADR 0009](../../docs/adr/0009-route-ai-adapters-through-controllers.md) records why AI adapters enter through controllers.
