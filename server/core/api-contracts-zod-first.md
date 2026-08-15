# API Contracts: Zod-First (tRPC Now, OpenAPI Ready)

> Canonical contract strategy for transport coexistence and migration.

## Purpose

Keep domain and service code transport-agnostic while supporting:

- tRPC as the current transport
- OpenAPI as a migration/parallel transport target

## Source of Truth

`Zod` schemas are the single source of truth for request/response contracts.

- Define each wire contract once in an isomorphic shared module
- Derive TypeScript types from schema inference
- Reuse the same schemas in the client and every enabled transport adapter
- Never hand-maintain a second client copy of a server contract

## Canonical Location

Module-owned contracts that cross the client/server boundary live here:

```text
src/lib/modules/<module>/shared/contracts/
  <capability>.contract.ts
  index.ts
```

Example:

```typescript
// src/lib/modules/user/shared/contracts/create-user.contract.ts

import { z } from "zod";

export const CreateUserInputSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
});

export type CreateUserInput = z.infer<typeof CreateUserInputSchema>;

export const CreateUserResponseSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string(),
  createdAt: z.string().datetime(),
});

export type CreateUserResponse = z.infer<typeof CreateUserResponseSchema>;
```

Application-wide transport primitives such as response envelopes and pagination remain in `src/lib/shared/kernel/`. Do not move a module-owned contract into the kernel merely because both client and server use it.

### Payload vs Envelope

`<Capability>ResponseSchema` validates the capability payload carried in `ApiResponse.data`; it does not redefine the universal envelope. The full success body is the composition of:

```text
kernel ApiResponse envelope + module CapabilityResponse payload
```

The server parses/maps the payload, then wraps it. The client parses the envelope at its HTTP/tRPC adapter and parses `body.data` with the same capability response schema. Pagination metadata uses the kernel pagination schema. This convention avoids duplicating `{ data, meta }` while still validating every serialized field.

## Contract, Command, and View-Model Boundary

These are different types with different owners:

| Type | Canonical location | Purpose |
| --- | --- | --- |
| Shared API input/response payload contract | `src/lib/modules/<module>/shared/contracts/` | Capability data serialized across the network |
| Server-only command/internal DTO | `src/lib/modules/<module>/dtos/` or beside its use case | Internal orchestration data that is not a public wire contract |
| Client feature model | `src/features/<feature>/types.ts` | Client-friendly model after DTO mapping |
| Client form schema | `src/features/<feature>/schemas.ts` | UI-only fields and normalization composed from shared input schemas |
| Database entity/record | `src/lib/shared/infra/db/` | Persistence representation; never a public contract |

Prefer `Input` and `Response` names for shared wire types. Reserve `DTO` for internal or generic discussions where the boundary is already clear.

## Transport Policy

- Current primary transport: `tRPC`
- Migration target transport: `OpenAPI` (REST)
- During migration, both transports may coexist for selected features
- Transport-specific parsing/serialization stays in framework adapters only

Framework-neutral controllers and domain layers (`usecase`, `service`, `repository`) MUST NOT depend on HTTP, tRPC, Next.js, Express, Hono, or OpenAPI framework types.

A framework adapter parses the shared input and passes the inferred type to the capability controller. The controller may pass it directly to a use case/service when the public contract and internal command are intentionally identical. When they differ, the controller maps the shared input to a server-only command.

## Architecture

```text
                    Shared Zod Contracts (Canonical)
                                     |
        +----------------------------+----------------------------+
        |                            |                            |
        v                            v                            v
 Client featureApi          tRPC framework adapter       HTTP framework adapter
 validates response          validates input             validates input
        |                            +-------------+--------------+
        |                                          |
        v                                          v
 client model                    framework-neutral controller
                                                   |
                                                   v
                                      usecase OR service -> repository
```

## Contract Location Guidance

- Module-specific cross-runtime contracts: `src/lib/modules/<module>/shared/contracts/*`
- Universal cross-module primitives: `src/lib/shared/kernel/*`
- Server-only commands/internal DTOs: `src/lib/modules/<module>/dtos/*`
- Client-only form/view schemas: `src/features/<feature>/schemas.ts`

Sharing is determined by the runtime boundary, not by the number of modules using the type. A contract used by one client feature and one server module is still cross-runtime and belongs in that module's `shared/contracts/`.

## Isomorphic Contract Rules

Files under `shared/contracts/` may import:

- Zod;
- other isomorphic contracts from `shared/contracts/`;
- browser-safe, side-effect-free primitives from `src/lib/shared/kernel/`.

They must not import:

- database/ORM schemas or generated entity types;
- `server-only`, environment variables, secrets, filesystem, or Node-only APIs;
- logger, auth session attachment, repositories, services, use cases, or transport initialization;
- React, Next.js components, browser globals, or client stores.

Model the wire format explicitly. For example, use an ISO datetime string in a response contract rather than leaking a database `Date`, then map it to a client model if the UI needs a `Date` object.

## Boundary Usage

```text
Client form schema
  -> shared input contract
  -> featureApi / clientApi
  -> network
  -> framework adapter parses the same input contract
  -> framework-neutral controller maps to a command
  -> use case/service
  -> controller maps the result to the shared response shape
  -> framework adapter validates and serializes the response contract
  -> client featureApi parses the same response contract
  -> client feature model / TanStack Query cache
```

Both sides parse because they guard different trust boundaries: the server validates untrusted input, while the client validates untrusted network output and catches contract drift.

## Coexistence Rule (Parity Required)

When both transports expose the same business capability:

- Inputs must validate against the same Zod schema
- Error semantics must remain equivalent
- Success envelope/payload shape must remain equivalent by contract
- Add parity tests to prevent drift

See `server/runtime/nodejs/libraries/openapi/parity-testing.md`.

## OpenAPI/Swagger Generation

When publishing API docs/specs, generate OpenAPI from the same Zod contracts.

- Prefer build-time artifact generation (`openapi.json` / `openapi.yaml`)
- Keep generation strategy library-agnostic
- Do not maintain separate hand-written schemas for the same contract

See:

- `./zod-openapi-generation.md`

## Standards References

- OpenAPI Specification: https://spec.openapis.org/oas/latest.html
- OpenAPI Paths Object: https://spec.openapis.org/oas/latest.html#paths-object
- OpenAPI Operation Object: https://spec.openapis.org/oas/latest.html#operation-object

## Adapter Boundary Enforcement

Zod-first contracts remain canonical, and adapter boundaries must expose them explicitly:

- Framework adapters should bind success envelopes to concrete response types and call the same capability controller.
- Avoid transport-level `unknown` response payload types for external APIs.
- OpenAPI operation responses must be derived from the same contract intent and stay synchronized with route behavior.

This keeps coexistence practical: same domain behavior, same validation intent, same envelope semantics across tRPC and OpenAPI.

## Related Guides

- [Client Zod Validation](../../client/core/validation-zod.md)
- [Client API Architecture](../../client/core/client-api-architecture.md)
- [API Response Envelope](./api-response.md)
