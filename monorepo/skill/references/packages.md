# Packages Slice

Use this slice for package activation, imports, exports, task ownership, environment ownership, compilation, and boundary enforcement.

## Activation

| Role | Activated when | Default placement for a new monorepo module |
| --- | --- | --- |
| Contracts | Serialized schemas cross workspace-package boundaries | `packages/contracts/<module>/` |
| Domain | Pure rules genuinely cross client/server runtime or package boundaries | `packages/domain/<module>/` |
| Capabilities | A server-backed operation needs transport-independent application behavior | `packages/capabilities/<module>/`, even with one deployable consumer |
| Adapters | Persistence/provider behavior is required | `packages/adapters/<module>-<provider>/`, even with one deployable consumer |
| UI | Multiple client applications share presentation components | `packages/ui/<system>/` |
| Config | Multiple packages share tool configuration | `packages/config/<tool>/` |

Activate only roles needed by current behavior. Explicit user scope or cohesive existing module ownership may keep roles app-local; do not split that module for a new operation. Do not create unused roles, one package per operation, or one package per onion layer.

## Dependency Direction

```text
client app  -> contracts, optional domain, optional UI
server app  -> contracts, capabilities, adapters
worker app  -> capabilities, adapters
capability  -> contracts, optional domain
adapter     -> capability-owned ports, optional domain
any app/package -> optional config (tooling/dev only)
config      -> optional config, external tooling

contracts/domain -X-> capabilities, adapters, apps
capability       -X-> concrete adapters, apps
config           -X-> contracts, domain, capabilities, adapters, UI, apps
packages         -X-> apps
```

Controllers or explicit mappers translate between serialized contracts and application/domain inputs. Application services and use cases do not become wire-model driven merely because their package also contains a controller.

Config edges are orthogonal to runtime onion dependencies. Each consumer declares its config package in its own manifest; config packages may compose other configs and external tooling but never runtime application code.

## Public Package Contract

- Use unique namespaced identities derived from the target workspace.
- Declare internal dependencies in every consuming manifest.
- Import only through intentional exports; never traverse another package's filesystem.
- Install dependencies in the package that uses them; keep root dependencies repository-scoped.
- Preserve the package manager and lockfile. If absent, propose a currently supported option and obtain approval.
- Choose compiled versus direct-source packages from actual consumers. Do not force consumers to compile unsupported source formats.

## Tasks and Cache

Greenfield vocabulary is `build`, `typecheck`, `lint`, `test:unit`, optional `test:integration`, optional `test:e2e`, and `dev`. Preserve coherent existing names.

Package scripts own task logic; root scripts coordinate. Dependency ordering comes from declared package relationships. Parallel lint, type, and unit checks must invalidate when dependency sources change without unnecessary serialization. Declare outputs only for files actually produced.

## Environment

Classify configuration by consumer and lifecycle: `BrowserBuildConfig`, `PrivateBuildConfig`, `ServerRuntimeConfig`, and optional resource-backed `BrowserRuntimeConfig`. Each deployable owns its executable schemas and checked examples. Reusable packages receive narrow normalized configuration or ports, never a complete environment object, shared environment package, or root environment file.

Application schema validation permits unrelated ambient variables and is separate from task environment policy. Every variable/file that changes cached output affects that task's cache identity; runtime-only values do not invalidate unrelated builds. Publication/deployment credentials authorize side effects rather than artifact content: supply them to a separate non-cacheable task, or equivalent, that consumes build outputs and still runs after a cache hit. Remote caching and credentials remain opt-in.

## Enforcement

Use manifests/exports, package-category checks, and language/runtime onion checks together. Experimental build-system boundaries may supplement them but are not the sole enforcement mechanism. Any boundary violation fails verification.
