# Operations Slice

Use this slice for background jobs, outbox delivery, domain event records, webhooks, idempotency, retries, rate limiting, cron handlers, and side-effect timing.

## Choose the Mechanism

- Domain event log: immutable business history or audit record written with business state.
- Transactional outbox/job: reliable external delivery that must survive process failure.
- Post-response operation: best-effort, non-critical work that can be lost safely.
- Product analytics: typed behavioral measurement, best-effort unless an explicit reliable adapter uses the outbox.

Do not describe a documented design as production-ready until the consuming project proves migrations, workers, retry policy, idempotency, monitoring, and operational ownership.

## Outbox and Jobs

Persist the business change and outbox/job record in one database transaction. Dispatch only after commit. Workers must claim jobs safely, use bounded exponential backoff with jitter, classify retryable failures, and move exhausted jobs to an inspectable terminal state.

Every externally visible effect needs an idempotency key or provider-supported equivalent. Record attempts and final outcomes without placing secrets or unrestricted payloads in logs.

## Webhook Flow

```text
provider request
  -> raw-body + signature verification
  -> base event validation
  -> provider event registry
  -> event-specific validation + mapping
  -> framework-neutral handler/controller
  -> one use case
  -> atomic idempotency write + business changes
  -> standard response envelope
```

Verify signatures against the exact raw bytes before parsing or transforming the body. Keep provider SDK and event types at the provider adapter.

Use a unique database constraint with insert-on-conflict/upsert semantics for idempotency. Never use check-then-insert; concurrent deliveries can both pass the check.

Canonical unknown-event policy:

- acknowledge with HTTP 200;
- return `processed: false`;
- emit `webhook.skipped` with reason `unhandled_event_type`.

Invalid signatures or malformed supported payloads remain typed failures. Central error mapping owns the error envelope and status.

## Rate Limiting and Cron

Apply rate limiting in transport middleware using stable authenticated or trusted-network identifiers. Keep tier/limit policy behind a port, map exhaustion to the shared rate-limit error, and define provider-failure behavior explicitly.

Authenticate cron routes with a server-only secret or platform identity. Make each invocation idempotent, bound work, return the standard envelope, and obtain invocation/request correlation from active observability context.

## Event and Logging Ownership

Services own significant single-domain operational events. Use cases log only distinct workflow outcomes, not duplicate service events. Domain event tables and product analytics are separate from operational logs even when their names describe similar actions.

## Review Checklist

- Reliable side effects are transactionally enqueued.
- Workers have claim, retry, idempotency, terminal-state, and monitoring policies.
- Webhook verification precedes parsing and uses raw bytes.
- Webhook idempotency is atomic under concurrent delivery.
- Unsupported events use the canonical acknowledged-skip policy.
- Rate-limit and cron identities cannot be spoofed through untrusted headers.
- Side effects occur after commit unless they participate through the outbox.
- One layer owns each operational event.

## Derivation Sources

Derived from async jobs/outbox, event patterns, rate limiting, webhook architecture/testing, tRPC rate limiting, and Next.js cron guidance. Exact paths and fingerprints are maintained outside the portable skill package.
