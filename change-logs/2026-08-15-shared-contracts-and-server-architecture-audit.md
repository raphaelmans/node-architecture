# 2026-08-15: Framework-Neutral Server Architecture and Shared Contracts

## Summary

Established one cohesive, framework-neutral server architecture from kernel contracts through Node.js runtime infrastructure and inbound framework adapters. Sharpened the same-repository client/server contract boundary and made Next.js, Express, Hono, tRPC, and OpenAPI peers at the outer edge rather than part of application logic.

Canonical flow:

```text
framework adapter -> framework-neutral controller
  -> service -> repository/provider
  OR
  -> use case -> service(s) -> repository/provider(s)
```

## Core Decisions

- Module-owned public input/response payload schemas live in `src/lib/modules/<module>/shared/contracts/` and are imported by both client and server.
- Universal response/pagination envelopes remain in `shared/kernel/`; module response schemas validate the payload under `data`.
- Server-only command DTOs are optional and are never imported by client code.
- The kernel contains transport-neutral ports and semantic `AppError.kind` values; HTTP and tRPC codes are mapped once in transport infrastructure.
- Every public framework adapter invokes one capability controller. The controller maps the public boundary and invokes one service or one use case. Cross-service work, external side effects, and delivery policy belong in a use case.
- Controllers are plain TypeScript capability boundaries. They receive shared-contract inputs and plain application types—not framework requests, responses, contexts, service locators, transactions, or tracing bags.
- Framework adapters own request extraction, authentication, rate limiting, input validation, request observability setup, response serialization, and central transport-error integration.
- Required delivery intent is persisted transactionally through an outbox. Best-effort post-commit work is caught and logged.

## Observability, Logging, and Transactions

- `TransactionContext` contains only the active database transaction. It never carries request, actor, logger, analytics, or tracing state.
- `requestId` identifies one application request/job for operational lookup. OpenTelemetry owns `traceId` and `spanId` for distributed causal correlation.
- Request/trace state propagates separately through the runtime's active async observability scope rather than ordinary method parameters.
- `AppLogger` is a DI port for operational diagnostics. The concrete Node.js logger enriches records from the active observability scope.
- `ProductAnalytics` is a separate typed DI port for behavioral events. Vendor fan-out uses adapter/composite patterns instead of embedding analytics vendors in the logger.
- OpenTelemetry semantic conventions drive span names and standard attributes. Application-specific attributes use one stable custom namespace and a low-cardinality `code.layer` classification.

## Runtime and Framework Alignment

- Added an explicit core -> Node.js runtime -> library/framework-adapter dependency direction.
- Added a Node.js Pino adapter guide while preserving `AppLogger` as the core contract.
- Standardized tRPC error middleware around central `AppError.kind` mapping and safe formatting.
- Strengthened the OpenAPI adapter and parity-test checklists.
- Standardized plain TypeScript controllers as a required boundary between Next.js, Express, Hono, tRPC, OpenAPI, and application logic.
- Updated Supabase guidance to keep provider models inside adapters, branch on provider error codes, use request-scoped factories, and model multi-system writes as compensating workflows.

### Inbound Adapter Matrix

| Adapter | Status | Framework-owned concerns |
| --- | --- | --- |
| Next.js App Router | Supported | `Request`, `NextResponse`, route lifecycle, framework caching, cookies, and central HTTP mapping |
| Express | Optional documented pattern | `Request`/`Response`, middleware order, request scope, route registration, and error middleware |
| Hono | Optional documented pattern | Hono `Context`, middleware variables, validator integration, `c.json()`, and `app.onError()` |
| tRPC | Supported transport | Procedure/context mechanics, middleware, formatter, and transport error mapping |
| OpenAPI/REST | Supported migration/coexistence path | HTTP method/path/status, schema publication, and transport parity |
| NestJS | Placeholder | Must inherit the same controller boundary when a canonical adapter guide is added |

## Testing Alignment

- Shared contract schemas have one canonical contract test suite.
- Framework-adapter tests cover envelope/payload integration, central error mapping, auth/rate-limit boundaries, and one controller call.
- Controller tests cover public input/actor mapping, one use-case-or-service call, null-to-domain-error behavior, and public response mapping.
- Use-case tests cover orchestration, transactions, outbox/side-effect timing, compensation, and injected telemetry ports.
- Service and repository tests remain transport-independent.

Canonical split:

```text
adapter test      -> stub controller; assert framework integration
controller test   -> stub service/use case; assert public mapping
use-case test     -> fake/stub ports; assert orchestration and transaction behavior
service test      -> fake/stub repository; assert domain policy
repository test   -> real test database where persistence behavior matters
```

## Documentation and Interactive Artifacts

- Added `server/core/controllers.md` as the canonical controller boundary guide.
- Added dedicated Express and Hono adapter guides and linked them from the server/runtime indexes and consumer guide-selection checklist.
- Updated core contracts, conventions, logging, testing, runtime, and folder-structure documentation to treat framework entrypoints as replaceable options.
- Added `assets/server-architecture-guide.html` as the standalone interactive server companion.
- Added one compact simple-read slice with expandable Next.js, Express, and Hono adapters over the same controller, service, repository, and factory.
- Added a matching controller test snippet so the visual guide shows both production and test boundaries.
- Added the standalone client and server HTML guides to the root/consumer navigation and included `assets/` in the downstream `copy-guides.sh` bundle.

