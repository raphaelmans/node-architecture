# Proposal: Mastra within our architecture standard

Status: accepted after review and applied. Date: 2026-11-14.

## Recommendation

Use Mastra's native execution machinery while preserving our application boundaries. Keep agents, tools, and workflows distinct. Define each Zod contract once in its owning application module. Route AI business actions through framework-neutral controllers, then use cases/services, with repositories behind services.

This proposal changes the rulebook and its portable skills. It does not migrate Ample, install new skills, execute workflows, or send email.

## Skills evaluated

Use the official [Mastra coding skill](https://github.com/mastra-ai/skills/tree/main/skills/mastra) alongside our server skill: it supplies version-specific implementation guidance, ours supplies application architecture. The separate [Factory skill](https://github.com/mastra-ai/skills/tree/main/skills/mastra-factory) is only for operating Factory deployments. Older overlapping Mastra skills and community wrappers are not adopted.

## Decisions applied

### 1. Distinct framework folders; application-owned contracts

The [Mastra guide](../../server/runtimes/nodejs/libraries/mastra/README.md#ownership-and-layout) now separates `mastra/agents`, `mastra/tools`, and `mastra/workflows`, with composition wiring outside business modules. The physical tree is our logical layout, adapted to the consuming topology; implementation-time docs determine actual discovery/entrypoint rules.

Canonical Zod contracts live in the owning application's module. Shared request/response schemas remain browser-safe; internal workflow and model-output schemas stay server-only. Tools, steps, HTTP adapters and agent-result handling import the same schema when they consume the same semantic contract. Generated database rows do not define public or model-output contracts.

This preserves a single source of truth without creating one global schema file. Zod validates shape and local constraints. Authorization, provenance, duplicate decisions and atomicity remain application responsibilities. Mastra supports schema systems beyond Zod; choosing Zod is our policy. [Mastra workflow schema concepts](https://mastra.ai/docs/workflows/overview).

### 2. Controllers for AI business entrypoints

Your clarified preference is now explicit: tools and workflow steps performing business work call controllers, including internal operations. A controller calls one use case or service. Services reach repositories/provider ports. Pure engine mapping, branching and suspension require no controller.

An internal controller does not imply a public API endpoint. It may accept a server-only operation contract. Reuse an existing controller when the operation is actually identical rather than create an AI-only business implementation.

[ADR 0009](../adr/0009-route-ai-adapters-through-controllers.md) records the trade-off: internal workers may call use cases directly, AI adapters may not.

Mastra permits steps to call ordinary functions, agents, or tools, and tools may execute custom code. Our boundary is deliberately stricter. Native agent/tool-as-step composition is acceptable only when the business action retains that controller and authorization path. [Native composition](https://mastra.ai/docs/workflows/agents-and-tools), [tools](https://mastra.ai/docs/agents/tools).

### 3. Use native execution instead of building a second framework

Mastra should handle sequencing, branches, parallel stages, iteration, suspension/resumption, and its agent loop. Application services decide domain outcomes; workflow adapters map them into engine control flow. Our run table is not another scheduler.

The earlier selection ladder was too easy to read as mutually exclusive. It now permits a fixed workflow to contain a bounded agent task. Daily Brief remains a fixed workflow because its sequence is known; it does not need an autonomous agent to choose that sequence. [Control flow](https://mastra.ai/docs/workflows/control-flow), [agents](https://mastra.ai/docs/agents/overview).

### 4. Separate business state from engine state

Keep business progress, accepted candidates, approvals, and published results in application records. Allow engine-native state for execution counters and intermediate references, and snapshots for recovery and operator diagnosis. The adapter may inspect native state to reconcile a run; product screens and business services must not treat snapshot payloads as their business database.

This clarifies ADR 0008 rather than abandoning it. There is no need to suppress Mastra state or copy its entire snapshot format into our tables. Persist intermediate application artifacts only when product behavior, audit, recovery or idempotency requires them. [Workflow state](https://mastra.ai/docs/workflows/workflow-state), [snapshots](https://mastra.ai/docs/workflows/snapshots).

### 5. Verify durability and keep retry outcomes honest

A workflow definition, storage persistence, reliable dispatch and restart recovery are different capabilities. Select and test the runner for the consuming deployment; do not promise recovery because a snapshot table exists. Sharing application/engine run identity is useful correlation, not exactly-once execution. [Workflow runners](https://mastra.ai/docs/deployment/workflow-runners).

Use native retries for transient execution failures. Application idempotency protects repeated business effects. Record failed attempts without marking the run terminal while retries remain; handle completion, cancellation, suspension and exhausted failure as distinct application transitions.

Required business writes stay in reliable operations, with stale-run reconciliation for crashes. Mastra's lifecycle callbacks are not a durable delivery mechanism. Our outbox remains for committed business intent handed to workflow dispatch or email delivery, not for rebuilding every engine retry. [Error handling](https://mastra.ai/docs/workflows/error-handling).

### 6. Preserve native model execution and schema validation

Application services still use the shared model gateway. Framework-owned agents may use native model routing or supported injected models configured at composition. Their loop, streaming and memory do not need to be recreated behind a simple generation port. Both paths retain application contracts, validated configuration and usage accounting.

Native schema validation can satisfy our boundary when it applies the canonical schema. Do not duplicate the parser simply for architectural appearance. Distinguish validated output from partial values, rejected output and fallbacks. Provider-compatible schema projections must be derived, not separately maintained. [Structured output](https://mastra.ai/docs/agents/structured-output).

Keep our strict output contract even for mutating tools. If a write commits and output validation fails, make retry recover the same result. Do not infer that a failed tool response means no write occurred, or weaken validation just to discourage retries. [Tool output validation](https://mastra.ai/docs/agents/tools).

### 7. Native access controls complement application authorization

Use Mastra authentication and supported resource/thread restrictions. Derive identity from verified server context and explicitly bridge MCP identity. Audit built-in workflow start/resume, Studio and auto-exposed workflow tools as well as our custom routes. A direct native route must not bypass the application's run creation or access checks.

Mastra request context carries per-call information. It is not a business permission grant or a substitute for persisted run scope. Agents receive only tools appropriate to their authorized operation; broad database handles remain unavailable. [Authentication](https://mastra.ai/docs/auth/overview), [request context](https://mastra.ai/docs/server/request-context).

### 8. Adopt supporting capabilities selectively

The guide now captures their architectural roles, without selecting packages, storage backends, model versions or implementation flags:

- **Memory:** native conversation continuity when needed; authenticated resource/thread scope and application retention policy. No permission authority or replacement business record. [Memory](https://mastra.ai/docs/memory/overview).
- **Retrieval:** native document/vector facilities may implement our ports; the application still owns source access and the decision that two candidates are duplicates. Similarity retrieves evidence. [Retrieval concepts](https://mastra.ai/reference/rag/overview).
- **Tracing and usage:** use native instrumentation/exporters with our correlation and redaction boundaries. Avoid duplicate spans/counting. Estimates support operations; budgets/settlement remain application-owned. [Tracing](https://mastra.ai/docs/observability/tracing/overview), [metrics](https://mastra.ai/docs/observability/metrics/overview).
- **Evaluation:** use supported datasets, scorers and experiments; modules own representative cases and acceptance criteria. Evals supplement deterministic contract, authorization and persistence tests. [Evals](https://mastra.ai/docs/evals/overview).
- **Guardrails:** use native processing where needed, without replacing deterministic validation or capability authorization. [Guardrails](https://mastra.ai/docs/agents/guardrails).

New memory/knowledge/execution features must meet actual version, maturity and isolation requirements before adoption. Discovery alone is not approval to introduce them. This is conceptual coverage, not a claim that these capabilities are configured in Ample.

### 9. Review amendments

A review of the first draft added four rules:

- **Execution identity.** A step has no session. It acts as a system principal for the run's recorded initiator, and each business step re-authorizes that initiator. Revoked access stops the run.
- **Step granularity.** A step is one retry unit. Per-item work with model or provider calls uses native iteration, one item per step, and cheap deterministic checks run before paid calls.
- **No review queue without a review operation.** Every candidate reaches a terminal disposition. Similarity starts in observe mode and is enforced only after a threshold is calibrated.
- **Adoption spike.** Before these rules bind a project, prove them on its installed engine version: one tool, one workflow with an iterated stage and a suspension, and a process kill mid-run.

## Effect on Daily Brief

The [worked example](../examples/daily-brief.md) now places a controller between every business step and its use case. Its Zod section shows which schema owns each boundary. The [call tree](../../assets/daily-brief-call-stack.html) follows the same path.

The product behavior stays as proposed: discover news → per candidate: normalize → exact lookup → embed → similarity → accept → prepare interviews → publish. Optional email remains separate and disabled when requested. Native workflow facilities handle execution; application operations retain the duplicate policies and protected publication.

No migration code is supplied or executed. The remaining implementation choices—runner/storage, source identity, the calibrated similarity threshold, provider versions, and quality thresholds—must be resolved against the consuming application before migration.

## Review map

- [Core AI boundaries](../../server/core/ai-boundaries.md): controller entrypoints, centralized contracts, native execution, business state, validation, model paths and reliability.
- [Controller rule](../../server/core/controllers.md) and [ADR 0009](../adr/0009-route-ai-adapters-through-controllers.md): explicit AI exception to the non-AI internal-worker direct-call allowance.
- [Mastra convention](../../server/runtimes/nodejs/libraries/mastra/README.md): folder roles and native-to-application integration.
- [AI SDK convention](../../server/runtimes/nodejs/libraries/ai-sdk/README.md): native validation and framework model routing without bypassing application ports.
- [Glossary](../../CONTEXT.md) and [ADR 0008](../adr/0008-keep-workflow-state-in-application-records.md): clarified terms and state authority.
- [Portable AI leaf](../../server/skill/references/operations/ai-boundaries.md) and [Mastra leaf](../../server/skill/references/runtimes/mastra.md): synchronized agent instructions.

## Verification

- All four source-drift checks report current after reviewing the affected references and refreshing their fingerprints.
- The official skill validator passes for client, server, monorepo, and development. It ran with PyYAML in an isolated tool environment; no application dependency was added.
- Local links and target anchors pass across 26 changed Markdown files; whitespace and visualization JavaScript syntax checks pass.
- The call-tree preview passes interaction checks for six views and four candidate outcomes, including controller presence and no accepted-story write after embedding failure. The mobile Zod view renders without runtime errors.
- Ample remains clean at the inspected commit. No application, workflow, provider call, migration or email was executed.

API implementation compatibility is intentionally not claimed: this is a documentation proposal, and no target application was built or run. Native integration guarantees remain implementation-time acceptance checks, not something a documentation validator proves.
