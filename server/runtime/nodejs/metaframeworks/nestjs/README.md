# NestJS Server Documentation (Adapter Placeholder)

NestJS is not yet a canonical implementation in this guide. When added, Nest route controllers are framework adapters and must adapt—not redefine—the [core architecture](../../../../core/README.md).

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
