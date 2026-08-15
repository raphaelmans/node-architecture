# Node.js Web Framework Adapter Documentation

Framework-specific server guidance layered on top of `server/core/` and `server/runtime/nodejs/libraries/`. The directory name is retained for compatibility, but it includes both frameworks and metaframeworks.

| Framework | Status | Guide |
| --- | --- | --- |
| Next.js App Router | Canonical/supported | [Next.js](./nextjs/README.md) |
| Express | Optional adapter pattern | [Express](./express/README.md) |
| Hono | Optional adapter pattern | [Hono](./hono/README.md) |
| NestJS | Placeholder adapter checklist | [NestJS](./nestjs/README.md) |

Framework entrypoints translate requests/responses, establish runtime scope, and call one module-owned framework-neutral controller. They do not call use cases/services directly or own business rules, vendor construction, or database transactions.
