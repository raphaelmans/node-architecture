# Server Runtime Documentation

Runtime-specific documentation implements the contracts defined in [`server/core/`](../core/README.md).

## Dependency Direction

```text
core/kernel + application ports
        ↓ implemented by
runtime adapters (Node.js)
        ↓ composed by
libraries and metaframeworks
```

- Core must not import runtime, library, or framework code.
- Runtime guides may choose concrete implementations, but must not redefine core contracts.
- Libraries adapt vendor APIs behind kernel/application interfaces.
- Metaframeworks own entrypoints and lifecycle hooks; they call module-owned framework-neutral controllers.

Current runtime:

- [Node.js](./nodejs/README.md)
