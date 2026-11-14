# Architecture Decision Records

Decisions that are hard to reverse, surprising without context, and the result of a real trade-off. Terms are defined in the [glossary](../../CONTEXT.md).

| ADR | Decision |
| --- | --- |
| [0001](0001-support-equal-canonical-topologies.md) | Single-project and monorepo are equal canonical topologies |
| [0002](0002-keep-tool-specializations-thin-and-version-resolved.md) | Tool specializations stay thin and version-resolved |
| [0003](0003-default-monorepo-roles-to-workspace-packages.md) | New monorepo modules default to workspace packages |
| [0004](0004-align-access-model-with-better-auth-conventions.md) | The access model follows Better Auth conventions |
| [0005](0005-mount-provider-managed-endpoints-natively.md) | Provider-managed endpoints are mounted natively, not through controllers |
| [0006](0006-keep-environment-ownership-with-each-deployable.md) | Each deployable owns its environment; no shared environment package |
| [0007](0007-use-atomic-repository-operations-where-transactions-cannot-be-shared.md) | Atomic repository operations where a transaction cannot be shared |
| [0008](0008-keep-workflow-state-in-application-records.md) | Workflow state lives in application records, not the workflow engine |
| [0009](0009-route-ai-adapters-through-controllers.md) | Agent tools and workflow business steps enter through controllers, even for internal operations |
