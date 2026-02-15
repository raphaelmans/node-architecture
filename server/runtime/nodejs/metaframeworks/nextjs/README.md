# Next.js Server Documentation

> Next.js-specific conventions layered on top of the backend architecture.

This section focuses on how to implement **Next.js App Router** server concerns (`route.ts`, cache/revalidation, metadata/SEO, cron operations, and transport boundaries) while adhering to:

- The standard response envelope in [`server/core/api-response.md`](../../../../core/api-response.md)
- The error handling conventions in [`server/core/error-handling.md`](../../../../core/error-handling.md)

## Documents

| Document | Description |
| --- | --- |
| [Route Handlers](./route-handlers.md) | Patterns for non-tRPC `route.ts` handlers (response envelope + `requestId` + `handleError`) |
| [FormData Transport](./formdata-transport.md) | FormData transport conventions + `zod-form-data` for Next.js + tRPC |
| [Caching + Revalidation](./caching-revalidation.md) | `revalidate`, tagged cache, on-demand invalidation |
| [Metadata + SEO](./metadata-seo.md) | `generateMetadata`, `robots.ts`, `sitemap.ts` patterns |
| [Next Config Security](./next-config-security.md) | Security headers, CSP/HSTS, redirects and rewrites |
| [Cron Routes](./cron-routes.md) | Authenticated cron endpoint conventions and failure handling |
