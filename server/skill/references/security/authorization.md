# Capability Authorization Convention

Load for actor, resource ownership, membership, and operation-access rules. Read [security](../security.md); add [tenancy](../foundations/tenancy.md) for tenant boundaries and [RBAC](rbac.md) only when roles grant permissions.

## Apply

- Authenticate and apply coarse gates at the adapter; pass a plain actor through the controller to one application operation. Provider sessions and framework context stay outside.
- Services own reusable resource rules; use cases own workflow rules. Extract a focused access-policy port only when reuse justifies it, not a universal policy engine for one ownership check.
- Resolve actual resource ownership, organization, scope, and relevant state. Require all applicable permissions and invariants. Deny unknown, absent, revoked, and out-of-scope grants.
- Distinguish denial from policy-store outage using typed safe errors. Fail closed; never convert an unavailable provider to successful anonymous access. Apply a consistent existence-disclosure policy.
- Preserve checks through workers, CLIs, alternate transports, and server rendering. A server caller or hidden route is not proof of authorization.
- Protect race-sensitive preconditions through commit using guarded writes, transaction checks/locking, or an atomic database operation. Specify ordering semantics for concurrent revocation and mutation.
- Repositories, RLS, constraints, and database functions enforce the application-owned policy at the data boundary; they do not invent a second policy. Directly exposed database APIs must enforce the full public contract or be restricted to the intended trusted caller.
- Expose only safe scoped access results for client UX. Recheck operations server-side; do not accept a client's earlier result, role list, or `authorized` flag as evidence.

If Better Auth is adopted, delegate the organization lifecycle it owns through supported APIs while retaining application resource rules. Keep one authoritative membership writer and avoid vendor types in application contracts.

## Verify

Cover anonymous/allowed/denied/outage cases, wrong tenant/scope, revoked membership, direct invocation without usual middleware, and direct database/API bypass attempts. Test race-sensitive transitions against real persistence.

## Official Sources

- [Next.js authentication](https://nextjs.org/docs/app/guides/authentication)
- [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security)

Derive framework/provider enforcement mechanics from matching documentation; the application owns the policy and observable behavior.
