# Node.js Web Framework Adapter Documentation

Framework-specific server guidance layered on top of `server/core/` and `server/runtime/nodejs/libraries/`. The directory name is retained for compatibility, but it includes both frameworks and metaframeworks.

| Framework | Status | Guide | Scaffolding |
| --- | --- | --- | --- |
| Next.js App Router | Documented specialization | [Next.js](./nextjs/README.md) | [Guide](./nextjs/scaffolding.md) |
| Express | Documented specialization | [Express](./express/README.md) | [Guide](./express/scaffolding.md) |
| Hono | Documented specialization | [Hono](./hono/README.md) | [Guide](./hono/scaffolding.md) |
| NestJS | Documented configuration + adapter specialization | [NestJS](./nestjs/README.md) | Derive route scaffolding from current evidence |

Framework entrypoints translate requests/responses, establish runtime scope, and call one module-owned framework-neutral controller. They do not call use cases/services directly or own business rules, vendor construction, or database transactions.

An unlisted Node.js framework is not unsupported. Apply the core and Node.js scaffolding guides, then derive the adapter from repository conventions and version-applicable official documentation.
