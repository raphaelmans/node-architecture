# Supabase Data-Access Convention

Use when a repository directly uses Supabase's data API or database functions, or when Supabase Auth, Storage, or Realtime creates a relevant security boundary. Supabase is independent of [Drizzle](../drizzle/README.md): an application may use either or both. Hosting PostgreSQL on Supabase does not require its data API.

## Repository Boundary

Application services depend on application-owned repository interfaces and records. A Supabase repository calls the SDK/data API directly, maps generated row/function types into application results, and translates known provider failures. Do not insert an ORM solely to satisfy the architecture or expose SDK builders, response wrappers, or generated database types inward.

User/session-bound clients are request-scoped. Privileged clients are explicitly named, server-only, and never the ordinary fallback when a user operation fails. Composition chooses credentials and verified identity; application services receive focused ports, not cookies, SDK clients, or environment objects.

Using Supabase in a server repository does not authorize browser CRUD. If direct browser access is explicitly selected, table/view/function grants and RLS must enforce the complete public entrypoint contract. Keep application-server-only operations inaccessible through weaker data API paths.

## Atomic Database Functions

For a multi-write operation that must be atomic, define a purpose-specific repository method, such as accepting an invitation with membership and scoped assignments. Implement it as one database-function call containing all required database changes and preconditions. Do not expose a generic arbitrary-SQL RPC or pretend several SDK requests share a transaction.

The service/use case owns the operation's policy and result contract. The function enforces that contract at the atomic boundary, including authorization-critical checks that can race: recipient/identity, eligible membership, scope relationship, invitation state/expiry, owner preservation, and allowed grants as applicable. An earlier application check or a caller-supplied `authorized: true` is insufficient.

Verify identity from the trusted request context for user-callable functions; do not trust an actor ID supplied by the browser. A server-only privileged operation may receive a server-verified actor through a restricted boundary, but still enforces the operation's declared preconditions. Functions and RLS implement the application-owned policy, not a competing business model.

Prefer invoker execution. If elevated execution is genuinely required, justify it, use a safe explicit search path and qualified objects, restrict execution grants, and test the privilege boundary. Do not assume a function automatically inherits the desired table RLS protections. Maintain function definitions, grants, and policies as reviewed migrations alongside their repository contract.

Return failures so the transaction rolls back; do not catch a failure and return success after partial writes. Preserve retry/idempotency behavior for ambiguous network outcomes. Persist required audit/outbox intent in that same atomic operation; email, storage, and other external effects do not participate in its database transaction.

## Coexistence and Future Authentication

Direct Supabase and Drizzle repositories can coexist with explicit operation and schema ownership. A Supabase HTTP call cannot participate in a Drizzle callback transaction. Coordinate mixed-system workflows with a purpose-specific single-database operation or an explicit compensating/outbox workflow, not a fake shared context.

If adopting Better Auth later, select its documented database adapter independently of business repositories. Reassess how verified identity reaches Supabase RLS, Storage, and Realtime; Better Auth sessions are not automatically Supabase access tokens. Preserve or deliberately map identity references and avoid two writable membership authorities.

## Verification and Sources

Test via actual user-scoped and privileged access paths: cross-organization IDs, direct RPC bypass attempts, forged actor input, revocation, unauthorized grants, rollback, replay, and concurrent acceptance/last-owner changes. Verify generated type/result mapping and safe provider-error translation.

- [Supabase database functions](https://supabase.com/docs/guides/database/functions)
- [PostgREST transaction semantics](https://docs.postgrest.org/en/stable/references/transactions.html)
- [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase API keys](https://supabase.com/docs/guides/getting-started/api-keys)
- [Better Auth Supabase migration](https://better-auth.com/docs/guides/supabase-migration-guide)

Resolve exact SDK calls, credential taxonomy, SQL security syntax, grants, schema exposure, and migrations from matching official documentation. There is no separate PostgreSQL leaf or copied database manual.
