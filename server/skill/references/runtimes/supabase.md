# Supabase Integration Convention

Load for direct Supabase repositories, database functions, or relevant Auth/Storage/Realtime boundaries. Read [runtimes](../runtimes.md), [data-flow](../data-flow.md) for persistence, and [security](../security.md) for identity, credentials, or exposed data. Drizzle is an independent sibling, not a requirement.

## Apply

- A Supabase-only repository calls the SDK/data API directly behind an application-owned interface. Map generated rows/function results to application records; SDK types, query builders, and errors stay in adapters.
- Construct user/session-dependent clients per request. Isolate privileged clients in explicit server-only factories; never escalate privileges as a fallback for a failed user operation.
- Server repository use does not imply browser CRUD. If direct data access is selected, RLS/grants/functions enforce the complete public contract; restrict weaker paths to server-only operations.
- Represent atomic multi-write work as a purpose-specific repository operation executed through one database function. Do not fake callback transactions across requests or expose arbitrary-SQL RPC.
- The function enforces the application-owned atomic contract, including applicable identity, recipient, membership, scope, invitation, grant, and owner-preservation preconditions. Service prechecks alone cannot protect a concurrent transition.
- User-callable functions derive identity from trusted request context, not submitted actor IDs. Restricted privileged functions can receive a server-verified actor but still enforce declared preconditions. Never trust a caller's `authorized` flag.
- Prefer invoker execution. Justify elevated execution, use a safe explicit search path and qualified objects, restrict execution grants, and test the real privilege/RLS path. Maintain functions and policies in reviewed migrations.
- Failures must roll back the whole operation; preserve replay behavior for uncertain network outcomes. Store required audit/outbox intent atomically. Storage, email, and other external effects are not part of the database transaction.
- Coexisting Drizzle and Supabase operations have explicit write/migration ownership. An HTTP call does not participate in a Drizzle transaction. Use one atomic database operation or explicit compensation/outbox semantics for mixed workflows.

Future Better Auth adoption selects an auth adapter independently of business repositories. Verify identity mapping and Supabase token/RLS/Storage/Realtime integration; Better Auth sessions are not automatically Supabase access tokens. Do not create competing writable membership authorities.

## Verify and Sources

Exercise actual user and privileged paths, direct RPC bypass, forged actors, cross-organization IDs, rollback, replay, revocation, grant escalation, and concurrency. Confirm result mapping and safe errors.

- [Database functions](https://supabase.com/docs/guides/database/functions)
- [PostgREST transactions](https://docs.postgrest.org/en/stable/references/transactions.html)
- [RLS](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [API keys](https://supabase.com/docs/guides/getting-started/api-keys)
- [Better Auth migration](https://better-auth.com/docs/guides/supabase-migration-guide)

Resolve exact SDK, key, SQL-security, schema-exposure, and migration details from matching official documentation. Do not add a PostgreSQL leaf or duplicate the vendor manual.
