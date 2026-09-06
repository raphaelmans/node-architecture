# Tenancy Convention

Load for product workspaces, organizations, membership, invitations, or tenant-scoped resources. Read the parent [foundations](../foundations.md); add [authorization](../security/authorization.md) for access decisions and [RBAC](../security/rbac.md) when roles grant permissions. Product workspace work does not select the monorepo `workspace` slice unless package topology is also involved.

## Apply

- Default new collaborative tenants to an organization and model membership separately from identity. Preserve existing domain names and behavior; do not generate a universal `Workspace` table or migrate existing memberships without scope.
- An invitation is not membership, and an active organization is only selection state. A user may belong to several organizations with different access.
- Resolve a target resource's actual organization and narrower scope in the service/use case. Validate parent-child relationships and eligible membership rather than trusting submitted IDs.
- Pass explicit scope into repository reads, lists/counts, guarded writes, exports, jobs, storage, and realtime operations. Persistence filters/constraints enforce the application-owned isolation rule.
- Define descendant permission inheritance deliberately; branch grants cannot escape their branch or tenant. Scope authorization caches by identity, organization, and resource scope, with explicit revocation freshness.
- Make invitation acceptance an atomic operation: verify recipient, pending state, expiry, membership/assignments, and required audit/outbox intent. Handle retries and concurrent acceptance without duplicated or resurrected grants.
- Removing membership removes effective scoped access. Reactivation cannot silently restore old assignments unless explicitly intended. Define eligible-membership uniqueness and lifecycle from actual requirements.

Use [data-flow](../data-flow.md) for atomicity and only the selected [Drizzle](../runtimes/drizzle.md) or [Supabase](../runtimes/supabase.md) implementation. Authentication-provider actions and local database writes do not become one transaction merely by sharing a workflow.

## Verify

Cover one user in two organizations, foreign resource IDs, mismatched branch/organization pairs, revoked membership with old assignments, invitation recipient/expiry/replay/concurrency, and alternate transports. Use real persistence tests for isolation and atomicity.

## Reference Model

[Better Auth Organization](https://better-auth.com/docs/plugins/organization) informs the organization/member/invitation vocabulary. Align semantics, not internal tables or encodings; do not install it just to follow this convention. Teams are optional groupings, not assumed branch-role support. Retrieve matching official provider docs for actual integration and migrations.
