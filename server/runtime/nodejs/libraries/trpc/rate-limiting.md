# tRPC Rate Limiting (Node.js Runtime)

> Middleware-based rate limiting conventions for `@trpc/server`.

## Scope

This document defines runtime implementation patterns for the core contract:

- `server/core/rate-limiting.md`

## Tier Configuration

Define named tiers in one module:

```ts
export const RATE_LIMIT_TIERS = {
  default: { requests: 100, window: "1 m" as const },
  auth: { requests: 10, window: "1 m" as const },
  mutation: { requests: 30, window: "1 m" as const },
  sensitive: { requests: 5, window: "1 m" as const },
} as const;
```

## Middleware Factory

Use a middleware factory that:

- resolves limiter by tier
- resolves a stable authenticated or trusted anonymous subject
- throws the transport-neutral `RateLimitError`; shared tRPC middleware maps it to `TOO_MANY_REQUESTS`

Pattern:

```ts
export function createRateLimitMiddleware(tier: RateLimitTier) {
  return middleware(async ({ ctx, next }) => {
    const subject = resolveRateLimitSubject({
      userId: ctx.userId,
      clientIdentifier: ctx.clientIdentifier,
      clientIdentifierSource: ctx.clientIdentifierSource,
    });
    const result = await getRateLimiter(tier).limit(subject.key);

    if (!result.success) {
      throw new RateLimitError("Rate limit exceeded. Please try again later.");
    }

    return next();
  });
}
```

`resolveRateLimitSubject` must not fall back to `requestId`. Only trust forwarded IP headers after deployment-specific proxy validation. Log the subject source/class and quota result; do not log raw credentials.

The limiter adapter must implement the system's documented fail-open/fail-closed policy for infrastructure errors. Do not accidentally turn a limiter timeout into an unclassified raw response.

## Tests

- Repeated requests from one authenticated user resolve the same key.
- Repeated anonymous requests behind the trusted proxy resolve the same key.
- A new `requestId` does not change the key.
- Untrusted forwarded headers are ignored.
- Missing stable identity follows the configured coarse-bucket/reject policy.
- Limiter infrastructure failure follows the configured fail-open/fail-closed policy.

## Procedure Factories

Expose tiered procedure helpers instead of repeating middleware wiring:

```ts
export const rateLimitedProcedure = (tier: RateLimitTier) =>
  publicProcedure.use(createRateLimitMiddleware(tier));

export const protectedRateLimitedProcedure = (tier: RateLimitTier) =>
  protectedProcedure.use(createRateLimitMiddleware(tier));
```

## Placement Rules

- Apply limits in router/procedure definitions.
- Do not perform limit checks in services/use-cases.
- Keep all tier names centralized.

## Related Docs

- `./integration.md`
- `../../metaframeworks/nextjs/formdata-transport.md`
- `../../metaframeworks/nextjs/cron-routes.md`
