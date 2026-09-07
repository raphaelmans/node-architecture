# Better Auth Integration Convention

Load only when Better Auth is present or selected. Read [runtimes](../runtimes.md) and [security](../security.md). Add [tenancy](../foundations/tenancy.md), [authorization](../security/authorization.md), and [RBAC](../security/rbac.md) for organization/resource access. Select [Drizzle](drizzle.md) only if used; [Supabase](supabase.md) is independent and unnecessary for Better Auth + Drizzle alone.

## Native Integration Boundary

- Better Auth owns authentication, sessions, and its native endpoints. Mount the documented framework handler under the configured auth boundary and preserve its status/body, redirects, cookies, and headers. Do not wrap native responses in the business envelope or regenerate provider endpoints as controllers.
- This provider-managed endpoint boundary does not exempt application-owned features from `adapter -> controller -> service/use case -> ports`. A custom business action remains an application capability even when it uses Better Auth.
- Derive body parsing, route matching, CORS, middleware ordering, and cookie behavior from the actual Next.js/Express/Hono or other runtime integration. Do not consume required bodies early, require a session for login, or disable origin/CSRF protections to make setup work.
- Supply narrow validated configuration, including trusted origins and callback destinations, from deployable composition. Apply safe logging/redaction without rewriting the native protocol.
- In Next.js, distinguish native handlers, RSC reads, and cookie-mutating Server Actions. Verify browser cookie propagation for in-process auth calls; layouts and cookie-existence checks cannot authorize protected application data.

## Session and Access Ports

- Implement the app's narrow session resolver using documented server verification. Extract current request credentials at the outer boundary, then map the verified result into a minimal plain actor with stable identity. Provider sessions, headers/cookies, and inferred database types stay out of application contracts.
- Return anonymous only for real absence/expiry; translate provider/database outages to typed unavailable/gateway errors. Native errors remain protocol-owned; errors crossing application ports are normalized.
- Reuse configured infrastructure only when it holds no request/user state. Never cache actors or cookie-bound results globally. Define session/cache freshness and revocation explicitly; current membership and resource authorization are separate checks.
- When the Organization plugin is selected, delegate its membership/invitation/role lifecycle to supported APIs rather than competing direct table writes. Keep branch/resource assignments application-owned and do not infer per-team roles from teams.
- Enforce required delegation, scope, and owner rules at every reachable lifecycle path, including native plugin APIs. Use supported configuration/hooks or resolve a restricted workflow design before exposing an endpoint that cannot enforce the policy. Application wrappers cannot secure a weaker native endpoint.
- Hooks adapt into focused application calls. Verify their timing, failure, and transaction guarantees; a precheck is not concurrency protection and an after-hook is not an atomic outbox.

## Persistence and Migration

- Select a supported auth-database adapter independently of business repositories. Better Auth + Drizzle needs no Supabase configuration or functions merely to authenticate and persist business data.
- Use selected auth configuration/plugins to generate the auth schema; review identity types, relations, and application foreign keys. Keep one migration owner per object and a coherent migration pipeline without overwriting business schema or duplicating history.
- Drizzle may manage migrations while Better Auth owns runtime auth/membership writes. Business repositories continue to return application-owned records.
- A shared database/client does not prove provider operations join an application transaction. Use documented participation or explicit idempotent recovery/compensation; prove atomicity before promising combined invitation, assignment, audit, or outbox writes.
- Existing-user migration is explicit work: identity references, credentials/providers, sessions, membership data, and recovery. Supabase migration requirements apply only if that provider is being replaced or retained.

## Client Boundary

Compose Better Auth's client as an auth-specific transport behind focused feature APIs. Do not feed native responses through the business envelope decoder or leak SDK errors/methods into components. Provider-reactive session hooks, if used, are projected through an integration hook with one session-state owner. React/Next.js access-control leaves own UX and private-cache invalidation on identity, organization, or grant changes; static client role checks are never server authority.

## Verify and Sources

Test real handler mounting, middleware interaction, cookies, redirects, rejected origins, session mapping/outages/revocation, simultaneous users, native plugin policy bypass, invitation replay, relevant concurrency, migrations, and cross-boundary workflow recovery. Also test application-route authorization and client cache isolation; mocked SDK calls do not establish these integration guarantees.

- [Installation](https://better-auth.com/docs/installation)
- [Drizzle adapter](https://better-auth.com/docs/adapters/drizzle)
- [Organization](https://better-auth.com/docs/plugins/organization)
- [Sessions](https://better-auth.com/docs/concepts/session-management)
- [Hooks](https://better-auth.com/docs/concepts/hooks)
- [Next.js](https://better-auth.com/docs/integrations/next), [Express](https://better-auth.com/docs/integrations/express), [Hono](https://better-auth.com/docs/integrations/hono)

Inspect installed versions and resolve exact package commands, imports, configuration, schema/migration syntax, handlers, and hook/transaction behavior from matching official docs. Loading this leaf does not authorize installation or migration beyond the user's requested scope.