## Distribution and Adoption

- `consumer/AGENTS-MD-ALIGNMENT.md` now selects Next.js, Express, and Hono server guides independently according to the consuming project's stack.
- A consuming project chooses its framework entrypoint folder; the inward `lib/shared/` and `lib/modules/` structure remains stable.
- Legacy server documentation remains historical reference only and does not override the canonical core/runtime guides.

## Post-Audit Coherence Hardening

A complete follow-up review of all `server/` guides corrected the remaining
places where copyable examples disagreed with the core decisions.

### Security and Provider Boundaries

- User/session-scoped Supabase clients now use the publishable key; the secret
  key is confined to separately named privileged/admin factories.
- Supabase Auth and Storage adapters translate provider failures to typed
  application errors instead of leaking raw vendor errors across the port.
- tRPC context creation now receives a module-owned `SessionResolver`; shared
  transport infrastructure no longer constructs Supabase clients or resolves a
  module repository directly, and infrastructure outages are not swallowed as
  anonymous sessions.
- OAuth and PKCE route examples invoke framework-neutral controllers and derive
  redirects from a validated application origin rather than forwarded host
  headers.
- Pino and manual sanitization guidance now covers nested authorization,
  cookie, token, API-key, and secret shapes with regression tests and an
  allowlist-first logging rule.

### Correctness and Concurrency

- Removed the generic PostgreSQL `23505` UUID retry pattern. Known uniqueness
  conflicts are translated by exact constraint name; unexpected UUID
  collisions fail once rather than being retried inside an aborted transaction.
- Webhook idempotency now requires an atomic unique constraint/upsert or
  insert-on-conflict operation. Check-then-insert is explicitly forbidden for
  concurrent deliveries.
- Unsupported webhook event types have one canonical policy: acknowledge with
  HTTP 200, return `processed: false`, and emit a structured skip record.
- Webhook handler wiring, response-schema ownership, central HTTP error mapping,
  provider folder paths, and fixture layouts were corrected and unified.
- `TransactionContext` is now an opaque branded kernel type; only transaction
  infrastructure and repositories bridge it to a concrete Drizzle transaction.

### Cross-Framework and Contract Parity

- Express and Hono validation examples normalize Zod failures to the shared
  `ValidationError` so every transport reaches the canonical error envelope.
- Copyable core and Next.js controller examples use the same request-body and
  schema-normalization helpers; no inbound example leaks a raw parser error.
- tRPC documentation now has one inline authentication/authorization
  middleware implementation, preserves domain errors as causes, and routes
  logout/current-session capabilities through controllers.
- Procedure tests using `createCaller` are explicitly separated from real HTTP
  adapter integration tests; only the latter claim coverage of context,
  observability, raw parsing, and serialized error formatting.
- All runtime folder examples now follow `src/lib/shared` and
  `src/lib/modules`; capability response schemas validate payloads while the
  kernel owns envelopes.
- Numeric pagination is consistently named `offset`/`nextOffset`; true cursors
  are reserved for opaque, stable traversal keys.
- Cron response examples now use the standard success envelope and rely on
  contextual request/invocation correlation.

### Observability and Framework Currency

- Operational event ownership is explicit: services own single-domain events,
  while use cases log only distinct workflow events. Duplicate `user.created`
  records were removed.
- Contextual `user.id` is reserved for the authenticated actor; target users
  use the namespaced `com.example.api.target.user.id` attribute.
- Trace correlation is runtime-owned, while callers supply stable
  `otel.event.name` and `code.function.name` values such as
  `AuthConfirmRoute.GET` or `UserService.create`.
- The core observability primitive accepts plain context values and a minimal
  header reader; Fetch, Express, and Hono request types remain adapter details.
- Next.js caching now distinguishes the Cache Components model from the
  previous `unstable_cache` model and uses the current
  `revalidateTag(tag, "max")`/`updateTag` guidance.
- Event-driven patterns are described as canonical designs whose production
  readiness must be demonstrated in each consuming project, rather than being
  declared implemented by documentation alone.
- The standalone server HTML now uses the same normalized Next.js, Express, and
  Hono validation snippets and distinguishes procedure tests from real HTTP
  adapter tests.

## Notes

- Documentation-only change.
- HTML structure/scripts, local documentation links, desktop/mobile layouts, and the downstream guide-copy bundle were validated during the original architecture update.
- The post-audit hardening pass validated all server Markdown links, code-fence
  balance, terminology scans, and whitespace integrity.

## Review Follow-up

- Hardened the OAuth callback against backslash-normalized open redirects by
  checking the final parsed origin, and converted code-exchange failures into a
  centrally logged, same-origin error redirect.
- Corrected the pagination examples so offset pagination uses a regular tRPC
  query; infinite queries now explicitly require an optional opaque `cursor`
  contract.
- Centralized sanitized Zod issue projection into `publicDetails`, preserving
  field-level 400 details without exposing raw validation objects.
- Added an explicit Hono status adapter so the shared numeric HTTP result is
  narrowed before it reaches `c.json()`.
