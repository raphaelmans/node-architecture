# Capability Authorization

Use this convention whenever an operation has actor, ownership, membership, or resource-access rules. Authentication and route visibility are not substitutes for authorization. Add [tenancy](./tenancy.md) for tenant boundaries and [RBAC](./rbac.md) only when roles grant permissions.

## Enforcement Boundary

Preserve `adapter -> controller -> service/use case -> repository/provider port`.

- The adapter verifies identity and applies coarse transport gates. The controller maps a plain actor and validated public input to one application operation.
- The service owns reusable resource policy; a use case owns policy spanning its workflow. A focused access-policy component may implement shared decisions through an application-owned port. Do not build a universal policy engine for a single ownership check.
- Resolve the target's actual organization, branch, ownership, and relevant state before deciding. Check all required permissions and invariants, not whichever check happens to succeed first.
- Deny missing, unknown, revoked, or out-of-scope grants. Distinguish a genuine denial from an unavailable identity/policy store; fail closed without disguising outages as successful anonymous access.
- Return typed, safe errors. Use a consistent not-found/forbidden policy where resource existence is sensitive, including list and count behavior.

Workers, CLIs, Next.js route handlers/server actions, Express, Hono, and alternate transports must reach the same capability rules. Server rendering must authorize data before serialization. A server-side caller is not inherently privileged.

## Persistence Enforcement

The application owns the rule, but more than one enforcement point may be necessary. Repository filters, database constraints, RLS, and database functions enforce the declared policy where data is accessed or changed. This is not permission for repository adapters to invent their own role hierarchy.

For an atomic access-sensitive change, protect the authorization-critical preconditions through commit: use guarded writes, transaction-scoped checks/locking, or a purpose-specific database operation. An earlier service check alone is insufficient when a concurrent change could violate the invariant. Define and test the intended ordering of concurrent revocation and mutation.

If a database API is reachable directly, it is a public entrypoint too. Its policies/functions must enforce every applicable guarantee without assuming the caller passed through the application server. Restrict grants/exposure when a function or table is server-only. Browser access is an explicit design choice, not implied by using Supabase in a server repository.

## Permission-Aware UI

Expose only the current user's safe, scoped access result needed for UX. A client can hide or disable controls using that result, but cannot authorize the subsequent mutation. Recheck on the server even when the client submits a role, permission list, or earlier access result.

Keep vendor session objects, role storage encodings, tokens, and policy engine types behind integration boundaries. If Better Auth is adopted, use its supported APIs for the organization behavior it owns; application resource/state rules still apply. Avoid a parallel writable membership authority.

## Verification

Cover anonymous, allowed, denied, unknown permission, revoked membership, wrong organization/scope, and policy-store outage. Invoke protected operations without their usual route middleware and verify they remain protected. Exercise RLS/function entrypoints directly where exposed, and use real database tests for race-sensitive grants and writes.

See [Next.js authentication guidance](https://nextjs.org/docs/app/guides/authentication) for framework-owned entrypoints and [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security) for provider enforcement mechanics. These sources own current syntax; this document owns application boundaries.
