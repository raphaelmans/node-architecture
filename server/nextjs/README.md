# Next.js Server Documentation

> Next.js-specific conventions layered on top of the backend architecture.

This section focuses on how to implement **Next.js App Router** server endpoints (especially `app/api/**/route.ts`) while adhering to:

- The standard response envelope in `server/core/api-response.md`
- The error handling conventions in `server/core/error-handling.md`

## Documents

| Document | Description |
| --- | --- |
| [Route Handlers](./route-handlers.md) | Patterns for non-tRPC `route.ts` handlers (response envelope + `requestId` + `handleError`) |
