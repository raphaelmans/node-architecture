# Telemetry Slice

Use this slice for dependency-injected operational logging, Pino adapters, OpenTelemetry correlation, request and trace identifiers, event/function naming, product analytics, privacy, and telemetry tests.

## Separate the Concerns

| Concern | Port | Purpose |
| --- | --- | --- |
| Operational logs | `AppLogger` | debugging, failures, lifecycle, operational events |
| Distributed traces | OpenTelemetry/runtime context | cross-service causality and latency |
| Product analytics | `ProductAnalytics` | typed user/business behavior |
| Transactions | `TransactionContext` | database atomicity only |

Do not combine these into a telemetry service locator or generic execution context. A composite analytics adapter may fan one typed product event to multiple vendors; the operational logger remains separate.

## Logger Dependency Injection

Define a vendor-neutral logger port in the kernel and implement it with Pino or another runtime adapter. Inject `AppLogger` into the service/use case that owns an event. Repositories generally do not log; central error handling owns provider/database failures.

The adapter reads active request and trace context. Callers supply event-specific safe fields only:

```ts
log.info(
  {
    "otel.event.name": "user.created",
    "code.function.name": "UserService.create",
    [APP_ATTRIBUTES.targetUserId]: user.id,
  },
  "User created",
);
```

Use contextual `user.id` for the authenticated actor. Use a namespaced target attribute for another user/entity.

## Correlation

- `requestId`: one application request/invocation identifier generated or accepted at a trusted transport boundary.
- `traceId`: one distributed trace spanning related service/process operations and owned by OpenTelemetry.
- `spanId`: one operation inside the trace.

Establish context once with a framework-neutral primitive and thin Fetch, Express, Hono, worker, or queue adapters. Do not add request/trace IDs to business DTOs, controllers, transaction options, or logger method parameters.

## Naming

- Operational event: stable past-tense dotted name in `otel.event.name`, such as `user.created` or `webhook.skipped`.
- Function: stable owner and method in `code.function.name`, such as `UserService.create`, `CreateUserUseCase.execute`, or `AuthConfirmRoute.GET`.
- Application attributes: registered reverse-domain namespace, such as `com.example.api.*`.
- Dynamic identifiers belong in fields, never event names.

Services own single-domain events. Use cases emit only distinct orchestration outcomes. Transport middleware owns request lifecycle records. Avoid duplicate logs for one occurrence.

## Product Analytics

Use a typed event union/registry and inject `ProductAnalytics` into the owning workflow. Emit completion events only after success. Keep consent, identity, batching, retry, vendor mapping, and fan-out in adapters.

Best-effort analytics failures must not alter business behavior. Route analytics through an outbox only when delivery is an explicit reliable business requirement.

## Redaction and Failure Safety

Use allowlist-first fields and recursive sanitization. Configure Pino redaction for nested authorization, cookies, tokens, API keys, and secret shapes. Never log raw request bodies, unrestricted DTOs/entities, SQL/provider diagnostics in public fields, or unapproved personal data.

Logging and analytics adapters must not throw into business behavior. Preserve internal causes for diagnostics while keeping serialized public errors safe.

## Review Checklist

- Logger and analytics ports are separate and injected narrowly.
- Runtime context supplies correlation automatically.
- Event and function names are stable and consistently namespaced.
- Actor and target identifiers are not conflated.
- One boundary records each occurrence.
- Redaction occurs before every sink/fan-out.
- Telemetry failures cannot change the business result.
- Tests assert app-facing records/events, not Pino or vendor formatting.

## Derivation Sources

Derived from logging, observability, product analytics, event patterns, and Pino runtime guidance. Exact paths and fingerprints are maintained outside the portable skill package.
