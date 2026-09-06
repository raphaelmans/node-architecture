# Organization and Scoped RBAC Convention

Read [authorization](authorization.md) first and [tenancy](../foundations/tenancy.md) for organization grants. This leaf adds roles as permission bundles, not an alternative authorization boundary.

## Apply

- Use Better Auth's organization model as the semantic reference for new applications: memberships, invitations, resource/action permissions, and initial `owner`, `admin`, `member` roles. Preserve existing names and behavior until an explicit migration.
- Define an application-owned permission catalog and grant explicit sets through roles. Normalize role collections in application contracts. Do not use numeric ranks, provider storage encodings, or role-label shortcuts for business decisions.
- Start with code-defined roles; enable organization-defined roles only for a real product need. Multiple roles can contribute applicable allow grants. Empty and unknown grants cannot fall back to a privileged default.
- Keep platform administration separate from organization administration. Explicitly configure business permissions even for administrative roles.
- Branch/resource assignments are application-owned extensions. Validate membership, organization, and scope; inherit organization grants only by explicit domain rule. Do not infer per-team role support from Better Auth teams.
- Do not add per-user overrides or explicit-deny precedence by default. If a branch must restrict inherited organization grants, design that extension rather than treating missing grants as denies.
- For new collaborative organizations, support multiple administrative owners and atomically protect the last eligible owner. Preserve separate business/legal ownership and existing sole-owner rules. Ownership transitions need explicit policy.
- Enforce both management permission and a scope-aware delegation ceiling. Check privilege escalation through role-definition edits and assignments, including every affected scope. Ownership/support exceptions are explicit audited operations, not higher numeric ranks.
- Protect membership, invitation, grant, and owner-count preconditions atomically; record safe audit intent and invalidate affected access results after changes.

## Adoption Boundary

Keep organization membership/lifecycle under one authority. A future Better Auth integration uses its supported APIs rather than competing direct writes to provider-owned tables. Branch rules remain application-owned. Static client role checks do not cover dynamic roles or resource state; use server-backed decisions where required.

This alignment reduces migration work but does not migrate sessions, identity references, custom tables, or Supabase RLS/token integration. Do not install Better Auth merely because this leaf is loaded.

## Verify and Sources

Test role/action combinations, multiple/empty/unknown roles, two branches with different grants, wrong organization, privilege escalation via role edits, concurrent last-owner changes, revocation, and parity across activated implementations.

[Better Auth Organization documentation](https://better-auth.com/docs/plugins/organization) owns current plugin configuration, APIs, schemas, dynamic-role behavior, and limitations. Recheck the target version rather than freezing vendor syntax here.
