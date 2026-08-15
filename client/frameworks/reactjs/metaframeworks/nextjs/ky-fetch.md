# Non-tRPC HTTP Clients with `ky`

> Conventions for browser-side HTTP clients that call Next.js `route.ts` endpoints.

Examples target Ky 2 (`baseUrl`/`prefix`). If a consumer is pinned to Ky 1, follow that version's `prefixUrl` path rules until it migrates; do not mix option names across major versions.

## Goals

- Use a consistent HTTP client wrapper (`ky`)
- Decode the standard server envelope (`ApiResponse<T>` / `ApiErrorResponse`)
- Throw typed, inspectable errors (aligned with server error-handling)
- Integrate cleanly with TanStack Query hooks
- Import the same Zod input/response contracts used by the Next.js route
- Own transport logging and response `requestId` correlation through injected `AppLogger`
- Construct Ky only inside `createClientApi` at the client composition root

## Standard Response Envelope

Non-tRPC endpoints must follow the server conventions:

- **Success (2xx)**: `ApiResponse<T>` → `{ data: T }`
- **Error (non-2xx)**: `ApiErrorResponse` → `{ code, message, requestId, details? }`

Both are defined in `src/lib/shared/kernel/response.ts`. Capability-specific payload schemas live in `src/lib/modules/<module>/shared/contracts/`.

## Ky-backed `clientApi` factory

Keep Ky construction inside the factory. Feature code depends on `IClientApi`, never Ky.

```typescript
import ky from "ky";

export function createClientApi(deps: {
  logger: AppLogger;
  baseUrl?: string;
  timeoutMs?: number;
}): IClientApi {
  const transport = ky.create({
    baseUrl: deps.baseUrl,
    throwHttpErrors: false,
    timeout: deps.timeoutMs ?? 30_000,
  });

  return new KyClientApi({ transport, logger: deps.logger });
}
```

The browser composition root calls `createClientApi` once. Same-origin browser calls may omit `baseUrl` and use origin-relative paths such as `/api/profile`. SSR supplies an absolute `baseUrl` when required and creates the client per request only when the transport closes over request headers/cookies/context.

## Typed client error

Throw a typed transport error so `toAppError` can preserve safe `code` and `requestId` metadata. UI and feature hooks consume only the resulting `AppError`.

```typescript
import type { ApiErrorResponse } from "@/lib/shared/kernel/response";

export class ApiClientError extends Error {
  readonly code: string;
  readonly requestId: string;
  readonly httpStatus: number;
  readonly details?: Record<string, unknown>;

  constructor(args: {
    code: string;
    message: string;
    requestId: string;
    httpStatus: number;
    details?: Record<string, unknown>;
  }) {
    super(args.message);
    this.name = "ApiClientError";
    this.code = args.code;
    this.requestId = args.requestId;
    this.httpStatus = args.httpStatus;
    this.details = args.details;
  }
}

export const isApiClientError = (error: unknown): error is ApiClientError =>
  error instanceof ApiClientError;

const isApiErrorResponse = (value: unknown): value is ApiErrorResponse => {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.code === "string" &&
    typeof record.message === "string" &&
    typeof record.requestId === "string"
  );
};
```

## `featureApi` example

```typescript
import {
  PreviewGoogleLocationInputSchema,
  PreviewGoogleLocationResponseSchema,
  type PreviewGoogleLocationInput,
  type PreviewGoogleLocationResponse,
} from "@/lib/modules/location/shared/contracts";
import { invalidResponseError } from "@/common/errors/invalid-response-error";

export class GoogleLocApi implements IGoogleLocApi {
  constructor(private readonly deps: {
    clientApi: IClientApi;
    logger: AppLogger;
    toAppError: (error: unknown) => AppError;
  }) {}

  async preview(
    input: PreviewGoogleLocationInput,
  ): Promise<PreviewGoogleLocationResponse> {
    const request = PreviewGoogleLocationInputSchema.parse(input);

    try {
      const payload = await this.deps.clientApi.post<unknown>(
        "/api/poc/google-loc",
        request,
      );

      return PreviewGoogleLocationResponseSchema.parse(payload);
    } catch (error) {
      if (error instanceof ZodError) {
        this.deps.logger.error(
          {
            eventName: "location.preview.response.invalid",
            attributes: { "error.type": "api.invalid_response" },
            error,
          },
          "Location preview response violated contract",
        );
        throw invalidResponseError(error);
      }

      throw this.deps.toAppError(error);
    }
  }
}
```

