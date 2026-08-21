# Monorepo Architecture

## Equal Canonical Topologies

The architecture has two equal physical mappings:

| Role | Single-project topology | Monorepo topology |
| --- | --- | --- |
| Deployable client | Client source tree | Application package |
| Deployable server or worker | Server source tree | Application package |
| Shared wire contract | Owning module's isomorphic contract boundary | Contract package when it crosses package boundaries |
| Shared pure domain rule | Owning module's isomorphic domain boundary | Domain package when it crosses runtime/package boundaries |
| Application behavior | Module service/use-case/controller boundary | Capability package for an activated new module by default |
| Infrastructure adapter | App/module-owned adapter | Adapter package when persistence/provider behavior is activated for a new module |
| Composition root | App-owned runtime boundary | Deployable application package |

Examples in `client/` and `server/` may use the single-project mapping. They name architecture roles, not a requirement to collapse a workspace into one project.

## Monorepo Placement Precedence

Package placement applies only to roles required by current behavior; it never creates empty or speculative packages. Resolve an activated role in this order:

1. Follow an explicit user request to keep a module app-local or migrate it.
2. Reuse a cohesive existing module owner, including an app-local module, unless migration is explicitly requested.
3. For a new module without placement precedent, use the monorepo package convention for contracts, capabilities, and activated adapters. Activate domain, UI, and config packages only when their sharing rules are satisfied.

Do not split one module between app-local and package-default ownership merely to apply the convention to a new operation. Package boundaries are organized by stable module/role ownership, not one package per operation or onion layer.

## Onion Alignment

Workspace packages and onion layers solve different problems. Packages define ownership and reuse; onion layers define source dependency direction. One package may contain several layers while preserving inward imports.

```text
                  OUTSIDE / MOST VOLATILE
┌──────────────────────────────────────────────────────────┐
│ Deployable apps: frameworks, transports, composition     │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Interface and infrastructure adapters              │  │
│  │ controllers, wire mappers, database/provider code  │  │
│  │                                                    │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │ Application                                 │  │  │
│  │  │ services, use cases, application ports      │  │  │
│  │  │                                              │  │  │
│  │  │  ┌────────────────────────────────────────┐  │  │  │
│  │  │  │ Domain                                 │  │  │  │
│  │  │  │ pure rules, models, invariants         │  │  │  │
│  │  │  └────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                   INSIDE / MOST STABLE
```

Source dependencies point inward. At runtime an application may call an injected outer adapter through an inward-owned port; the adapter still imports and implements the port, never the reverse.

## Reference Workspace Shape

This is a role map, not a requirement to generate every directory:

```text
apps/
  <client-app>/                 client transport, views, features, composition
  <server-app>/                 public transport and composition
  <worker-app>/                 job/event transport and composition

packages/
  contracts/<module>/           serialized wire schemas
  domain/<module>/              optional cross-runtime pure rules
  capabilities/<module>/        portable server application behavior and ports
  adapters/<module>-<provider>/ concrete infrastructure adapters
  ui/<system>/                  multi-client presentation packages
  config/<tool>/                shared tool configuration
```

Grouping directories are not themselves packages. A build-system specialization maps these roles to its currently supported workspace-discovery mechanism.

## Client and Server Relationship

A client application is not an outer ring of the server onion. It is a separate deployable with its own client dependency stack:

```text
view -> query/state adapter -> feature API -> client transport -> network
```

Client applications may consume shared wire contracts and explicitly cross-runtime domain packages. They never import server capability or infrastructure packages.
