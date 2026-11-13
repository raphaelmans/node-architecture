# Better Auth Integration Convention

Use when Better Auth is installed or explicitly selected. Apply the [controller boundary](../../../../core/controllers.md), session/security rules, and the selected runtime mapping. Add [tenancy](../../../../core/tenancy.md) and [RBAC](../../../../core/rbac.md) only when the Organization plugin is needed. Better Auth does not require Supabase or Drizzle; select a supported auth-database adapter independently of business persistence.

## Ownership

| Concern | Owner |
| --- | --- |
| Authentication, credentials, sessions, native auth endpoints | Better Auth integration |
| Organization/member/invitation lifecycle when selected | Better Auth Organization plugin through its supported APIs |
| Business operations and resource/branch authorization | Application services/use cases and focused access ports |
| Business records and queries | Application-owned repositories with selected persistence adapters |
| Runtime configuration, handler mounting, cookies, request context | Deployable composition and framework adapters |

Reuse the provider's supported behavior rather than implementing a competing auth engine. Keep SDK objects, inferred provider schemas, and transport context out of application contracts. Do not invent wrappers for every provider endpoint; introduce focused app-facing interfaces only where application behavior consumes that capability.

## Native Routes and Application Routes

Mount Better Auth's documented framework handler under its configured auth route boundary. Preserve native status codes, bodies, redirects, cookies, and headers; do not wrap it in the application's JSON envelope or regenerate all native endpoints as controllers. This is the narrow [provider-managed endpoint boundary](../../../../core/controllers.md#provider-managed-endpoints), not permission for business routes to bypass controllers or authorization.

Keep routing, body parsing, CORS, cookies, and middleware ordering compatible with the detected Next.js, Express, Hono, or other runtime. Do not consume the body before a handler that requires it, make login require an existing session, or disable origin/CSRF protections to resolve integration problems. Configure trusted origins and callback destinations from validated application configuration; never trust arbitrary request hosts. Apply the application's safe observability/redaction policy without rewriting the provider protocol.

For Next.js, distinguish native handler mounting, authenticated RSC reads, and cookie-mutating Server Actions. Derive supported cookie propagation from current docs; an in-process auth call does not by itself guarantee the browser receives updated cookies. Protect application data before rendering or serialization, even if a layout or early route gate already checked a cookie.

## Session-to-Actor Boundary

Implement the application's narrow session resolver using Better Auth's documented server verification API. Resolve credentials from the current request at the outer boundary and map a verified session to a minimal plain actor with a stable application identity. Cookie existence, submitted user IDs, or a client session object are not verification.

Return anonymous only for genuine absence/expiry; map provider/database failures to typed unavailable/gateway errors. Translate errors when they cross into application ports, while leaving native handler error responses under the provider protocol. Reuse the configured auth instance only if it captures no per-user/request state; never cache an actor or cookie-bound result globally.

Choose an explicit session freshness/revocation policy, including any provider cookie cache. Current membership and resource authorization remain separate from session validity. Active organization/team selection is context, not an access grant.

## Organization Policy and Lifecycle

When selected, let Better Auth own organization memberships, invitations, and organization roles. Business repositories must not independently mutate those provider-owned records. Normalize role collections and permission results into app-facing values; use current server-backed decisions for dynamic roles and resource policy.

The application's branch/resource assignments remain separate extensions, not assumed team roles. Use the existing authorization/RBAC rules for scope, delegation ceilings, and owner preservation. Enforce required restrictions through supported provider configuration/hooks at every exposed lifecycle entrypoint, including direct native API calls; a stricter application wrapper alone cannot secure a weaker native endpoint. If the provider cannot enforce a required invariant, resolve the exposure/workflow design before shipping it rather than silently weakening the rule.

Hooks adapt provider events into focused application calls. Check the selected hook's timing, failure, and transaction guarantees before using it for invariants or side effects. Do not treat a hook name as proof that its work is atomic with the provider mutation, or assume a precheck protects a concurrent change.

## Drizzle and Migration Ownership

For Better Auth + Drizzle, compose the supported auth adapter with a compatible Drizzle client/schema, and use the independent [Drizzle convention](../drizzle/README.md) for business repositories. No Supabase clients, keys, RLS integration, or database functions are required merely for this stack.

Treat the selected Better Auth configuration/plugins as the input to auth schema generation. Review the generated schema alongside application tables, identity types, relations, and foreign keys, then use one coherent migration pipeline with one owner per schema object. Regeneration must not overwrite business schema changes or create duplicate migration histories. Runtime semantics remain provider-owned even if Drizzle manages schema migrations.

Sharing a database or client does not prove Better Auth operations join an application's Drizzle transaction. Use only documented transaction participation when available. Otherwise design an explicit idempotent workflow with recovery/compensation and appropriately durable delivery; do not claim atomic acceptance plus custom assignments/audit/outbox writes without proving it. A generic after-hook is not an atomic outbox.

For existing-user adoption, explicitly plan identity references, session replacement, credentials, enabled providers/plugins, memberships, and rollback/recovery. Supabase migration concerns apply only when moving from or retaining Supabase services; a new Better Auth + Drizzle app needs no Supabase migration layer.

## Client Integration

Compose the configured Better Auth client as an auth-specific transport behind focused feature APIs; preserve its native protocol rather than passing its responses through the business API envelope decoder. Keep SDK methods/errors out of presentation components. If using provider-reactive session hooks, project them through an integration hook into app-facing state and choose one session-state owner instead of duplicating it in competing caches.

React and Next.js access-control leaves still own scoped permission UX. Invalidate application access/data caches on login, logout, organization changes, and membership/role updates. Client role checks remain display hints, not permission to execute a protected business operation.

## Verification and Sources

Test the real mounted handler for login/logout, cookie propagation, redirects, rejected origins, and interaction with middleware. Test the session resolver for missing/expired/revoked sessions, provider outage, identity mapping, and simultaneous users. Test native organization endpoints for direct-call policy bypass, role edits, ownership changes, invitation replay, and relevant concurrency. Verify migration generation on a disposable database and failure/recovery behavior for workflows crossing provider and application writes. Add normal application-route authorization and client cache-isolation tests; mocked provider calls alone do not prove integration.

- [Better Auth installation](https://better-auth.com/docs/installation)
- [Drizzle adapter](https://better-auth.com/docs/adapters/drizzle)
- [Organization plugin](https://better-auth.com/docs/plugins/organization)
- [Session management](https://better-auth.com/docs/concepts/session-management)
- [Hooks](https://better-auth.com/docs/concepts/hooks)
- [Next.js integration](https://better-auth.com/docs/integrations/next)
- [Express integration](https://better-auth.com/docs/integrations/express)
- [Hono integration](https://better-auth.com/docs/integrations/hono)

Detect the actual Better Auth, database adapter, Drizzle/driver, framework, and plugin versions. Retrieve matching official docs for installation commands, imports, configuration, schema generation, migrations, handler APIs, and hook/transaction guarantees. This guide records our approach, not frozen vendor setup instructions.