`KyClientApi` decodes the universal envelope and returns its `data`. It also logs the transport outcome once. `GoogleLocApi` validates the capability payload and logs only a contract failure owned by that boundary.

## React Query integration

```typescript
import { useMutation } from "@tanstack/react-query";

export function useMutGoogleLocPreview() {
  const analytics = useProductAnalytics();
  const googleLocApi = getGoogleLocApi();

  return useMutation({
    mutationFn: (input: PreviewGoogleLocationInput) => googleLocApi.preview(input),
    onSuccess: (_location, input) => {
      analytics.track({
        name: "location_previewed",
        properties: { provider: "google" },
      });
    },
  });
}
```

The typed product event is optional and belongs here only when this reusable mutation owns the successful user action. It is not an operational log.

## Feature API Contract (Required)

Do not expose raw transport functions directly to hooks long-term.
Wrap them behind `I<Feature>Api` + class in `src/features/<feature>/api.ts`.

```typescript
export interface IGoogleLocApi {
  preview(input: PreviewGoogleLocationInput): Promise<PreviewGoogleLocationResponse>;
}

export const createGoogleLocApi = (deps: GoogleLocApiDeps): IGoogleLocApi =>
  new GoogleLocApi(deps);
```

The corresponding `route.ts` imports `PreviewGoogleLocationInputSchema` and `PreviewGoogleLocationResponseSchema` from the same module. Do not define a second route-local or client-local payload schema.

Testing implication:

- API class tests mock transport boundary
- query hook tests mock `IGoogleLocApi`

## Invalidation Ownership (Mixed)

For non-tRPC adapters, query keys come from `src/common/query-keys/<feature>.ts`.

```typescript
export const googleLocQueryKeys = {
  all: ["google-location"] as const,
  preview: () => [...googleLocQueryKeys.all, "preview"] as const,
  history: () => [...googleLocQueryKeys.all, "history"] as const,
};
```

Variant A (preferred): hook-owned invalidation

```typescript
export function useMutGoogleLocPreview() {
  const queryClient = useQueryClient();
  const analytics = useProductAnalytics();
  const googleLocApi = getGoogleLocApi();

  return useMutation({
    mutationFn: ({ url }: { url: string }) => googleLocApi.preview({ url }),
    onSuccess: async () => {
      analytics.track({
        name: "location_previewed",
        properties: { provider: "google" },
      });

      await queryClient.invalidateQueries({
        queryKey: googleLocQueryKeys.preview(),
      });
    },
  });
}
```

Variant B (allowed): component-coordinator sequencing through a cache-sync hook

```typescript
export function useModGoogleLocSync() {
  const queryClient = useQueryClient();
  return {
    invalidateAfterPreview: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: googleLocQueryKeys.preview() }),
        queryClient.invalidateQueries({ queryKey: googleLocQueryKeys.history() }),
      ]),
  };
}

const previewMut = useMutGoogleLocPreview();
const googleLocSync = useModGoogleLocSync();

const onSubmit = async ({ url }: { url: string }) => {
  await previewMut.mutateAsync({ url });
  await googleLocSync.invalidateAfterPreview();
};
```

Choose based on orchestration scope:

- Shared mutation behavior across screens: hook-owned.
- Route-local submit flow sequencing: component coordinator calling a named `useMod*Sync` operation.

Detailed scenario matrix:

- `client/frameworks/reactjs/server-state-patterns-react.md`

## Error Normalization Handoff

This layer should emit a typed transport error (for example `ApiClientError`), then hand off normalization to the app error adapter:

```text
Network failure / non-2xx response
  -> ApiClientError (transport-typed)
  -> toAppError(err) adapter
  -> UI branches on AppError.kind only
```

Preserve `requestId` when present so support/debug logs can correlate client and server events.

`KyClientApi` records method, sanitized path, duration, status, retry exhaustion, and `requestId` through `AppLogger`. Query hooks and components must not report the same transport failure again. Sentry, when enabled, receives only records selected by the logger adapter.

## Notes

- Do not leak internal error details in `message`; use `details` for additional context.
- Always include `requestId` in server responses so clients can show it or log it.
- Prefer an `x-request-id` response header on success and error; fall back to the error envelope when necessary.
- Assemble `createClientApi` and `createGoogleLocApi` in the composition root; do not create hidden singletons in feature modules.
