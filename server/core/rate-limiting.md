# Rate Limiting (Core Contract)

> Agnostic conventions for request throttling across transports.

## Purpose

Rate limiting protects reliability and abuse-sensitive endpoints by enforcing request quotas before business logic runs.

## Boundary Rules

- Enforce limits at transport boundaries (HTTP/tRPC middleware), not in services/repositories.
- Keep limit logic deterministic and observable (tier, identifier class, remaining quota).
- Return a consistent 429 error contract.

## Tier Model

Use named tiers instead of inline numeric limits so policies are reusable.

Suggested baseline tiers:

- `default` for standard reads
- `auth` for login/verification operations
- `mutation` for write-heavy operations
- `sensitive` for abuse-prone operations

Actual quota values are runtime/provider decisions.

## Identifier Strategy

Use stable identifiers in this order:

1. Authenticated `userId` when available
2. Network identifier (for example IP) for anonymous traffic
3. Request-level fallback (`requestId`) when no stronger identifier exists

## Error Contract

On limit exceeded, return `429` with standard error envelope:

```json
{
  "code": "TOO_MANY_REQUESTS",
  "message": "Rate limit exceeded. Please try again later.",
  "requestId": "req-abc-123"
}
```

Include `requestId` for correlation.

## Logging + Telemetry

At minimum, log:

- `tier`
- identifier class (`user` / `anonymous`)
- `limit`
- `remaining`
- `requestId`

## Failure Mode

Define and document one runtime policy:

- fail-open (allow requests when limiter infra is unavailable), or
- fail-closed (reject requests when limiter infra is unavailable)

Choose once per system and apply consistently.

## Runtime Implementations

- tRPC middleware pattern: `server/runtime/nodejs/libraries/trpc/rate-limiting.md`
- Next.js route enforcement for cron/public routes: `server/runtime/nodejs/metaframeworks/nextjs/cron-routes.md`

