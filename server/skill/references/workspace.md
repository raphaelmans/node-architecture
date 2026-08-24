# Server Workspace Slice

Use this slice when server work occurs in a workspace, consumes internal packages, or would create/change capability, adapter, contract, or domain package boundaries.

## Equal Topologies

Single-project and monorepo layouts preserve the same inward server flow:

```text
framework adapter
  -> framework-neutral controller
    -> one service or one use case
      -> repository/provider port
        <- concrete adapter implementation
```

```text
server role                single project                 monorepo when activated
-----------                --------------                 -----------------------
transport/composition      app source                     apps/<server|worker>/
wire contracts             module shared/contracts       packages/contracts/<module>
shared pure rules          module shared domain           packages/domain/<module>
application behavior       module                         packages/capabilities/<module>
concrete infrastructure    module adapter                 packages/adapters/<module>-<provider>
configuration boundary     deployable composition         remains in apps/<server|worker>/
```

A workspace package may contain several onion layers. Controllers may depend on wire contracts and application boundaries; services/use cases remain independent of transport shapes; concrete adapters import and implement inward-owned ports.

## Composition and Imports

Deployable server/worker apps are graph endpoints. Their composition roots select concrete adapters and inject narrow `PrivateBuildConfig`/`ServerRuntimeConfig` values. Capabilities never import concrete adapters or apps. Packages never read a shared root environment, own deployable variable names, or receive the complete app environment. Task environment availability/cache identity remains separate from schema validation; publication/deployment side effects consume build outputs through separate execution that still runs when those outputs come from cache.

For a new monorepo module, activated capability and adapter roles use package placement by default, even with one deployable consumer. Unused roles remain absent. Preserve a cohesive existing app-local module for incremental operations unless the user explicitly requests migration; never create one package per operation or onion layer.

Server apps/packages may declare shared config packages as tooling/dev dependencies. Config packages remain outside the runtime onion and never import contracts, domain, capabilities, adapters, UI, or deployable apps.

## Coordination

`$server` owns files inside resolved server app/package boundaries. `$monorepo` owns package creation, manifests, exports, workspace dependency edges, task coordination, and atomic changes spanning packages.

If a server scaffold requires a new or changed package boundary, stop before partial writes, resolve the cross-package slice through monorepo scaffolding, then resume the server contract inside the approved packages.

Retrieve version-matched official build-system/runtime guidance for exact workspace, compilation, task, environment, or deployment behavior. Do not embed frozen vendor syntax in this slice.
