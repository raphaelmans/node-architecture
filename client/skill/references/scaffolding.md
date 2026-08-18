# Client Scaffolding Slice

Use this slice when the user invokes `$client scaffold`, asks to bootstrap missing client foundations, or requests one repository-aware vertical feature. It applies to listed and unlisted client frameworks. Load the relevant architecture slices and derive stack-specific execution from repository evidence and current primary sources.

## Commands and Scope

```text
$client scaffold foundation
$client scaffold <feature>/<operation>
$client scaffold <feature>/<operation> using canonical layout
```

`foundation` creates only missing cross-feature infrastructure. A vertical feature creates one real view-to-network capability plus only its missing prerequisites. Never generate example features or install a new application framework merely to match a known specialization.

An unlisted framework is not unsupported. Use the generic contract, inspect its repository conventions, retrieve current official framework/runtime resources, and derive the specialization. A framework-neutral foundation may proceed when its complete role set is resolved. A vertical feature must resolve its complete UI/framework integration before any writes.

## Preflight Before Writes

1. Detect language, framework, runtime/metaframework, package/build manager, installed versions, module format, workspace, source root, routes/views, aliases, composition roots, and tests.
2. Inspect existing contract, validation, error, transport, server-state, form, telemetry, runtime, and test capabilities through public behavior.
3. Discover the actual operation, trustworthy request/response contract, cache/synchronization identity, UI intent, and success/failure behavior.
4. Classify every required boundary as `reuse`, `create`, `patch`, `blocked`, or `not-needed`.
5. Retrieve current primary sources for version-sensitive dependency, configuration, lifecycle, module-format, build, and deployment decisions.
6. Resolve exact compatible dependencies, show the smallest exact install command and rationale, and ask for approval.
7. Validate the complete plan, install approved dependencies, verify the graph, and only then write.

Evidence priority:

```text
target repository + manifest/lock/config/installed types
  -> repository core architecture docs
    -> version-matched official documentation
      -> official release notes/source
        -> non-primary sources only with explicit approval
```

Fail closed on missing or contradictory evidence before affected writes. Do not persist a retrieval log or generator manifest.

## Safety and Atomicity

- Preserve unrelated and dirty work.
- Never overwrite, including canonical mode.
- Reuse structural equivalents despite naming differences.
- Do not create parallel transports, errors, telemetry, runtimes, feature APIs, or state layers.
- Do not emit placeholder DTOs, unresolved imports, fake endpoints, TODOs, generated headers, or scaffold metadata.
- Patch dirty files only when narrow and unambiguous.
- Treat prior scaffolded files as ordinary maintained code.

Foundation scaffolding is atomic within its resolved role set. A vertical feature is atomic across its complete framework/view-to-network flow; do not write inner layers while a required UI/framework adapter remains unresolved.

## Layout Mode

Default to adaptive placement: preserve compatible repository paths and stack idioms while enforcing architectural roles.

Canonical layout is stack-relative. Use a documented specialization when available. For an unlisted stack, derive and show a role-to-path mapping for approval:

```text
shared wire contract       -> stack-native location
client transport           -> stack-native location
feature API                -> stack-native location
state/query adapter        -> stack-native location when activated
view/coordinator           -> stack-native location
composition root           -> stack-native location
tests                      -> stack-native location
```

Canonical mode changes placement, never overwrite authority.

## Capability Resolution

Activate only behavior the requested scaffold needs:

| Capability | Activation rule |
| --- | --- |
| Runtime validation | Serialized data crosses a trust boundary |
| Server state | Remote query, mutation, cache, or subscription exists |
| Forms | Non-trivial validated input workflow exists |
| Operational logging | Boundary diagnostics have an explicit owner |
| Remote reporting | Production reporting is explicitly required |
| Product analytics | A meaningful feature-owned behavioral event exists |
| Transport | The feature calls an external/server boundary |
| Tests | A created public boundary needs executable verification |

Do not choose packages in the generic slice. Reuse compatible repository capabilities first, then a documented stack specialization, then current official ecosystem guidance. Resolve exact versions and obtain dependency approval. Package-specific fallbacks belong to the selected specialization; never replace required validation, remote-state ownership, or tests with ad hoc code.

## Contract Discovery

Use the first trustworthy source:

1. Existing shared runtime-validated wire contract.
2. Existing typed RPC contract.
3. Generated or authoritative API specification.
4. Existing handler/adapter schema.
5. User-provided fields and behavior.

Ask for missing details. Never infer DTOs from view names or persistence entities. Create one shared wire contract only when enough behavior is known; UI/form schemas compose it rather than copy it.

## Foundation and Feature Roles

Create only missing foundation roles:

```text
application errors
operational logging port
client transport port
composition root
product analytics when activated
tests for created boundaries
```

Hide providers behind narrow ports/factories and inject specific dependencies rather than a runtime container.

For server-backed features preserve:

```text
view or interaction adapter
  -> state/query adapter when activated
    -> feature API
      -> client transport
        -> network
```

Parse untrusted responses at the feature API, normalize failures once, and keep cache/synchronization mechanics out of presentation code. Use the smallest orchestration owner; require one server-owned workflow endpoint for atomic remote mutations.

## Known and Derived Specializations

- For React, load `scaffolding` + `react` and apply the canonical React scaffolding guide.
- For Next.js, load `scaffolding` + `react` + `nextjs` and verify router, Server/Client boundaries, config format, environment behavior, and the production build against installed versions.
- For any other framework, keep `scaffolding` loaded, add capability slices, inspect repository conventions, retrieve official sources, and derive the integration. Never stop merely because the stack lacks a named slice.

## Verification and Handoff

Run focused tests for every generated contract and boundary, then the repository's type/compile checks, touched-file lint/format checks, and relevant production build.

Report detected stack/layout/tooling/transport, consulted sources and version applicability, dependency decisions, reused/created/patched/blocked roles and files, verification outcomes, and remaining actions.
