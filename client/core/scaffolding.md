# Client Scaffolding Contract

Use this contract when bootstrapping missing client foundations or adding one complete feature capability to an existing client repository. It applies across frameworks and runtimes; stack-specific guides implement it without replacing its guarantees.

## Contents

- [Scope and commands](#scope-and-commands)
- [Safety contract](#safety-contract)
- [Evidence and preflight](#evidence-and-preflight)
- [Layout selection](#layout-selection)
- [Capability and dependency policy](#capability-and-dependency-policy)
- [Contract discovery](#contract-discovery)
- [Foundation roles](#foundation-roles)
- [Feature roles](#feature-roles)
- [Atomicity, idempotency, and conflicts](#atomicity-idempotency-and-conflicts)
- [Verification and report](#verification-and-report)
- [Stack specializations](#stack-specializations)

## Scope and Commands

Scaffolding remains an action of the `$client` architecture router:

```text
$client scaffold foundation
$client scaffold <feature>/<operation>
$client scaffold <feature>/<operation> using canonical layout
```

`foundation` creates only missing cross-feature infrastructure. `<feature>/<operation>` creates one real vertical capability plus only its missing prerequisites. Never create disposable examples.

An unlisted framework is not unsupported. Apply this contract, inspect the repository, and derive the required stack specialization from current authoritative resources. Do not install a new application framework or convert an arbitrary repository merely to make scaffolding possible.

A foundation scaffold may proceed when its complete framework-neutral boundary set is resolved. A vertical feature scaffold must resolve its complete UI/framework integration before any files are written; never leave inner layers waiting for a future adapter.

## Safety Contract

- Complete evidence gathering, preflight, dependency approval, and plan validation before writing.
- Preserve unrelated and uncommitted changes.
- Never overwrite an existing file, including in canonical-layout mode.
- Reuse structurally compatible abstractions even when names differ.
- Do not create parallel transport, error, telemetry, runtime, feature API, or state-synchronization layers merely to match canonical names.
- Do not emit placeholder contracts, unresolved imports, fake endpoints, TODO implementations, generated-file headers, or scaffold manifests.
- Fail closed before affected writes when a required capability, dependency, contract, integration boundary, or authoritative source remains unresolved.

Patch a dirty target only when integration is narrow and unambiguous. Otherwise stop and ask for direction.

## Evidence and Preflight

Inspect before proposing installations or edits:

1. Detect the client language, framework, runtime/metaframework, package or build manager, installed versions, module format, and workspace boundary.
2. Locate source roots, aliases, feature folders, shared contracts, composition roots, route/view entry points, tests, and generated artifacts.
3. Inspect existing transport, server-state, form, validation, configuration, telemetry, error, and testing capabilities through their public behavior.
4. Discover the requested feature's real operation, authoritative request/response contract, cache or synchronization identity, UI intent, and success/failure behavior.
5. Classify every planned boundary as `reuse`, `create`, `patch`, `blocked`, or `not-needed`.
6. Resolve the narrowest relevant tests, type or compile checks, lint checks, and production build.

Use this evidence order:

1. The target repository, manifest, lockfile, configuration, and installed types for current state.
2. This repository's core documents for architecture boundaries.
3. Version-matched official framework, runtime, and package documentation.
4. Official release notes or source code.
5. Non-primary sources only with explicit user approval.

Retrieve current primary sources whenever a decision depends on dependency or peer versions, configuration syntax, framework lifecycle APIs, module format, build behavior, or deployment behavior. If sources are missing or contradictory, block only the affected scaffold before writing. Do not infer an API contract from a view or component name.

## Layout Selection

Default to adaptive placement. Preserve compatible repository paths, names, and framework idioms while enforcing core boundary ownership and dependency direction.

Canonical layout is stack-relative, not one universal directory tree. When explicitly requested, use the detected stack's documented canonical mapping. For an unlisted stack, derive a role-to-path mapping from repository evidence and authoritative framework guidance, show it for approval, and only then write.

```text
core role                   -> stack-native location
shared wire contract        -> ...
client transport boundary   -> ...
feature API                 -> ...
state/query adapter         -> ...        # only when activated
view/coordinator            -> ...
composition root            -> ...
tests                       -> ...
```

Canonical mode changes placement, never overwrite authority. Architectural roles take precedence over exact filenames.

When the resolved placement crosses workspace packages, `$monorepo` owns package creation, manifests, exports, dependency edges, and atomic cross-package coordination. Stop before partial client writes, resolve the topology through `monorepo/core/scaffolding.md`, then resume this contract inside the selected client app/package boundaries. A client-only change contained within existing packages remains owned here.

## Capability and Dependency Policy

Activate capabilities from requested behavior, not from package presence:

| Capability | Activation rule |
| --- | --- |
| Runtime wire validation | Serialized request or response crosses a trust boundary |
| Server-state synchronization | Remote query, mutation, cache, or subscription state exists |
| Form coordination | Non-trivial input workflow requires validation and submission state |
| Operational logging | Boundary diagnostics have an explicit owner |
| Remote error reporting | Production reporting is explicitly required |
| Product analytics | The feature owns a meaningful behavioral event |
| Transport | The feature communicates with an external/server boundary |
| Browser build configuration | The deployable declares public values consumed while producing browser output |
| Browser runtime configuration | Public browser values must be delivered independently of the build |
| Test tooling | A created boundary requires executable verification |

Core does not prescribe packages. Resolve each activated capability as follows:

1. Reuse a compatible capability already present.
2. Apply a documented specialization for the detected stack when available.
3. Otherwise retrieve current authoritative ecosystem guidance and derive the integration.
4. Resolve exact versions compatible with the installed graph.
5. Show the smallest exact install command, explain each dependency, and request approval.
6. Install only after approval and verify the resulting graph.

Package names, native primitives, and fallbacks belong in stack specializations. Never substitute unchecked data, component-owned remote state, unresolved tests, or another ad hoc implementation for a declined required capability.

## Contract Discovery

Use the first trustworthy source:

1. Existing shared runtime-validated wire contract.
2. Existing typed RPC procedure contract.
3. Generated or authoritative API specification.
4. Existing handler/adapter request and response schema.
5. User-provided fields and endpoint behavior.

Reuse compatible partial pieces, but ask for missing behavior. Never infer a public response from persistence models or UI labels. Create one shared wire contract only when no canonical contract exists and enough information is known; client-side form or view validation composes it rather than copying it.

## Foundation Roles

Create only missing roles:

```text
application errors       normalize unknown/provider failures once
operational logging      stable application-facing port
client transport         application-facing request/response port
composition root         construct and own application-scoped dependencies
configuration boundary   only for declared build/runtime configuration surfaces
product analytics        only when an activated capability requires it
tests                    verify every created public boundary
```

Hide concrete providers behind narrow ports and factories. Preserve compatible existing implementations. Add request scope only when the client runtime performs server rendering and a dependency captures request-bound state. Inject specific ports or normalized configuration, never the entire runtime container or environment object. Follow the [configuration boundary](./configuration.md); do not scaffold a browser runtime loader unless independent runtime delivery is required.

## Feature Roles

For a server-backed operation, preserve this abstract flow:

```text
view or interaction adapter
  -> server-state/query adapter        # when activated
    -> feature API
      -> client transport
        -> network
```

Use the actual feature and operation names. Parse untrusted responses at the feature API boundary, normalize provider failures once, and keep cache/synchronization mechanics out of presentation code.

Choose the smallest orchestration owner:

- one state/query adapter for one remote-state responsibility;
- a feature coordinator for genuine multi-step UI orchestration;
- a named synchronization operation for multi-query/cache reconciliation;
- a view/screen coordinator for route-local sequencing;
- presentation code for rendering and callbacks only.

Do not add orchestration solely for telemetry. If several remote mutations must be atomic, require one server-owned workflow endpoint rather than simulating atomicity in the client.

## Atomicity, Idempotency, and Conflicts

On every run:

1. Resolve the complete requested boundary set before writing.
2. Compare required capabilities through public contracts, not filenames.
3. Reuse structural equivalents and report naming drift.
4. Create only missing files and patch compatible files narrowly.
5. Stop on incompatible or ambiguous contracts, transports, state ownership, errors, composition, or framework integration.
6. Treat previously scaffolded files as ordinary maintained code, never generator-owned artifacts.

Foundation scaffolding is atomic within its resolved role set. A vertical feature is atomic across its complete view-to-network flow.

## Verification and Report

Run the narrowest relevant checks first:

1. Tests for every created contract and boundary.
2. Type, compile, or static-analysis checks.
3. Lint or formatting validation for touched files.
4. The relevant production build, especially for framework import/runtime boundaries.

Do not rewrite unrelated configuration to hide failures. Distinguish scaffold-caused failures from pre-existing drift.

Report:

- detected language, framework/runtime, layout mode, package/build manager, and transport;
- authoritative sources consulted and their version applicability;
- dependencies approved, installed, declined, or blocked;
- roles and files reused, created, patched, blocked, or omitted;
- verification commands and outcomes;
- remaining user actions.

Do not commit a retrieval log or generator manifest.

## Stack Specializations

- [React scaffolding](../frameworks/reactjs/scaffolding.md)
- [Next.js client scaffolding](../frameworks/reactjs/metaframeworks/nextjs/scaffolding.md)

These are known implementations, not an allowlist. For any other stack, derive a repository-specific implementation using the evidence policy above.
