# Next.js Server Documentation

> Next.js-specific conventions layered on top of the backend architecture.

This section focuses on how to implement **Next.js App Router** server concerns (`route.ts`, cache/revalidation, metadata/SEO, cron operations, and transport boundaries) while adhering to:

- The shared Zod contract boundary in [`server/core/api-contracts-zod-first.md`](../../../../core/api-contracts-zod-first.md)
- The standard response envelope in [`server/core/api-response.md`](../../../../core/api-response.md)
- The error handling conventions in [`server/core/error-handling.md`](../../../../core/error-handling.md)
- The request/trace boundary in [`server/core/observability.md`](../../../../core/observability.md)
- The dependency-injection and layer rules in [`server/core/conventions.md`](../../../../core/conventions.md)
- The configuration lifecycle rules in [`server/core/configuration.md`](../../../../core/configuration.md)
- The framework-neutral controller boundary in [`server/core/controllers.md`](../../../../core/controllers.md)
- The transaction boundary in [`server/core/transaction.md`](../../../../core/transaction.md)
- The testing pattern in [`server/core/testing-service-layer.md`](../../../../core/testing-service-layer.md)

```text
app/api/**/route.ts
  -> shared input contract
  -> factory-created framework-neutral controller
  -> service OR use case
  -> shared response contract
  -> NextResponse
```

Next.js owns the request lifecycle and response adapter. It never becomes the controller or replaces the controller/use-case/service/repository flow.

## Documents

| Document | Description |
| --- | --- |
| [Scaffolding](./scaffolding.md) | Next.js implementation of the portable server capability adapter contract |
| [Route Handlers](./route-handlers.md) | Patterns for non-tRPC `route.ts` handlers (response envelope + `requestId` + `handleError`) |
| [FormData Transport](./formdata-transport.md) | FormData transport conventions + `zod-form-data` for Next.js + tRPC |
| [Caching + Revalidation](./caching-revalidation.md) | `revalidate`, tagged cache, on-demand invalidation |
| [Environment Configuration](./environment-variables.md) | Private-build/server-runtime surfaces, T3 Env adaptation, lifecycle validation, injection, and tests |
| [Metadata + SEO](./metadata-seo.md) | `generateMetadata`, `robots.ts`, `sitemap.ts` patterns |
| [Next Config Security](./next-config-security.md) | Security headers, CSP/HSTS, redirects and rewrites |
| [Cron Routes](./cron-routes.md) | Authenticated cron endpoint conventions and failure handling |

## Official Next.js References

- [Route Handlers](https://nextjs.org/docs/app/api-reference/file-conventions/route)
- [Proxy](https://nextjs.org/docs/app/api-reference/file-conventions/proxy)
- [`after`](https://nextjs.org/docs/app/api-reference/functions/after)
