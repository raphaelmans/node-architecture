# Architecture Guidance

This repository defines portable architecture contracts and stack-specific guidance for applying them.

## Language

**Scaffolding contract**:
The framework- and runtime-agnostic guarantees that every scaffolding implementation must preserve, including safety, boundary ownership, idempotency, and verification.
_Avoid_: React scaffolding, Node.js scaffolding

**Scaffolding implementation**:
A realization of the scaffolding contract adapted to the target repository's framework or runtime. It may use a documented specialization or derive one from repository evidence and current authoritative resources.
_Avoid_: Supported-stack allowlist, core scaffolding policy

**Transport gate**:
A cross-cutting access check tied to an entry point, such as authentication, request-context enrichment, or rate limiting.
_Avoid_: Capability authorization

**Capability authorization**:
An application invariant deciding whether an actor may perform a specific operation on a particular domain resource, including ownership and tenant rules.
_Avoid_: Transport authorization

**Monorepo foundation**:
The repository-wide architectural baseline that establishes workspace and package boundaries without assuming any deployable application or business behavior.
_Avoid_: Starter application, application foundation

**Application foundation**:
The non-business architectural baseline owned by one deployable application and adapted to that application's client, server, or worker responsibilities.
_Avoid_: Monorepo foundation, vertical slice

**Module**:
A cohesive business area that owns a related set of operations and contracts.
_Avoid_: Package, layer

**Operation**:
A specific business action within a module.
_Avoid_: Capability as a scaffold target, feature

**Vertical slice**:
The complete implementation of one operation across every boundary activated by its behavior; it may span several applications or packages but is not itself a package.
_Avoid_: Capability package, slice package

**Repository topology**:
The physical organization through which the same architecture roles and dependency rules are realized. Scaffolding derives it from repository evidence rather than treating one topology as universally preferred.
_Avoid_: Architecture variant, stack

**Single-project topology**:
A canonical repository topology in which application roles are colocated within one project boundary.
_Avoid_: Legacy layout, non-monorepo fallback

**Monorepo topology**:
A canonical repository topology in which deployable applications and reusable internal packages have distinct workspace boundaries.
_Avoid_: Preferred layout, Turborepo architecture

**Workspace package**:
An independently addressable ownership and reuse boundary within a monorepo topology. It may contain several architecture layers while preserving their inward dependency direction.
_Avoid_: Architecture layer, one package per layer

**Package placement default**:
The monorepo convention that activated capability and adapter roles of a new module use workspace packages. Explicit user scope or cohesive existing module ownership may keep them app-local until an explicit migration.
_Avoid_: Package only after a second consumer, automatic partial migration

**Tooling dependency**:
A development-only edge from an application or package to shared configuration; it does not participate in or weaken the runtime onion dependency graph.
_Avoid_: Runtime dependency, architecture-layer dependency

**Architecture convention**:
A durable ownership, dependency, safety, or verification rule governed by this repository and intended to remain valid across tool versions.
_Avoid_: Tool configuration, copied vendor guidance

**Thin specialization**:
A stack-specific mapping from architecture conventions to a detected tool or framework whose version-sensitive behavior is resolved from matching authoritative sources at execution time.
_Avoid_: Embedded vendor manual, frozen configuration cookbook
