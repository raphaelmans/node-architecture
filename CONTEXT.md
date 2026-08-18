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
