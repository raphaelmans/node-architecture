# NestJS Server Documentation

NestJS is a framework specialization over the [core architecture](../../../../core/README.md). Nest route controllers and modules adapt—not redefine—the framework-neutral application boundary.

## Guides

- [Configuration and dependency injection](./configuration.md)

A NestJS adapter must:

- validate with module-owned shared Zod contracts;
- establish request/trace scope in middleware/interceptors;
- call one framework-neutral capability controller from the thin Nest route controller;
- map `AppError.kind` centrally in an exception filter;
- return the shared success/error envelopes;
- keep `TransactionContext` out of request-scoped transport objects;
- preserve manual/interface-driven application boundaries even if Nest owns construction;
- add framework-adapter tests plus framework-neutral-controller/shared-contract/service/use-case tests.

Nest-only modules, providers, guards, interceptors, and exception filters belong here. Kernel and domain rules remain in `server/core/`.
