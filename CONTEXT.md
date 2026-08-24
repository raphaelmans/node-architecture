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

**Environment boundary**:
The deployable-application boundary that reads and validates external configuration, then normalizes it into application configuration. Reusable components declare focused configuration needs but do not own or read a deployable's environment.
_Avoid_: Shared environment package, global environment service

**External environment contract**:
The deployable-owned inventory of external variables required to build, start, or operate it, classified by visibility, consumer, and lifecycle. It is a setup and validation contract, not an application dependency-injection surface.
_Avoid_: Undifferentiated server environment, application configuration

**Executable environment schema**:
The authoritative machine-executable declaration of a lifecycle-specific subset of an external environment contract. It validates only declared variables, permits unrelated ambient variables, and may be composed with other schemas while the environment example remains a checked projection.
_Avoid_: Environment example as source of truth, globally importable environment object

**Task environment policy**:
The build-orchestration boundary that determines which ambient variables reach a task and which influence its cache identity. It is independent of the executable environment schema that validates application-owned variables.
_Avoid_: Application configuration, environment validation

**Configuration materialization**:
Validating and normalizing external configuration once at the earliest lifecycle point where it is available, before the deployable accepts traffic or work that depends on it.
_Avoid_: Lazy environment lookup, universal build-time validation

**Application configuration**:
Validated, normalized, framework-neutral values that a deployable application's composition boundary supplies explicitly to the dependencies that require them. External variable names and environment-reading mechanisms do not cross this boundary.
_Avoid_: Raw environment, environment service, framework-prefixed configuration

**Configuration namespace**:
A focused, typed portion of application configuration exposed to a framework-owned outer component according to its declared needs. Generic configuration lookup and external variable names remain at the environment boundary.
_Avoid_: Global configuration lookup, complete application configuration

**Configuration surface**:
The typed application configuration visible within one execution realm. A deployable may expose separate surfaces from one environment boundary while its framework specialization chooses a unified or physically split validation implementation.
_Avoid_: Combined cross-realm configuration, mandatory file split

**Browser build configuration (`BrowserBuildConfig`)**:
Public browser configuration materialized from a build process and embedded in its output. It owns only build-materialized fields; the browser never receives the originating environment variables.
_Avoid_: Browser environment, browser runtime configuration

**Private build configuration (`PrivateBuildConfig`)**:
Private configuration materialized while producing a non-browser artifact and excluded from public artifacts. It owns only output-affecting fields; credentials that only authorize publication or deployment belong to separate task execution policy.
_Avoid_: Server runtime configuration, browser build configuration

**Server runtime configuration (`ServerRuntimeConfig`)**:
Validated, normalized configuration materialized from host-supplied values for one server or worker execution. It may contain secrets and never crosses into browser-reachable code.
_Avoid_: Server environment, browser runtime configuration

**Browser runtime configuration (`BrowserRuntimeConfig`)**:
Public configuration data loaded and validated by the browser independently of build-time environment substitution when the work that depends on it begins. It owns only runtime-loaded fields and never contains secrets.
_Avoid_: Environment variable, browser build configuration

**Configuration mode**:
A validated configuration state for an optional capability in which activation explicitly requires every value needed to compose that capability.
_Avoid_: Missing means disabled, unrelated optional variables

**Framework-native composition**:
Using a selected framework's dependency injection, lifecycle, module, and testing mechanisms at its outer application boundaries while keeping reusable inward components independent of that framework.
_Avoid_: Reimplementing the framework, framework-coupled core

**Architecture convention**:
A durable ownership, dependency, safety, or verification rule governed by this repository and intended to remain valid across tool versions.
_Avoid_: Tool configuration, copied vendor guidance

**Thin specialization**:
A stack-specific mapping from architecture conventions to a detected tool or framework whose version-sensitive behavior is resolved from matching authoritative sources at execution time.
_Avoid_: Embedded vendor manual, frozen configuration cookbook
