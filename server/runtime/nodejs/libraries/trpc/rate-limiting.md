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
- resolves identifier (`userId` fallback strategy)
- throws `TOO_MANY_REQUESTS` via structured error

Pattern:

```ts
export function createRateLimitMiddleware(tier: RateLimitTier) {
  return middleware(async ({ ctx, next }) => {
    const identifier = ctx.userId ?? ctx.requestId;
    const result = await getRateLimiter(tier).limit(identifier);

    if (!result.success) {
      throw new TRPCError({
        code: "TOO_MANY_REQUESTS",
        message: "Rate limit exceeded. Please try again later.",
      });
    }

    return next();
  });
}
```

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

