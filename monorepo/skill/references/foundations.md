# Monorepo Foundations Slice

Use this slice for repository topology, deployable application ownership, composition, onion alignment, and cross-client/server workspace architecture.

## Canonical Topologies

Single-project and monorepo topologies implement the same roles and dependency directions. Paths differ; architecture does not. Preserve cohesive existing module ownership rather than migrating merely to match an example. For a new monorepo module, activated roles use the package convention unless the user explicitly requests app-local scope.

```text
single project                 monorepo
--------------                 --------
app source root                apps/<deployable>/
module shared contracts        packages/contracts/<module>/ when cross-package
module shared pure rules       packages/domain/<module>/ when cross-runtime
portable application behavior packages/capabilities/<module>/ when activated
concrete provider adapter      packages/adapters/<module>-<provider>/ when activated
deployable configuration       remains app-owned in either topology
```

Activation means current behavior needs the role; it does not mean generating every possible package. New modules use capability and activated adapter packages even with one deployable consumer. Domain, UI, config, and adapter roles remain absent when their behavior/sharing condition is not present. Do not split an existing app-local module for one new operation; migrate its complete ownership only when explicitly requested.

## Onion and Package Boundaries

Packages define ownership and reuse; onion layers define inward source dependency. One package may contain controllers, application services/use cases, ports, and server-owned domain rules when their ownership is cohesive.

```text
framework/transport/composition
  -> controller or interface mapper
    -> service or use case + inward-owned ports
      -> domain rules

concrete adapter -> implements inward-owned port
```

At runtime application policy may call outward through an injected port. Source dependencies remain inverted because the adapter imports the port, never the application importing the concrete adapter.

A client app is a separate deployable with its own flow:

```text
view -> query/state adapter -> feature API -> client transport -> network
```

It may import wire contracts and explicitly cross-runtime pure domain packages, but never server capabilities or adapters.

## Composition

Deployable applications are endpoints of the package graph. Their composition roots select concrete transports, repositories, providers, lifecycle-specific configuration, and runtime lifetimes. Reusable packages never select providers, inspect app containers, import applications, or own deployable environment schemas.

## Review Checklist

- The selected topology follows repository evidence.
- Apps are never imported as libraries.
- Package boundaries do not replace inward source layering.
- Client and server share only intentional isomorphic contracts/domain rules.
- Concrete adapters are selected only by application composition.
- No unused role or one-operation package was created.
- Existing cohesive app-local ownership was not partially migrated.
