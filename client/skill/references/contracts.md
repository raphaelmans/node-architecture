# Contracts Slice

Use this slice for Zod wire contracts, form/schema composition, response validation, DTO mapping, normalized application errors, and safe error presentation.

## Contents

- [One wire contract](#one-wire-contract)
- [Schema layers](#schema-layers)
- [Boundary parsing](#boundary-parsing)
- [AppError contract](#apperror-contract)
- [Normalization and reporting](#normalization-and-reporting)
- [Review checklist](#review-checklist)

## One Wire Contract

Define each public capability once:

```text
src/lib/modules/<module>/shared/contracts/   # single-project mapping
  <capability>.contract.ts
  index.ts
```

In a monorepo, use an activated `packages/contracts/<module>/` boundary when the schema crosses packages. Import through public exports; never reach into a server application or capability package for wire schemas.

Both client and server import the same input and response schemas. Do not import wire contracts from routes, routers, services, repositories, DTO folders, or ORM schemas.

Use JSON-safe representations. Model datetimes as ISO strings at the wire boundary and map them to `Date` only in runtime-specific models when necessary.

## Schema Layers

| Layer | Owns |
| --- | --- |
| Shared wire contract | Serialized API input and response shape |
| Feature/UI schema | Form-only fields, UI validation, and empty-value normalization |
| Feature model | Client-friendly mapped type after parsing |

Compose UI schemas from shared input schemas rather than recreating them:

```ts
export const ProfileFormSchema = UpdateProfileInputSchema.safeExtend({
  confirmEmail: z.string().email(),
});

export function toUpdateProfileInput(form: ProfileForm) {
  return UpdateProfileInputSchema.parse({
    email: form.email,
    name: form.name,
  });
}
```

Normalize ambiguous UI values such as `"" -> undefined` at the UI schema boundary. UI-only fields must not leak into the network payload.

## Boundary Parsing

Parse at every trust boundary because each boundary protects a different concern:

```text
UI input
  -> feature form schema
  -> shared input schema
  -> transport
  -> server input parse

network payload
  -> universal envelope decode in clientApi
  -> capability response parse in featureApi
  -> pure DTO-to-model mapping
```

Treat response parse or mapping failures as contract errors. Log them once at the feature API boundary and expose a generic message to the UI.

When the boundary already knows a response violated the capability contract, construct that known error directly rather than sending the Zod error through the generic provider normalizer:

```ts
try {
  return ResponseSchema.parse(payload);
} catch (error) {
  if (error instanceof ZodError) {
    logger.error(
      {
        eventName: "profile.update.response.invalid",
        attributes: { "error.type": "api.invalid_response" },
        error,
      },
      "Profile update response violated contract",
    );
    throw invalidResponseError(error);
  }
  throw toAppError(error);
}
```

`invalidResponseError` produces `kind: "contract"` with a safe generic message. Reserve `toAppError` for unknown/provider failures whose classification is not already known at this boundary.

Shared contracts may import Zod and side-effect-free isomorphic primitives. They must not import ORM entities, server services, environment variables, Node-only modules, React, browser globals, stores, or query hooks.

## AppError Contract

UI code branches only on a discriminated `AppError`, never on Ky, fetch, Axios, tRPC, Sentry, or provider-specific errors.

```ts
type AppError =
  | ({ kind: "network" } & AppErrorMeta)
  | ({ kind: "unauthorized" | "forbidden" | "not_found" | "rate_limited" } & AppErrorMeta)
  | ({ kind: "validation"; fieldErrors?: Record<string, string> } & AppErrorMeta)
  | ({ kind: "contract" } & AppErrorMeta)
  | ({ kind: "unknown" } & AppErrorMeta);
```

The adapter boundary is always:

```ts
function toAppError(error: unknown): AppError;
```

Preserve safe `message`, `code`, `status`, and `requestId` metadata. Use a generic message for internal, unexpected, server, contract, or mapping failures. Reserve field errors for user-correctable validation failures.

## Normalization and Reporting

Normalize once, then pass the same `AppError` through unchanged:

```text
provider/transport error
  -> typed transport error
  -> toAppError
  -> feature/query/UI handling
```

Normalization does not itself imply reporting. Assign one reporting owner:

- `clientApi`: transport and non-success response failures;
- `featureApi`: capability response parsing or mapping failures;
- framework error boundary: unhandled render/runtime failures.

Do not report the same handled failure in client API, feature API, QueryClient defaults, hooks, forms, and components.

Map validation errors close to user input. Send other safe errors through an error/toast facade rather than importing a toast provider into feature code. Sentry remains behind the logging/error-boundary adapter.

## Review Checklist

- Client and server share one runtime schema per public capability.
- UI schemas compose shared input contracts and remove UI-only fields before sending.
- `clientApi` decodes the universal envelope; `featureApi` parses the capability payload.
- Known response-schema failures become `invalidResponseError`, not generic validation errors.
- Provider-specific error inspection exists only in adapters.
- UI branches on `AppError.kind` and never sees raw provider errors.
- Internal failures expose generic UI messages.
- Each failure is reported once by its owning boundary.
- Contract and pure domain tests cover the boundary without duplicating matrices across layers.

## Derivation Sources

Derived from the source repository's validation-zod, error-handling, domain-logic, client-api-architecture, React error-handling, and React forms documents. These paths are provenance only in an installed skill.
