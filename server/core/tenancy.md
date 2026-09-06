# Tenancy and Product Workspaces

Use this convention when a capability has organization membership, invitations, workspace switching, or organization/branch-scoped resources. It is independent of authentication, persistence, transport, and repository topology. A product workspace is not the monorepo `workspace` slice.

## Model and Ownership

For new organization-backed products, use an organization as the tenant boundary and membership as the user-to-organization relationship. A user may belong to several organizations. Preserve existing business names such as organization or business; do not introduce a universal `Workspace` table or rename a working model merely to match this guide.

Keep these concepts separate:

| Concept | Meaning |
| --- | --- |
| Identity | The authenticated person or explicitly authorized machine actor |
| Membership | That user's relationship to an organization; an invitation is not membership |
| Organization role | A bundle of permissions within that organization, not a global user rank |
| Access scope | The organization or a narrower domain resource such as a branch |
| Active organization | Navigation/session selection, not proof of access |

Use [RBAC](./rbac.md) when membership carries roles. Use [authorization](./authorization.md) for resource decisions whether or not RBAC is present. Keep membership and invitation behavior in the owning module; extract a shared access module only when several modules actually need it.

## Isolation Contract

- Authenticate at the adapter and pass a plain actor inward. Resolve the requested resource and its owning organization/scope in the service/use case; never trust a client-supplied organization-to-resource relationship.
- Require current eligible membership and a permission valid for that resource's scope. Define machine/system access explicitly rather than representing it as an ordinary user's fabricated membership.
- Make organization/scope restrictions part of repository query inputs and affected-row conditions, including list, count, update, delete, export, background work, storage, and realtime paths. A resource ID by itself does not establish tenant access.
- Persist relationships so a branch/resource cannot reference a parent in a different organization. Database constraints and policies enforce the application-owned isolation contract; repositories do not invent its policy.
- Scope authorization caches by identity, organization, and resource scope. Membership revocation and role changes must take effect according to an explicit freshness policy; do not rely on a long-lived token's old role as permanent authority.
- Organization-level permissions apply to descendants only where the domain explicitly defines that inheritance. Branch-scoped grants cannot escape their branch or organization.

## Membership Lifecycle

Invitations have explicit pending and terminal outcomes, a recipient, expiry, organization, and intended roles/scope. Acceptance verifies the recipient's identity using the selected provider's secure invitation flow and atomically claims an eligible invitation, establishes membership/assignments, and records required audit/outbox intent. Retrying acceptance must not duplicate grants; rejection, cancellation, expiry, and concurrent acceptance must not resurrect an invitation.

Removing membership removes its effective access, including narrower assignments. A membership reactivation must not silently restore old grants unless that behavior is intentional. Enforce uniqueness of eligible membership and assignment relationships; choose physical delete or lifecycle state from actual audit and provider requirements rather than mandating both.

Use the [transaction contract](./transaction.md) and the selected persistence implementation for these transitions. Do not claim that a provider account operation and a local database write share one transaction.

## Verification

Test one user in two organizations; a resource ID from another organization; mismatched branch/organization pairs; removed membership with old assignments; invitation expiry/recipient/replay/concurrency; and an alternate entrypoint reaching the same service. Verify scoped reads and writes against the real persistence boundary, not only policy mocks.

## Reference Model

[Better Auth Organization](https://better-auth.com/docs/plugins/organization) is the semantic reference for organization/member/invitation concepts, as recorded in [ADR 0004](../../docs/adr/0004-align-access-model-with-better-auth-conventions.md). Do not copy its storage encodings into application contracts or install it solely to apply this convention. Teams are optional member groupings, not an assumed branch-permission engine. Exact provider schemas, lifecycle hooks, and migration behavior come from matching official documentation at implementation time.
