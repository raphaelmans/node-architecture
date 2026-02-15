# Async Jobs + Outbox (Core Pattern)

> Canonical pattern for reliable background delivery side effects.

## Purpose

When write operations trigger external side effects (email, SMS, push, webhooks), use an outbox job model to keep business writes and background delivery consistent.

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
- Include correlation metadata (`requestId`, job id, provider message id if available)

## Ownership and Boundaries

- Use case/service layer decides **what event to enqueue**
- Dispatcher decides **how/when to deliver**
- Transport/metaframework layer decides **how dispatchers are triggered** (cron, worker, queue consumer)

For Next.js cron-triggered dispatch patterns, see:

- `server/runtime/nodejs/metaframeworks/nextjs/cron-routes.md`

