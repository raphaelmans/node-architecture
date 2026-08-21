# Server Scaffolding Contract

Use this contract when bootstrapping missing server foundations or adding one complete public capability to an existing server repository. It is runtime- and framework-agnostic; stack-specific guides implement it without replacing its guarantees.

## Contents

- [Scope and commands](#scope-and-commands)
- [Safety contract](#safety-contract)
- [Evidence and preflight](#evidence-and-preflight)
- [Layout selection](#layout-selection)
- [Capability and dependency policy](#capability-and-dependency-policy)
- [Contract and access discovery](#contract-and-access-discovery)
- [Foundation roles](#foundation-roles)
- [Capability roles](#capability-roles)
- [Application boundary selection](#application-boundary-selection)
- [Persistence, transactions, and effects](#persistence-transactions-and-effects)
- [Atomicity, idempotency, and conflicts](#atomicity-idempotency-and-conflicts)
- [Verification and report](#verification-and-report)
- [Runtime specializations](#runtime-specializations)

## Scope and Commands

Scaffolding remains an action of the `$server` architecture router:

```text
$server scaffold foundation
$server scaffold <feature>/<operation>
$server scaffold <feature>/<operation> using canonical layout
```

`foundation` creates only missing cross-capability infrastructure. `<feature>/<operation>` creates one real vertical capability plus only its missing prerequisites. Never create disposable examples.

An unlisted language, runtime, or framework is not unsupported. Apply this contract, inspect the repository, and derive the required specialization from current authoritative resources. Do not initialize an application, install a framework without approval, or convert an arbitrary repository merely to fit a documented example.

A foundation scaffold may proceed when its complete runtime-neutral role set is resolved. A public capability must resolve its complete adapter-to-infrastructure flow before any files are written; never leave inward layers waiting for a future transport or durable adapter.

## Safety Contract

- Complete evidence gathering, preflight, dependency approval, and plan validation before writing.
- Preserve unrelated and uncommitted changes.
- Never overwrite an existing file, including in canonical-layout mode.
- Reuse structurally compatible abstractions even when names differ.
- Do not create parallel controllers, error systems, loggers, envelopes, persistence ports, transaction abstractions, or composition roots merely to match canonical names.
- Do not emit placeholder contracts, unresolved imports, fake persistence, TODO implementations, unknown-access endpoints, generated-file headers, or scaffold manifests.
- Fail closed before affected writes when a capability, dependency, contract, policy, integration boundary, durable adapter, or authoritative source remains unresolved.

Patch a dirty target only when integration is narrow and unambiguous. Otherwise stop and ask for direction.

## Evidence and Preflight

Inspect before proposing installations or edits:

1. Detect the language, runtime, framework/transport, build and dependency managers, installed versions, module/package boundaries, and workspace layout.
2. Locate source roots, aliases/import roots, modules, composition roots, public adapters, tests, migrations, and generated artifacts.
3. Inspect existing contracts, errors, envelopes, logging, observability, actor/session boundaries, persistence, transactions, effects, analytics, and tests through their public behavior.
4. Discover the requested operation, access policy, input/response contract, domain ownership, reads/writes, persistence needs, transaction boundary, side effects, and failure behavior.
5. Choose one service or one use case as the controller's application boundary.
6. Classify every planned boundary as `reuse`, `create`, `patch`, `blocked`, or `not-needed`.
7. Resolve the narrowest tests, static or compile checks, lint/format checks, and production build.

Use this evidence order:

1. The target repository, dependency locks, configuration, and installed types/source for current state.
2. This repository's core documents for architecture boundaries.
3. Version-matched official language, runtime, framework, and package documentation.
4. Official release notes or source code.
5. Non-primary sources only with explicit user approval.

Retrieve current primary sources whenever a decision depends on dependency compatibility, configuration syntax, runtime/framework APIs, request lifecycle, module format, build behavior, or deployment behavior. If sources are missing or contradictory, block only the affected scaffold before writing.

If several transports exist, ask which should expose the capability. Multiple transports reuse the same controller, application boundary, and shared contract.

## Layout Selection

Default to adaptive placement. Preserve compatible repository paths, names, and runtime/framework idioms while enforcing core boundary ownership and dependency direction.

Canonical layout is stack-relative, not one universal directory tree. When explicitly requested, use the detected stack's documented canonical mapping. For an unlisted stack, derive a role-to-path mapping from repository evidence and authoritative guidance, show it for approval, and only then write.

```text
core role                  -> stack-native location
shared wire contract       -> ...
framework adapter          -> ...
controller                 -> ...
service or use case        -> ...
repository/provider port   -> ...
infrastructure adapter     -> ...
composition root           -> ...
tests                      -> ...
```

Canonical mode changes placement, never overwrite authority. Architectural roles take precedence over exact filenames.

When the resolved placement crosses workspace packages, `$monorepo` owns package creation, manifests, exports, dependency edges, and atomic cross-package coordination. Stop before partial server writes, resolve the topology through `monorepo/core/scaffolding.md`, then resume this contract inside the selected server app/package boundaries. A server-only change contained within existing packages remains owned here.

## Capability and Dependency Policy

Activate capabilities from requested behavior, not package presence:

| Capability | Activation rule |
| --- | --- |
| Runtime wire validation | Serialized input or output crosses a trust boundary |
| Test tooling | A created boundary requires executable verification |
| Operational logging | Server diagnostics have an explicit owner |
| Request/trace context | Correlation must propagate through one execution |
| Outbound transport | An external provider call is required |
| Persistence | The operation promises durable state |
| Framework adapter | A public transport entry point is requested |
| API description or RPC | The selected transport requires it |
| Product analytics | The capability owns a meaningful behavioral event |

Core does not prescribe packages, runtime primitives, or frameworks. Resolve each activated capability as follows:

1. Reuse a compatible capability already present.
2. Apply a documented specialization for the detected stack when available.
3. Otherwise retrieve current authoritative ecosystem guidance and derive the integration.
4. Resolve exact versions compatible with the installed graph.
5. Show the smallest exact install command, explain each dependency, and request approval.
6. Install only after approval and verify the resulting graph.

Never replace required validation with unchecked DTOs, durable persistence with production in-memory storage, framework integration with unresolved imports, or tests with unexecuted placeholders.

## Contract and Access Discovery

Use the first trustworthy contract source:

1. Existing shared runtime-validated wire contract.
2. Existing typed RPC procedure contract.
3. Generated or authoritative API specification.
4. Existing handler/adapter request and response schema.
5. User-provided fields and behavior.

Reuse compatible partial pieces, but ask for missing behavior. Never derive a public response from a persistence entity. Normalize malformed input to the core validation error contract; expose only sanitized public details and keep internal diagnostics private.

Resolve access explicitly:

- `public`: no actor required;
- `authenticated`: a verified actor/session is required;
- `authorized`: authentication plus capability, ownership, tenant, or domain policy is required;
- `system`: a trusted job, webhook, service, or internal caller policy applies.

Transport adapters own request/session extraction, authentication, cookies, headers, rate limiting, request observability, and transport-wide coarse gates. They pass narrow plain actor/application values inward.

Services or use cases own capability authorization: ownership, tenant membership, domain roles, target-resource lookup, and operation-specific permission invariants. Apply this test:

```text
if the rule must remain true through HTTP, a worker, a CLI, or another transport:
  enforce it in the service or use case
else if the rule exists only to admit or shape one transport request:
  enforce it in the framework adapter
```

Never pre-fetch domain resources or implement capability policy in a transport adapter. Every alternate transport must call the same protected application boundary.

## Foundation Roles

Create only missing roles:

```text
application errors       typed expected failures + safe public details
operational logging      stable application-facing port
response contracts       compatible success/error envelopes when used
execution observability  runtime-neutral request/trace correlation contract
transport mapping        centralized error/envelope integration
composition root         application-scoped construction and wiring
tests                    verify every created public boundary
```

Do not add persistence, transactions, authentication, analytics, outbox, or provider abstractions to a foundation-only scaffold unless the requested foundation actually activates them. Inject narrow ports and configuration, never a generic dependency container or transport context.

## Capability Roles

Every public capability preserves:

```text
framework adapter
  -> framework-neutral controller
    -> one service OR one use case
      -> repository/provider port
        -> infrastructure adapter
```

The framework adapter owns framework request/context types, input parsing, transport gates, request observability, response status/envelope, and centralized error integration. It calls a controller factory or equivalent composition-root entry point only.

The controller accepts the shared input plus narrow plain actor/application values, maps them to an internal command, calls exactly one application boundary, and maps the internal result to the shared response. It imports no framework request/response types and receives no generic request, trace, transaction, or dependency context.

Preserve existing compatible envelope and pagination contracts. Never double-wrap responses.

## Application Boundary Selection

Choose a service for one-domain behavior and a self-contained read or write. Choose a use case only for multi-service orchestration, cross-service transactions, outbox coordination, or post-commit effects.

```text
one domain/repository/provider      -> controller -> service
multiple services/writes/effects   -> controller -> use case -> services
```

Do not create a use case for naming symmetry. Do not let a controller or framework adapter orchestrate services. Resolve ambiguous domain ownership before writing.

## Persistence, Transactions, and Effects

When persistence is required but no durable adapter exists, define the narrow repository port and test fake only as part of an explicitly approved foundation; a production capability remains blocked until durable persistence is resolved. Never imply durable behavior with process-local memory.

Transaction state is opaque and persistence-only. Request IDs, trace IDs, actors, loggers, analytics, and generic metadata never enter transaction options.

Activate transactions only for atomic persistence writes. A service may own a self-contained transaction; a use case owns a transaction spanning services.

Classify effects before generating them:

- durable business effect -> transactional outbox or equivalent durable mechanism;
- operational diagnostic -> application logger, best effort and non-fatal;
- product event -> separate analytics port, best effort unless explicitly durable;
- external effect that cannot safely retry -> after commit or through a durable worker.

Never perform an unsafe external network effect inside a retryable transaction.

## Atomicity, Idempotency, and Conflicts

On every run:

1. Resolve the complete requested boundary set before writing.
2. Compare required capabilities through public contracts, not filenames.
3. Reuse structural equivalents and report naming drift.
4. Create only missing files and patch compatible files narrowly.
5. Stop on incompatible or ambiguous contracts, errors, envelopes, access policy, persistence, transactions, composition, or framework integration.
6. Treat previously scaffolded files as ordinary maintained code, never generator-owned artifacts.

Foundation scaffolding is atomic within its resolved role set. A public capability is atomic across its complete adapter-to-infrastructure flow.

## Verification and Report

Verify every created public boundary:

1. wire-contract input and response behavior;
2. controller mapping and single-boundary delegation;
3. service or use-case behavior, including capability authorization;
4. the actual selected framework adapter, including transport gates;
5. repository/provider behavior when an adapter is generated;
6. type, compile, static-analysis, lint/format, and production build checks appropriate to the stack.

Use real infrastructure only for infrastructure-owned guarantees. Do not mutate unrelated configuration to hide failures; distinguish scaffold-caused failures from pre-existing drift.

Report:

- detected language, runtime/framework, layout mode, dependency/build manager, access policy, and persistence;
- authoritative sources consulted and their version applicability;
- dependencies approved, installed, declined, or blocked;
- roles and files reused, created, patched, blocked, or omitted;
- application-boundary and authorization ownership decisions;
- verification commands and outcomes;
- remaining user actions.

Do not commit a retrieval log or generator manifest.

## Runtime Specializations

- [Node.js scaffolding](../runtime/nodejs/scaffolding.md)

This is a known implementation, not an allowlist. For any other language/runtime/framework, derive a repository-specific implementation using the evidence policy above.
