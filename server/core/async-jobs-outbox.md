# Async Jobs + Outbox (Core Pattern)

> Canonical pattern for reliable background delivery side effects.

## Purpose

When write operations trigger external side effects (email, SMS, push, webhooks, important product analytics events), use an outbox job model to keep business writes and background delivery consistent.

## Core Rule

Write domain data and enqueue job records in the **same transaction**.

This guarantees:

- no side effect without domain write
- no domain write without a queued delivery intent

## Job States

Use an explicit state machine:

- `PENDING` — queued and ready
- `SENDING` — claimed by dispatcher
- `SENT` — delivered successfully
- `FAILED` — delivery failed; may retry
- `SKIPPED` — invalid target/payload or intentionally not deliverable

## Retry Contract

- Keep `attemptCount`
- Apply bounded retries with backoff
- Persist next-attempt scheduling metadata
- Stop retrying once attempts are exhausted

## Idempotency Contract

Each job must carry an `idempotencyKey` derived from:

- event type
- entity/event identifier
- recipient identity
- channel

The key must be unique for equivalent delivery attempts to prevent duplicates.

## Dispatcher Rules

- Claim jobs transactionally (`PENDING`/retryable `FAILED` -> `SENDING`)
- Mark terminal states explicitly (`SENT` / exhausted `FAILED` / `SKIPPED`)
- Give each worker invocation its own request/invocation ID
- Persist an optional `causationRequestId` for the originating request and standard trace carrier metadata where supported
- Include job ID and provider message ID in operational records
- Never reuse a producer `spanId` as the worker's active span

## Ownership and Boundaries

- Use case decides **what cross-service event to enqueue**; a single-domain service may write an event owned entirely by that same module
- Dispatcher decides **how/when to deliver**
- Transport/metaframework layer decides **how dispatchers are triggered** (cron, worker, queue consumer)
- Product analytics dispatchers depend on `ProductAnalytics`; they do not repurpose `AppLogger`

For Next.js cron-triggered dispatch patterns, see:

- `server/runtime/nodejs/metaframeworks/nextjs/cron-routes.md`

For correlation semantics across producer/consumer boundaries, see [Observability](./observability.md#async-and-queue-boundaries).
