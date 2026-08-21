# Package Boundaries

## Package Activation

Separate role activation from physical placement. A role must be required by current behavior before any package is created. For a new module in a monorepo, activated roles use the package convention unless explicit scope or cohesive existing ownership resolves them elsewhere.

| Package role | Activated by current behavior when | Default monorepo placement |
| --- | --- | --- |
| Contract | A serialized contract crosses workspace-package boundaries | `packages/contracts/<module>/` |
| Capability | A server-backed operation needs transport-independent application behavior | `packages/capabilities/<module>/` for a new module, even with one deployable consumer |
| Adapter | Persistence or an external provider is required | `packages/adapters/<module>-<provider>/` for a new module, even with one deployable consumer |
| Domain | Pure rules are genuinely shared across client/server runtimes or packages | `packages/domain/<module>/` |
| UI | Presentation components are shared by multiple client applications | `packages/ui/<system>/` |
| Config | Multiple packages need the same tool configuration | `packages/config/<tool>/` |

Explicit user scope may keep activated roles inside a deployable app. A cohesive existing app-local module remains app-local for incremental work unless migration is explicitly requested. Do not create a package for an unused role, possible future behavior, folder symmetry, or one operation per package.

## Dependency Matrix

`consumer -> dependency`:

```text
client app       -> contracts, optional domain, optional UI
server app       -> contracts, capabilities, adapters
worker app       -> capabilities, adapters
capability       -> contracts, optional domain
adapter          -> capability-owned ports, optional domain
any app/package  -> optional config (tooling/dev dependency only)
config           -> optional config, external tooling

contracts        -X-> domain, capabilities, adapters, apps
domain           -X-> contracts, capabilities, adapters, apps
capability       -X-> concrete adapters or apps
config           -X-> contracts, domain, capabilities, adapters, UI, apps
any package      -X-> deployable apps
```

Within a capability package, controllers may map wire contracts into application inputs, while services and use cases remain independent of serialized transport shapes. Contracts and domain packages are siblings; explicit boundary mappers translate between their representations.

Configuration edges are development-only and orthogonal to the runtime onion. Every consumer declares the config package it uses in its own manifest; config packages may compose other config packages and external tooling but never import runtime application code.

## Package Public Surface

- Give every package a unique namespaced identity appropriate to the target workspace.
- Declare every workspace dependency in the consuming package's manifest.
- Export intentional entry points; do not import another package through filesystem traversal or private source paths.
- Keep application dependencies in the package that uses them; reserve workspace-root dependencies for repository tooling.
- Preserve the detected package manager and lockfile. When none exists, propose a package manager and obtain approval before initialization or installation.
- Choose compilation from consumer evidence. Prefer portable compiled libraries when consumers cannot all compile source; use direct source exports only when every consumer supports them.

## Task Contract

Greenfield package task vocabulary is:

```text
build
typecheck
lint
test:unit
test:integration        when activated
test:e2e                when activated
dev
```

Each package owns the command that implements a task. The workspace root only coordinates package tasks. Task ordering and cache invalidation follow declared package dependencies; parallel checks must still invalidate when dependency source changes. File-producing tasks declare their actual outputs, while non-producing tasks do not invent cache artifacts.

Existing repositories preserve coherent task names and map them rather than being renamed automatically.

## Environment Ownership

- Each deployable application owns, validates, and documents its environment.
- Reusable packages never read a process-wide environment directly and never receive a complete environment object.
- Composition roots inject narrow configuration values or ports.
- Do not create a shared root environment file.
- Cache inputs include the variables and files that actually affect each task.
- Remote caching and provider credentials are opt-in and never written into repository files.

## Enforcement

Use layered enforcement:

1. Package manifests, workspace dependencies, and public exports enforce package identity.
2. A tool-appropriate static check enforces the package dependency matrix.
3. Language/runtime checks enforce onion boundaries inside packages.
4. Experimental build-system checks may supplement, but never replace, stable enforcement.

Boundary violations fail verification. Core defines the rule; a specialization resolves the current supported enforcement mechanism from authoritative sources.
