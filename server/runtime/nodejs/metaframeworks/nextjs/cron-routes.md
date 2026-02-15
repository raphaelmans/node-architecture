# Cron Routes (Next.js)

> Conventions for scheduled jobs implemented as Next.js route handlers.

## Purpose

Standardize cron-triggered routes for safety, observability, and retry tolerance.

## Authentication

- Require explicit cron auth (shared secret/signature/header contract).
- Reject unauthorized requests early with clear 401/403 response.

## Idempotency + Safety

- Design handlers to be retry-safe.
- Process in bounded batches.
- Keep state transitions explicit (for example queued -> processing -> done).
- Use transactions for multi-step state changes.

## Response Contract

Return structured JSON containing:

- success flag
- processed count(s)
- timestamp
- optional per-item errors for partial failure cases

For non-cron public endpoints, continue using standard API envelope conventions.

## Logging

Log start/end and failure with:

- cron job name/event key
- processed counts
- requestId
- error details when applicable

## Runtime Notes

- Prefer `GET` for scheduler trigger endpoints unless payload is required.
- Use `export const dynamic = "force-dynamic"` when static optimization is undesirable.
- Keep cron schedule configuration close to deployment config documentation.

## Related Patterns

- Async job model: `../../../../core/async-jobs-outbox.md`
- Core rate-limiting contract (if cron endpoint is externally callable): `../../../../core/rate-limiting.md`

