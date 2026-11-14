# Mastra Integration Convention

Load only when Mastra is present or selected. Read [runtimes](../runtimes.md), [operations](../operations.md), [AI boundaries](../operations/ai-boundaries.md), and [security](../security.md). Add [AI SDK](ai-sdk.md) for application model calls through that adapter.

## Standards and Composition

- Our playbook owns architecture and access policy; matching Mastra documentation owns supported runtime behavior. Prefer native features within our boundaries. Record unsupported guarantees instead of pretending wrappers supply them.
- Keep distinct agent, tool and workflow adapter folders. Centralize each contract once in its owning application module, not in a global framework schema folder. Public Zod wire contracts are shared; internal model/operation schemas are server-only. Infer types and reuse schemas only for identical semantic contracts.
- Compose Mastra from validated model configuration or a supported injected model, narrow controller factories, actor resolution, and logging/telemetry ports. No environment reads or connection creation in definitions. Business modules import neither Mastra nor model SDKs.
- Use workflows for explicit control flow and agents for model-directed actions. They may compose. Keep native agent execution, memory and streaming intact; direct service model calls still use the application gateway.

## Application Boundaries

- Application tools and workflow business steps call one framework-neutral controller. It delegates to a use case or service; repositories remain behind services. Pure engine mapping or suspension requires no controller. Internal controllers do not imply public routes.
- Reuse a capability controller and its contract across HTTP, tools and steps. Inject factories bound to the verified actor, or for steps to the execution identity rebuilt from stored run scope; re-authorize the run's initiator in each business step. Do not resolve services through a builder in adapters.
- Preserve native schema handling and normalize returned/thrown failures into public outcomes. Avoid redundant validation when the native runtime applies the same schema. Reject unvalidated fallback/partial output; keep committed writes repeat-safe if response handling fails.
- Use native auth/resource/thread controls where available over the application's identity system. Explicitly bridge MCP identity and audit native start/resume routes and workflow-as-tool exposure; none may bypass operation authorization or run creation.
- Native tool/agent composition as steps is permitted when it retains these boundaries. Framework-owned utility tools may operate on framework resources, never bypass protected business operations.

## Workflow State and Reliability

- Prefer native sequence/branch/parallel/map/loop/retry/suspension mechanisms. Each business step calls a controller; its use case owns multi-service orchestration. Run per-item model/provider work through native iteration with bounded concurrency so one failed item retries alone.
- Persist run and scope identifiers in step contracts. Request context is adapter data, not a durable permission grant. Engine state can carry execution counters and intermediate references; business authority stays in application records.
- Create the application run before starting tracked/resumable work and share its identity with the engine. Verify checkpoints, storage, dispatch and restart behavior; a shared id is not exactly-once execution.
- Keep engine storage ownership separate from business storage. Use the outbox for committed intent handoffs, not a second workflow scheduler. Retain idempotency during operator replay.
- Record attempts separately from terminal failure. Required business writes cannot rely solely on lifecycle callbacks; reconcile stale runs after crashes. Human decisions enter through an authorized controller before native resume.

## Supporting Capabilities

- Adopt native memory/retrieval only for actual feature needs, with verified scope, retention and isolation. Services own source access and duplicate decisions; context/embeddings are evidence.
- Reuse native tracing, metrics, and exporters with application correlation/redaction. Avoid duplicate spans or usage accounting. Cost estimates are not budget/settlement records.
- Use native datasets, scorers and experiments for output quality where supported. Keep deterministic tests for contracts, authorization, retries and atomicity. Guardrails supplement these controls.
- Keep framework-owned chat/stream protocols native and align the client's installed protocol. Application tool actions still use controllers.

## Verify and Sources

Run the adoption spike from AI boundaries on the installed version before treating these rules as binding. Verify adapter parsing, returned/thrown failure translation, post-commit response failure, actor/scope parity, MCP identity, direct workflow routes, native streams, repeat execution, retry exhaustion, suspension/cancellation, restart/resume and telemetry. Evaluate output quality separately.

- [Official Mastra coding skill](https://github.com/mastra-ai/skills/tree/main/skills/mastra)
- [Agents](https://mastra.ai/docs/agents/overview), [tools](https://mastra.ai/docs/agents/tools), [structured output](https://mastra.ai/docs/agents/structured-output)
- [Workflows](https://mastra.ai/docs/workflows/overview), [control flow](https://mastra.ai/docs/workflows/control-flow), [agents/tools as steps](https://mastra.ai/docs/workflows/agents-and-tools)
- [State](https://mastra.ai/docs/workflows/workflow-state), [snapshots](https://mastra.ai/docs/workflows/snapshots), [errors/retries](https://mastra.ai/docs/workflows/error-handling), [runners](https://mastra.ai/docs/deployment/workflow-runners)
- [Auth](https://mastra.ai/docs/auth/overview), [request context](https://mastra.ai/docs/server/request-context), [MCP](https://mastra.ai/docs/connections/mcp)
- [Memory](https://mastra.ai/docs/memory/overview), [retrieval](https://mastra.ai/reference/rag/overview), [tracing](https://mastra.ai/docs/observability/tracing/overview), [metrics](https://mastra.ai/docs/observability/metrics/overview), [evals](https://mastra.ai/docs/evals/overview)

Use the installed version's embedded docs/types first, then matching primary documentation. Derive exact imports, configuration keys, execution signatures and defaults at implementation time. Load the separate official Factory skill only for operating a Factory deployment. Loading either skill does not authorize installation outside the task scope.
