---
status: accepted
---

# Align the access model with Better Auth conventions

Use [Better Auth's organization model](https://better-auth.com/docs/plugins/organization) as the reference for organization membership, invitations, and resource/action permissions grouped into roles, with `owner`, `admin`, and `member` as the starting vocabulary for new applications. This deliberately favors a future Better Auth adoption over numeric role ranks or a bespoke universal workspace model, while keeping application contracts independent of vendor types and storage encodings. The decision selects conventions, not an authentication-provider installation or a migration of existing applications.

## Consequences

- Preserve meaningful existing domain names and behavior until an explicit migration. An organization role is not automatically legal ownership, and a selected workspace is not proof of access.
- Keep branch/resource-scoped authorization application-owned. The documented team model groups members and uses organization permissions for team management; it does not document per-team role assignments, so treating teams as a branch-level authorization engine would be an unsupported assumption. Resolve and check the target resource's organization and scope, not only a role or client-selected identifier.
- Keep authentication/access integration separate from business-data repositories. Drizzle and direct Supabase access remain independent persistence choices; the accepted Supabase database-function approach to atomic repository operations remains unchanged. If Better Auth is adopted, delegate the behavior it owns to its supported APIs rather than maintaining two competing membership authorities.
- Treat compatibility as reduced migration work, not a drop-in switch. Better Auth's [Supabase migration guide](https://better-auth.com/docs/guides/supabase-migration-guide) uses a PostgreSQL connection, invalidates existing sessions, and leaves RLS and two-factor configuration migration outside its scope. Assess identity references, custom membership data, and Supabase token/RLS integration separately when adopting it; business repositories need not change solely because the auth adapter changes.

Version-sensitive APIs, schemas, and configuration remain owned by the matching official documentation, consistent with [ADR 0002](0002-keep-tool-specializations-thin-and-version-resolved.md).
