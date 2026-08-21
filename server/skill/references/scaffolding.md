# Server Scaffolding Slice

Use this slice when the user invokes `$server scaffold`, asks to bootstrap missing server foundations, or requests one repository-aware vertical capability. It applies to listed and unlisted languages, runtimes, and frameworks. Load the relevant architecture slices and derive stack-specific execution from repository evidence and current primary sources.

## Commands and Scope

```text
$server scaffold foundation
$server scaffold <feature>/<operation>
$server scaffold <feature>/<operation> using canonical layout
```

`foundation` creates only missing cross-capability infrastructure. A vertical capability creates one real adapter-to-infrastructure flow plus only its missing prerequisites. Never generate examples, initialize an arbitrary application, or install a framework merely to match a known specialization.

An unlisted language/runtime/framework is not unsupported. Use the generic contract, inspect repository conventions, retrieve current official resources, and derive the specialization. A runtime-neutral foundation may proceed when its complete role set is resolved. A public capability must resolve its complete transport and durable behavior before any writes.

## Preflight Before Writes

1. Detect language, runtime, framework/transport, dependency/build manager, installed versions, module/package boundaries, workspace, source roots, composition roots, adapters, and tests.
2. Inspect contracts, validation, errors, envelopes, logging, observability, actors/sessions, persistence, transactions, effects, analytics, and tests through public behavior.
3. Discover the operation, explicit access policy, input/response contract, domain ownership, reads/writes, persistence, transaction boundary, side effects, and failure behavior.
4. Select one service or one use case as the controller's application boundary.
5. Classify every required boundary as `reuse`, `create`, `patch`, `blocked`, or `not-needed`.
6. Retrieve current primary sources for version-sensitive dependency, configuration, lifecycle, module-format, build, and deployment decisions.
7. Resolve exact compatible dependencies, show the smallest exact install command and rationale, and ask for approval.
8. Validate the complete plan, install approved dependencies, verify the graph, and only then write.

Evidence priority:

```text
target repository + locks/config/installed types or source
  -> repository core architecture docs
    -> version-matched official documentation
      -> official release notes/source
        -> non-primary sources only with explicit approval
```

Fail closed on missing or contradictory evidence before affected writes. If several transports exist, ask which should expose the capability; reuse one contract, controller, and application boundary across transports. Do not persist a retrieval log or generator manifest.

## Safety and Atomicity

- Preserve unrelated and dirty work.
- Never overwrite, including canonical mode.
- Reuse structural equivalents despite naming differences.
- Do not create parallel controllers, errors, envelopes, loggers, persistence ports, transactions, or composition roots.
- Do not emit placeholder contracts, unresolved imports, fake persistence, TODOs, unknown-access endpoints, generated headers, or scaffold metadata.
- Patch dirty files only when narrow and unambiguous.
- Treat prior scaffolded files as ordinary maintained code.

Foundation scaffolding is atomic within its resolved role set. A public capability is atomic across its complete adapter-to-infrastructure flow; do not write inward layers while a required transport or durable adapter remains unresolved.

## Layout Mode

Default to adaptive placement: preserve compatible repository paths and stack idioms while enforcing architectural roles.

Canonical layout is stack-relative. Use a documented specialization when available. For an unlisted stack, derive and show a role-to-path mapping for approval:

```text
shared wire contract       -> stack-native location
framework adapter          -> stack-native location
controller                 -> stack-native location
service or use case        -> stack-native location
repository/provider port   -> stack-native location
infrastructure adapter     -> stack-native location
composition root           -> stack-native location
tests                      -> stack-native location
```

Canonical mode changes placement, never overwrite authority.

In a workspace, load `workspace`. `$server` owns work inside resolved server app/package boundaries; `$monorepo` owns placement, package creation, manifests, exports, dependency edges, and atomic cross-package changes. Placement resolves explicit scope first, then cohesive existing module ownership, then package defaults for a new monorepo module. Stop before partial server writes when that coordination is required.

## Capability Resolution

Activate only behavior the requested scaffold needs:

