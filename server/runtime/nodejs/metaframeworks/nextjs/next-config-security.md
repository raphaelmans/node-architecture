# Next Config Security (Next.js)

> Security and routing conventions for `next.config.*`.

## Security Headers Baseline

Define a shared header set and apply to `/(.*)`:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy`
- `Permissions-Policy`
- `Cross-Origin-Opener-Policy`
- `Cross-Origin-Resource-Policy`

Production-only additions:

- `Strict-Transport-Security` (HSTS)
- `Content-Security-Policy` (CSP)

## CSP Guidance

- Keep CSP centralized in config.
- Start strict and expand only required origins.
- Revisit `unsafe-inline` / `unsafe-eval` usage regularly.

## Redirects and Rewrites

- Use redirects for canonical path migrations.
- Use rewrites for compatibility aliasing/internal route mapping.
- Keep rewrite/redirect intent documented per rule.

## Image and Asset Controls

- Explicitly constrain `images.remotePatterns`.
- Set sensible cache TTL for remote images.

## Environment Gating

- Security policy can differ by environment, but defaults must be safe.
- Do not disable critical security headers in production.

