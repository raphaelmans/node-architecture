---
status: accepted
---

# Keep environment ownership with each deployable

In a monorepo it is common to centralize configuration in a root environment file or a shared environment package. We instead make each deployable application the sole environment boundary: it owns its executable schemas, its checked example, and the composition that turns external variables into application configuration, while reusable packages only declare focused needs and receive normalized values. This costs some duplication when two applications read the same variable, and buys independent deployment contracts, no secrets reachable from a package another runtime imports, and packages that can be tested without a process environment.

## Consequences

- Schema fields may be composed across lifecycles inside one deployable, never across deployables.
- Which ambient variables reach a task and affect its cache identity is a separate build-orchestration policy, not part of application validation.
