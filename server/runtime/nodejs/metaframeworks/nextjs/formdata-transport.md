# FormData Transport (Next.js + tRPC)

> Metaframework-level transport rules for non-JSON payloads.

## Why This Is Here

`FormData`, `File`, and `Blob` handling depends on transport/runtime behavior, so it belongs in Next.js metaframework docs (not core).

## Client Transport Split

When using `@trpc/react-query`, route non-JSON payloads to non-batched links:

- JSON payloads -> `httpBatchLink`
- Non-JSON payloads -> `httpLink`

```ts
splitLink({
  condition: (op) => isNonJsonSerializable(op.input),
  true: httpLink({ url: "/api/trpc" }),
  false: httpBatchLink({ url: "/api/trpc" }),
});
```

## Server Parsing

Use `zod-form-data` for FormData payload parsing in DTO/schema modules:

```ts
import { zfd } from "zod-form-data";

export const UploadSchema = zfd.formData({
  entityId: zfd.text(z.string().uuid()),
  file: zfd.file(),
});
```

## Validation Boundary

- Transport schema validates shape and file-level constraints (size/type).
- Domain/service layer validates business rules.
- Storage adapter handles provider upload concerns.

For storage integration examples:

- `../../libraries/supabase/integration.md`

## tRPC v11 Note

tRPC v11 supports non-JSON content types natively; custom FormData transformers are generally unnecessary when link splitting is configured correctly.

## Do / Don't

Do:

- Keep upload limits and allowed MIME types centralized.
- Return typed errors with request correlation metadata.

Don't:

- Batch FormData operations.
- Parse raw multipart payloads inside service/business layers.

