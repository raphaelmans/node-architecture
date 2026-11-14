# Mastra Integration Convention

Use when Mastra is installed or explicitly selected for agents, tools, MCP servers, or workflows. Apply [AI boundaries](../../../../core/ai-boundaries.md), [controllers](../../../../core/controllers.md), [Zod-first contracts](../../../../core/api-contracts-zod-first.md), and [authorization](../../../../core/authorization.md). Add the [AI SDK convention](../ai-sdk/README.md) when application services call models through that adapter.

## Applying Mastra's Standard Within Ours

This playbook owns dependency direction, contracts, authorization, and persistence invariants. Mastra's matching official documentation owns supported runtime behavior and configuration. Prefer native facilities inside our boundaries. When the installed version cannot meet a requirement, document the gap and select a supported integration; a wrapper alone cannot supply missing durability or isolation guarantees.

Use the official [Mastra coding skill](https://github.com/mastra-ai/skills/tree/main/skills/mastra) for capability discovery and version-specific implementation. Its native-first approach complements this guide. The separate [Mastra Factory skill](https://github.com/mastra-ai/skills/tree/main/skills/mastra-factory) operates Factory deployments and is not required for application architecture.

Our controller boundary, module-owned contracts, shared model gateway, and application business records are deliberate policies. Do not describe them as Mastra requirements. Vendor examples demonstrate supported mechanisms; direct database access or environment reads in a quickstart do not override our ownership rules.

## Ownership and Layout

| Concern | Owner |
| --- | --- |
| Agent instructions, tool selection, model-directed loop | Agent adapter |
| Application tool exposure, contract binding, actor mapping | Tool adapter |
| Step order, branching, parallelism, retry and suspension | Workflow adapter/runtime |
| Public and internal operation contracts, model output schemas | Owning application module |
| Operation mapping | Framework-neutral capability controller |
| Business orchestration, authorization, idempotency, atomicity | Use cases and services |
| Database access | Repositories behind services |
| Engine execution state, snapshots, conversation memory | Framework infrastructure |
| Business run progress, decisions and results | Application records |
| Provider selection, auth, model configuration, dependency factories | Deployable composition |

Keep distinct agent, tool, and workflow folders within the Mastra adapter surface. This is our logical layout; verify the selected version's entrypoint/discovery rules rather than treating example filenames as required APIs.

```text
src/
  mastra/                         framework/composition boundary
    agents/                       native agent definitions and tool sets
    tools/                        application tool adapters
    workflows/                    workflow definitions and thin step adapters
    composition/                  wiring from validated configuration
    <registration entrypoint>     the file the installed version discovers; it only
                                  exports the instance built by composition
  lib/modules/<module>/
    shared/contracts/             canonical client/server wire Zod contracts
    schemas/                      server-only operation and generated-output schemas
    controllers/                  one framework-neutral operation boundary
    use-cases/                    orchestration across services
    services/                     business rules and provider-port calls
    repositories/                 database access
    factories/                    construct the inward dependency graph
```

In a monorepo, keep `mastra/` in its deployable and activate contract/capability/adapter packages only at actual package boundaries. Do not force the single-project filesystem tree into every topology.

Centralized validation means **one definition per contract**, owned by its module and imported by consumers. It does not mean every schema belongs in one global file or in `mastra/schemas`. Public wire contracts are browser-safe. Internal generation and step contracts remain server-only unless another runtime needs them. Application schemas import neither Mastra nor ORM tables.

## Agents, Tools, and Controllers

Use a direct model gateway call for a simple application generation task, a workflow for explicit multi-step control flow, and an agent for model-directed tool selection. These pieces can compose. Keep the framework's agent loop, memory, streaming, and supported model routing native; do not rebuild the loop inside a text-generation gateway.

For application business work, use these call paths:

```text
agent -> tool adapter -> controller -> use case OR service -> repository/provider port
workflow business step -> controller -> use case OR service -> repository/provider port
HTTP/RPC adapter -> same capability controller
```

Repositories are reached through services; controllers never query them. A use case coordinates services when needed. An internal workflow operation may have its own controller and server-only input/output contract without becoming an HTTP endpoint. Pure mapping, branching, and suspension need no controller because they perform no business operation. Non-AI internal workers retain the separate rule in the core controller guide.

A tool group and workflow factory receive narrow controller factories, an actor/scope resolver, and required infrastructure ports. They do not receive a service locator or select services. Resolve the actor from authenticated context and authorize the resource in the application operation. A step has no session: bind its controller to the [execution identity](../../../../core/ai-boundaries.md#workflow-steps-call-application-operations) rebuilt from the stored run scope, never to the user's current navigation state or to Mastra's request context. The operation re-authorizes the run's initiator on every business step.

Use a thin application tool helper to bind contracts, identity, logging and public error translation while preserving native execution context and validation. Normalize returned and thrown failures for the installed version. Never expose raw provider output or internal cause chains.

A committed write can be followed by failed output validation or response delivery. Keep strict output contracts and recover the same result on retry through application idempotency. Do not assume a failed tool response means no effect occurred.

Mastra supports agents/tools composed as workflow steps. Use that facility only when the application operation still enters its controller with the same contracts and scope. Prefer a direct step-to-controller adapter when the tool wrapper adds no useful behavior. Framework-owned memory/retrieval utility tools need no artificial business controller, but may not bypass application data access or authorization.

## Composition, Authentication, and Context

Build the Mastra instance from validated configuration, narrow application factories, an actor resolver, and logging/telemetry adapters. Native model routing or a supported injected model is selected at composition. Credentials remain deployable-owned. Application services still call the model gateway; framework agent execution is an explicit outer-layer path. Capture usage on both paths without double-counting.

Do not read environment variables or open connections while defining agents, tools, or workflows. Tests compose fakes through the same ports.

Use native authentication, resource/thread restrictions, and Studio access controls where supported, backed by the application's identity system. These complement capability authorization. Audit direct workflow start/resume, MCP, and automatically exposed workflow tools as well as custom routes. Keep a native route internal or use a protected application operation when native controls cannot enforce our run-creation and access rules.

Translate verified request context into plain application inputs. Framework context and client-writable values are not authorization. Explicitly bridge authenticated MCP identity; do not assume HTTP context propagation secures another transport.

## Zod and Structured Output

Bind tools, steps and resume inputs to application-owned Zod contracts. Match adjacent step inputs/outputs explicitly; use native data mapping when they differ. Reuse a schema across adapters only when the semantic contract is identical, and infer types rather than hand-copying shapes.

A service owns its prompt and structured-output schema. The gateway or agent-result adapter ensures native validation actually applies that schema. Native validation can fulfill the boundary; no second identical parse is needed. Partial values, fallback values, and rejected output must not silently become accepted business data. Zod proves structure, while services decide authorization, provenance, and duplicate identity.

Mastra supports schema alternatives; Zod remains our TypeScript standard. Derive any provider-compatible schema projection from the canonical contract and enforce application checks that the provider cannot represent. Never maintain an independent provider copy of the contract.

## Workflow Execution and Business State

The [core workflow rules](../../../../core/ai-boundaries.md#workflow-steps-call-application-operations) and [ADR 0008](../../../../../docs/adr/0008-keep-workflow-state-in-application-records.md) apply unchanged. This section only maps them onto Mastra.

- **Control flow.** Use native sequencing, parallelism, branches, mapping, loops, bounded retries, and suspend/resume. Each business step invokes one controller; multi-service coordination stays in its use case.
- **Iteration.** Run per-item work that calls a model or provider through native iteration with bounded concurrency, one item per business step. One failed item then retries alone instead of replaying the whole collection.
- **State.** Native workflow state carries execution counters and intermediate references. Snapshots serve recovery and operator diagnosis. Neither is read by product screens or business services.
- **Run identity.** Create the application run first for tracked or resumable work and pass its identity as the engine run identity. Keep authorization and idempotency checks on start, retry, replay, and resume.
- **Durability.** Snapshot persistence, dispatch reliability, and automatic crash recovery are separate capabilities of the selected storage and runner. Verify each one; do not infer recovery from a stored snapshot. Keep engine storage under its own schema and credentials.
- **Failure.** Native retries cover transient execution failures. Record attempts without marking the business run terminal, and do not put required business writes solely in lifecycle callbacks.
- **Human decisions.** Declare suspend and resume contracts, keep the suspend payload minimal, and authorize the decision through a controller before invoking native resume.

## Memory, Retrieval, Observability, and Evaluation

- Use native conversation memory only when the feature needs continuity. Derive resource/thread scope from authenticated identity and apply retention policy. Memory is not a permission grant or the authority for business facts.
- Native document processing and vector retrieval can implement application ports. Services own source access, provenance, and duplicate decisions. Verify maturity and isolation guarantees before adopting new knowledge or memory capabilities.
- Reuse native agent/workflow/tool/model traces and exporters. Bridge them to [application observability](../../../../core/observability.md), redact captured content, and correlate business run ids without using them as trace ids.
- Use supported usage metrics and cost estimates for operations. Verify provider reporting and storage support; application services still own budgets and settlement.
- Use native datasets, scorers, and experiments for output quality where supported. The application owns examples, criteria and thresholds; deterministic tests still prove authorization, idempotency, contract behavior and atomicity.
- Native guardrails/processors supplement validation and business access checks; they do not replace them.

## Chat Route

Framework-owned chat/stream protocols keep their native wire format and stay outside the business response envelope. Register them at composition, align the client protocol with the installed version, authenticate first, and route application tools through controllers.

## Verification and Sources

Before these rules bind a project, run the [adoption spike](../../../../core/ai-boundaries.md#verification) on its installed Mastra version and record any guarantee it cannot meet.

Verify real adapter behavior with fakes behind ports: schema validation including fallback/error outcomes, committed-write response failure, forged identity, HTTP/tool parity, MCP identity, direct start/resume access, and native chat streams. Verify repeated starts/steps, one failed item in an iterated stage, access revoked between steps, retry exhaustion, suspension, cancellation, authorized resume after restart, stale-run reconciliation, and telemetry correlation. Use output-quality evaluations separately from deterministic correctness tests.

- [Official skills](https://github.com/mastra-ai/skills)
- [Agents](https://mastra.ai/docs/agents/overview), [tools](https://mastra.ai/docs/agents/tools), and [structured output](https://mastra.ai/docs/agents/structured-output)
- [Workflows](https://mastra.ai/docs/workflows/overview), [control flow](https://mastra.ai/docs/workflows/control-flow), and [agents/tools as steps](https://mastra.ai/docs/workflows/agents-and-tools)
- [Workflow state](https://mastra.ai/docs/workflows/workflow-state), [snapshots](https://mastra.ai/docs/workflows/snapshots), [suspend/resume](https://mastra.ai/docs/workflows/suspend-and-resume), [errors/retries](https://mastra.ai/docs/workflows/error-handling), and [runners](https://mastra.ai/docs/deployment/workflow-runners)
- [Auth](https://mastra.ai/docs/auth/overview), [request context](https://mastra.ai/docs/server/request-context), and [MCP](https://mastra.ai/docs/connections/mcp)
- [Memory](https://mastra.ai/docs/memory/overview), [retrieval](https://mastra.ai/reference/rag/overview), and [guardrails](https://mastra.ai/docs/agents/guardrails)
- [Tracing](https://mastra.ai/docs/observability/tracing/overview), [metrics](https://mastra.ai/docs/observability/metrics/overview), and [evals](https://mastra.ai/docs/evals/overview)

Detect installed versions first. Use their embedded docs/types, then matching official documentation for missing detail. Public examples for a newer release do not override the target version. Exact imports, model identifiers, context keys, validation/error representations, storage configuration, and runner defaults belong to implementation-time verification, not portable architecture rules.