| Capability | Activation rule |
| --- | --- |
| Runtime validation | Serialized data crosses a trust boundary |
| Test tooling | A created public boundary needs executable verification |
| Operational logging | Server diagnostics have an explicit owner |
| Request/trace context | Correlation must propagate through an execution |
| Outbound transport | An external provider call exists |
| Persistence | The operation promises durable state |
| Framework adapter | A public entry point is requested |
| API description/RPC | The selected transport requires it |
| Product analytics | A meaningful capability-owned behavioral event exists |

Do not choose packages or primitives in the generic slice. Reuse compatible repository capabilities first, then a documented stack specialization, then current official ecosystem guidance. Resolve exact versions and obtain dependency approval. Never replace required validation with unchecked data, durable persistence with production memory, or tests with placeholders.

## Contract and Access Discovery

Use the first trustworthy contract source:

1. Existing shared runtime-validated wire contract.
2. Existing typed RPC contract.
3. Generated or authoritative API specification.
4. Existing handler/adapter schema.
5. User-provided fields and behavior.

Ask for missing behavior and never infer a public response from a persistence entity. Normalize malformed input to the repository's validation error and expose only sanitized public details.

Require one explicit access policy: `public`, `authenticated`, `authorized`, or `system`.

The framework adapter owns request/session extraction, authentication, cookies, headers, rate limiting, request observability, and transport-wide coarse gates. It passes narrow actor/application values inward.

The service or use case owns capability authorization: ownership, tenant membership, domain roles, target-resource lookup, and operation-specific permission invariants.

```text
must remain true through HTTP, worker, CLI, or another transport
  -> service or use case

exists only to admit/shape one transport request
  -> framework adapter
```

Never pre-fetch domain resources or implement capability policy in a transport adapter. Alternate transports call the same protected application boundary.

## Foundation and Capability Roles

Create only missing foundation roles:

```text
application errors
operational logging port
compatible response contracts
runtime-neutral execution observability
centralized transport mapping
composition root
tests for created boundaries
```

Do not activate persistence, transactions, auth, analytics, outbox, or providers without requested behavior.

Every public capability preserves:

```text
framework adapter
  -> framework-neutral controller
    -> one service OR one use case
      -> repository/provider port
        -> infrastructure adapter
```

The adapter owns framework types, parsing, transport gates, observability, status/envelope, and centralized errors. The controller maps shared input and plain actor values, calls exactly one application boundary, maps the public response, and imports no framework types or generic context.

Use a service for one-domain behavior. Use a use case only for multi-service orchestration, cross-service transactions, outbox coordination, or post-commit effects. Do not let controllers or adapters orchestrate services.

## Persistence, Transactions, and Effects

A persistence-promising public capability remains blocked until durable storage is resolved. Transaction state is opaque and database-only; never mix request IDs, traces, actors, loggers, analytics, or generic metadata into it.

Classify effects:

- durable business effect -> outbox or equivalent durable mechanism;
- operational diagnostic -> application logger, best effort;
- product event -> separate analytics port;
- unsafe-to-retry external effect -> after commit or durable worker.

Never perform unsafe external network effects inside a retryable transaction.

## Known and Derived Specializations

- For Node.js, load `scaffolding` + `runtimes` and apply the canonical Node.js scaffolding guide plus the detected adapter guide.
- For Next.js, Express, or Hono, verify the actual installed versions and load their documented adapter specialization.
- For any other runtime/framework, keep `scaffolding` loaded, add capability slices, inspect repository conventions, retrieve official sources, and derive the integration. Never stop merely because the stack lacks a named slice.

## Verification and Handoff

Verify wire contracts, controller mapping, service/use-case behavior and capability authorization, the real selected framework adapter and transport gates, and generated repository/provider adapters. Then run appropriate static/compile checks, lint/format checks, and the production build.

Report detected stack/layout/tooling/access/persistence, consulted sources and version applicability, dependency decisions, application and authorization ownership, reused/created/patched/blocked roles and files, verification outcomes, and remaining actions.
