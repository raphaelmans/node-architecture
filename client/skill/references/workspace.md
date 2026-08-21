# Client Workspace Slice

Use this slice when client work occurs in a workspace, consumes internal packages, or would create/change package boundaries.

## Equal Topologies

Single-project and monorepo layouts are equal canonical mappings. Preserve the detected topology and the client dependency stack:

```text
view -> query/state adapter -> feature API -> client transport -> network
```

```text
client role                  single project                 monorepo when activated
-----------                  --------------                 -----------------------
routes/features/common       src/*                          apps/<client>/src/*
wire contracts               module shared/contracts       packages/contracts/<module>
cross-runtime pure rules     module shared domain           packages/domain/<module>
shared UI                    components                     packages/ui/<system>
composition root             app-owned runtime              remains app-owned
```

Do not extract app-local client features merely because a workspace exists. Domain and UI packages require genuine cross-package consumers. When a new server-backed module activates cross-package contracts through the monorepo package convention, the client consumes the contract package through public exports.

## Allowed Imports

A client application may import intentional exports from contract, explicit cross-runtime domain, UI, and tooling packages. It never imports server capability packages, repositories, provider adapters, server composition, environment modules, entities, or internal commands.

Tooling packages are declared development dependencies and remain orthogonal to the runtime onion; they never import client or server application code.

Contracts and domain are siblings: serialized DTOs do not become domain models, and domain packages do not depend on transport contracts. Feature APIs or explicit mappers translate at the client boundary.

## Coordination

`$client` owns files inside resolved client app/package boundaries. `$monorepo` owns package creation, manifests, exports, workspace dependency edges, shared task coordination, and atomic changes spanning packages.

If a client scaffold requires a new or changed package boundary:

```text
stop before client writes
  -> resolve cross-package plan through monorepo scaffolding
    -> resume client roles inside approved boundaries
```

Retrieve version-matched official build-system/framework guidance for exact package consumption, transpilation, task, or build behavior. Do not copy frozen tool syntax into this slice.
