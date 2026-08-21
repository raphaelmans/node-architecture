# Zod Validation (Agnostic)

Use Zod at **boundaries** to validate and normalize data.

## Rules

- Parse inputs at the edge (UI boundary, API boundary).
- Normalize ambiguous UI values (e.g. `""` to `undefined`) at the schema boundary.
- Import public request/response schemas from the owning module's cross-runtime contract directory.
- Keep UI-only composition and normalization in the client feature.
- Infer TypeScript types from Zod; do not maintain parallel client interfaces for the same wire contract.

## Topology Mapping

In a single-project Next.js repository containing both client and server code:

```text
src/lib/modules/<module>/shared/contracts/
  <capability>.contract.ts
  index.ts
```

Both client and server import from this directory:

```typescript
import {
  CreateUserInputSchema,
  CreateUserResponseSchema,
  type CreateUserInput,
  type CreateUserResponse,
} from "@/lib/modules/user/shared/contracts";
```

In a monorepo topology, use an activated contract package when the schema crosses package boundaries. Client and server consumers import its intentional public exports; they do not reach into another package's files.

Do not import a contract from a server route, router, service, repository, `dtos/` directory, or ORM schema. The shared contract module must remain safe to include in the browser bundle.

## Schema Layers

| Layer | Location | Owns |
| --- | --- | --- |
| Shared wire contract | Resolved isomorphic boundary: module-local in one project or an activated contract package when cross-package | Serialized request and response shape |
| Feature/UI schema | `src/features/<feature>/schemas.ts` | Form-only fields, empty-value normalization, UI validation |
| Feature model | `src/features/<feature>/types.ts` | Client-friendly type after wire-to-model mapping |

## Composition Example

```typescript
// src/features/user/schemas.ts

import { z } from "zod";
import { CreateUserInputSchema } from "@/lib/modules/user/shared/contracts";

export const CreateUserFormSchema = CreateUserInputSchema.safeExtend({
  confirmEmail: z.string().email(),
});

export type CreateUserForm = z.infer<typeof CreateUserFormSchema>;

export function toCreateUserInput(form: CreateUserForm) {
  return CreateUserInputSchema.parse({
    email: form.email,
    name: form.name,
  });
}
```

The form schema may be stricter or contain additional fields, but those UI-only fields must not silently become part of the network payload.

## Response Validation

The client `featureApi` parses network output with the shared response schema:

```typescript
const payload: unknown = await clientApi.post("/api/users", input);
const response = CreateUserResponseSchema.parse(payload);
```

`clientApi` validates/decodes the universal success envelope and returns its `data` payload. `featureApi` then validates that payload with the capability schema. The server also parses input and serializes output through the same contract. Both sides validate because they guard different trust boundaries.

## Import Safety

Shared contracts may import Zod and other isomorphic, side-effect-free contract primitives. They must not import:

- database/ORM entities;
- repositories, services, use cases, loggers, or auth session implementations;
- environment variables, secrets, `server-only`, filesystem, or Node-only APIs;
- React components, browser globals, stores, or query hooks.

Model the wire representation explicitly: use ISO datetime strings in response contracts and map them to `Date` objects in client models only when needed.

## Naming

- File: `<capability>.contract.ts`
- Schemas: `<Capability>InputSchema`, `<Capability>ResponseSchema`
- Inferred types: `<Capability>Input`, `<Capability>Response`
- UI schema: `<Capability>FormSchema`

Avoid ambiguous pairs such as separate client and server `CreateUserDTO` interfaces.

## References

- [Server API Contracts: Zod-First](../../server/core/api-contracts-zod-first.md)
- [Client API Architecture](./client-api-architecture.md)
- [Domain Logic](./domain-logic.md)

For detailed historical examples, see `legacy/client/01-zod-schema-architecture.md`.
