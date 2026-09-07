# Organization and Scoped RBAC

Read [authorization](./authorization.md) first, and [tenancy](./tenancy.md) when grants belong to organizations. RBAC groups named permissions into roles; it does not replace resource ownership, tenant isolation, or workflow rules.

## Convention

Align new organization-backed models with [Better Auth Organization](https://better-auth.com/docs/plugins/organization): organization memberships, resource/action permissions, and `owner`, `admin`, `member` as starting roles. Custom roles and multiple roles are supported concepts; keep role collections normalized in application contracts rather than copying the provider's storage encoding. Preserve existing role names and effective behavior until migration is explicitly in scope.

Define an application-owned permission catalog such as resource `order` with actions `read` and `update`. Roles grant explicit sets from that catalog. Check named permissions, not numeric thresholds or scattered comparisons such as `role >= manager`. An administrative label does not automatically grant every newly introduced business permission.

Start with code-defined roles unless users genuinely need to create/edit organization-specific roles. Dynamic roles remain subsets of the application's permission catalog. Do not introduce per-user permission overrides or explicit-deny precedence by default; those require a separate policy model. Unknown permissions never grant access, and an explicitly empty grant set must not fall back to a more privileged role.

## Scope and Ownership

Keep global platform administration distinct from organization administration. Do not give a global `admin` implicit tenant access unless an explicit, auditable support policy requires it.

For branch access, use an application-owned scoped assignment linking an eligible organization member, role, and validated scope. Combine applicable allow grants only within that scope and its explicitly defined inheritance. Lack of a branch grant is not an explicit deny; if the product needs branch overrides that restrict organization grants, design and test that extension separately.

Better Auth's documented teams do not establish per-team role assignments. Do not rename branches to teams and assume branch authorization follows. For example, a manager grant at branch A and a viewer grant at branch B must be evaluated against the requested branch, not reduced to one highest role for the user.

For new collaborative organizations, allow multiple administrative owners and prevent removing/demoting the last eligible owner. Ownership changes are explicit, authorized, atomic transitions. Preserve a product's separate legal/business proprietor or existing sole-owner invariant; an `owner` role is not a substitute for that relationship.

## Delegation and Change Safety

- Require permission to manage the relevant members, assignments, or role definitions.
- Apply an explicit grant ceiling: an ordinary administrator cannot grant permissions or scopes they are not allowed to delegate. Ownership transfer and privileged support paths require their own policy, not a numeric-rank exception.
- Evaluate a role-definition change against every affected assignment scope, not only the role editor's currently selected branch. Prevent privilege escalation through role edits as well as assignment edits.
- Enforce critical membership, scope, owner-count, and invitation preconditions atomically. Record actor, target, scope, and changed grants using the application's audit/outbox policy; do not log secrets or invitation tokens.
- Invalidate affected permission results after changes. Client results are UX hints; authoritative decisions must use the configured server-side freshness policy.

## Provider Adoption

When Better Auth is selected, apply [its integration convention](../runtime/nodejs/libraries/better-auth/README.md) for native endpoint enforcement, session mapping, and lifecycle/schema ownership.

Keep one authoritative owner for memberships, invitations, and organization roles. A selected Better Auth integration delegates its supported lifecycle rather than writing its internal tables through a second implementation. Retain application-specific branch rules outside that provider and verify permission behavior during migration; matching names alone does not prove equivalence.

Consult the installed version's official docs for custom/dynamic roles and server-backed permission checks. Static client role checks do not represent runtime-defined roles. Database migration, session replacement, identity references, and Supabase token/RLS integration are separate adoption work, not promised by the repository interface.

## Verification

Test all role/action pairs; combined roles; empty and unknown grants; organization versus branch scope; owner versus business proprietor; grant-ceiling violations through both assignment and definition changes; concurrent last-owner removal; revocation; and identical decisions through every activated transport and persistence implementation.
