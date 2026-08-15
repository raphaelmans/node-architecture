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

## Notes

- Documentation-only change.
- HTML structure/scripts, local documentation links, desktop/mobile layouts, and the downstream guide-copy bundle were validated.
