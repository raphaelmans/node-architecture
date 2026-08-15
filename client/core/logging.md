# Client Operational Logging

> Core standard for structured client diagnostics, browser debug scoping, correlation, and optional remote reporting.

## Core Decision

Application code depends on a small `AppLogger` port with an OpenTelemetry-shaped record model.

- `debug` is the default local browser sink and namespace selector.
- Server-side local/operational output remains structured Pino JSON through the server `AppLogger` adapter.
- Sentry is an optional filtered production sink for unexpected errors and selected operational records.
- Providers remain behind adapters; feature code never imports `debug` or Sentry directly.
- Product analytics uses a separate `ProductAnalytics` port. See [Product Analytics](./product-analytics.md).
- Logging failures are best-effort and never change business behavior.

OpenTelemetry's log data model supplies the canonical concepts: timestamp, severity, body, event name, trace context, resource, instrumentation scope, and attributes. The application contract intentionally accepts only caller-owned fields; adapters add trusted runtime fields.

This is a compatibility contract, not a requirement to import the OpenTelemetry browser Logs SDK. Browser instrumentation remains less mature than the core data model, so application code stays behind `AppLogger` while adapters can evolve independently.

References:

- [OpenTelemetry Logs Data Model](https://opentelemetry.io/docs/specs/otel/logs/data-model/)
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/concepts/semantic-conventions/)
- [OpenTelemetry JavaScript status](https://opentelemetry.io/docs/languages/js/)
- [`debug` package](https://www.npmjs.com/package/debug)

## Separation of Concerns

| Concern | Purpose | Port / owner | Typical destination |
| --- | --- | --- | --- |
| Operational logging | Debug failures and runtime behavior | `AppLogger` | `debug`, console, Sentry |
| Product analytics | Understand user and business behavior | `ProductAnalytics` | analytics vendor(s) |
| Distributed tracing | Correlate operations across boundaries | runtime instrumentation | tracing backend |
| User notification | Communicate a safe outcome | toast/UI facade | rendered UI |

Do not introduce a combined `TelemetryService` with unrelated logging, analytics, tracing, and notification methods.

## Architecture

```text
clientApi / featureApi / workflow owner
                  |
                  v
             AppLogger port
                  |
                  v
   context enrichment -> redaction -> sampling
                  |
          +-------+--------+
          |                |
          v                v
   debug adapter      remote adapter
   local browser      Sentry (optional)
```

`debug` controls local visibility. It does not define the application record shape or control remote collection.

## Logger Contract

Use telemetry-compatible primitive attributes instead of `Record<string, unknown>`.

```ts
// src/common/logging/types.ts
export type LogAttributeValue =
  | string
  | number
  | boolean
  | readonly string[]
  | readonly number[]
  | readonly boolean[];

export type LogAttributes = Readonly<
  Record<string, LogAttributeValue | undefined>
>;

export interface LogEvent {
  eventName?: string;
  attributes?: LogAttributes;
  error?: unknown;
}

export interface AppLogger {
  debug(event: LogEvent, message: string): void;
  info(event: LogEvent, message: string): void;
  warn(event: LogEvent, message: string): void;
  error(event: LogEvent, message: string): void;

  child(scope: string, attributes?: LogAttributes): AppLogger;
}
```

Callers provide:

- severity through the selected method;
- a stable event name when the record represents a queryable occurrence;
- a human-readable message;
- occurrence-specific attributes; and
- the original error when applicable.

Adapters provide:

- timestamp and normalized severity number;
- resource attributes such as service name, version, and environment;
- instrumentation scope / logger namespace;
- active trace and span correlation;
- safe route and actor context when configured; and
- serialized exception attributes after redaction.

Callers must not set trusted adapter-owned fields such as timestamps, trace IDs, span IDs, or release metadata.

## Canonical Record Mapping

The logical emitted record maps to:

```text
Timestamp             adapter clock
SeverityText/Number   debug=5, info=9, warn=13, error=17
Body                  human-readable message
EventName             stable eventName
TraceId/SpanId        active tracing context, when available
Resource              service.name/version/environment
InstrumentationScope  logger child namespace
Attributes            caller fields + safe contextual fields
```

For non-OTLP JSON, use `trace_id`, `span_id`, and `trace_flags` at the top level. A compatible JSON adapter may map `eventName` to `otel.event.name`. Application code continues to use the vendor-neutral `eventName` property.

## Event and Attribute Naming

Operational event names use stable dotted names:

```text
<domain>.<operation>.<outcome>
```

Examples:

- `profile.load.completed`
- `profile.update.failed`
- `http.client.request.completed`
- `api.response.invalid`

Rules:

- never put IDs, URLs, timestamps, or other dynamic values in `eventName`;
- reuse OpenTelemetry semantic attributes where they apply;
- put application-specific attributes under one documented namespace;
- prefer low-cardinality values that remain queryable; and
- keep messages stable enough to scan but do not parse messages as data.

Define `APP_ATTRIBUTES` once with the same serialized names across client and server. The registry may live in runtime-specific modules, but `requestId` and other cross-boundary concepts must not acquire different keys per adapter/vendor.

Example:

```ts
logger.warn(
  {
    eventName: "profile.update.failed",
    attributes: {
      "error.type": appError.code ?? appError.kind,
      "http.response.status_code": appError.status,
      [APP_ATTRIBUTES.requestId]: appError.requestId,
    },
    error,
  },
  "Profile update failed",
);
```

## Namespace Convention (`debug`)

Use ownership-first namespaces:

```text
app:<feature>:<area>:<severity>
```

Examples:

- `app:profile:api:debug`
- `app:profile:api:error`
- `app:auth:flow:info`
- `app:chat:stream:warn`

The debug adapter derives these from `logger.child("profile:api")` and the selected method. It renders the normalized structured record with `%O`.

Enable local output:

```js
localStorage.debug = "app:profile:*"
// or
localStorage.debug = "app:*:api:error"
```

Disable:

```js
localStorage.debug = ""
```

Chromium-based browsers normally show `debug` output under the **Verbose** console level.

## Ownership by Client Layer

Default rule: log at boundaries and record each failure once.

| Layer | Owns |
| --- | --- |
| `clientApi` | HTTP method/path, duration, status, network failure, retry exhaustion, response `requestId` |
| `featureApi` | Contract parsing, DTO mapping, and normalization failures introduced at that boundary |
| Query adapter | Final query/mutation failure only when no lower boundary owns it; retry/cache decisions when operationally meaningful |
| Feature workflow/business component | Workflow-level outcome not equivalent to a single transport call |
| Framework error boundary | Unhandled render/runtime exceptions |
| Presentation component | No routine operational logging |

Do not log the same transport exception in `clientApi`, `featureApi`, QueryClient defaults, and a component. A higher layer logs only when it owns a distinct outcome or adds operationally meaningful context.

## Create Data Flow

```text
CreateForm.onSubmit
  -> useMutCreate.mutateAsync
  -> FeatureApi.create
  -> ClientApi.post
  -> network
  <- response + requestId
  <- shared response parsing + feature model
  +-> ProductAnalytics.track(success event)
  +-> cache update/invalidation
  -> toast/navigation
```

Operational ownership along the flow:

```ts
// clientApi: transport outcome
logger.debug(
  {
    eventName: "http.client.request.completed",
    attributes: {
      "http.request.method": "POST",
      "url.path": path,
      "http.response.status_code": response.status,
      [APP_ATTRIBUTES.requestId]: requestId,
      [APP_ATTRIBUTES.durationMs]: durationMs,
    },
  },
  "HTTP request completed",
);

// featureApi: only a contract failure owned by this boundary
logger.error(
  {
    eventName: "user.create.response.invalid",
    attributes: { "error.type": "api.invalid_response" },
    error,
  },
  "Create-user response violated contract",
);
```

Product analytics for the successful business action is emitted separately by the mutation/workflow owner. See [Product Analytics](./product-analytics.md#create-data-flow).

## Correlation Context

Do not add logging metadata to business DTOs or thread a telemetry options object through method chains.

Avoid:

```ts
featureApi.create(input, { logger, traceId, spanId, requestId, pathname });
```

Instead:

- inject `AppLogger` only into objects that emit records;
- establish route/runtime context once at the application boundary;
- let tracing instrumentation provide active trace/span fields;
- let `clientApi` capture a server-provided `requestId`; and
- preserve `requestId` through `ApiClientError -> AppError` for support and error logs.

On successful requests, `clientApi` may attach `requestId` to its boundary record/span without adding it to the returned business payload.

W3C `traceparent`/`tracestate` propagation is optional until browser tracing is adopted. When enabled, propagation belongs in transport instrumentation, not feature methods.

## Runtime Strategy

| Environment | Local debug sink | Remote logging/error sink |
| --- | --- | --- |
| Development | `debug`, opt-in through `localStorage.debug` | off by default |
| Test | spy or no-op | off |
| Preview/staging | off or break-glass | enabled with non-production destination and sampling |
| Production | off by default; gated break-glass only | unexpected errors, `error`, selected `warn`, sampled `info` |

`localStorage.debug` controls only the local debug sink. It must never enable, disable, or change remote telemetry collection.

### Break-Glass Local Debugging

If `NEXT_PUBLIC_ALLOW_BREAK_GLASS_LOGGING === "true"`, the local sink may honor:

```js
localStorage["app:log:provider"] = "debug"
localStorage.debug = "app:*"
```

Reset:

```js
localStorage.removeItem("app:log:provider")
localStorage.debug = ""
```

This affects local display only.

## Optional Sentry Adapter

Use Sentry for:

- unhandled browser exceptions and rejected promises;
- framework error-boundary exceptions;
- explicit unexpected errors; and
- filtered structured `error`/`warn` records.

For one occurrence, the adapter chooses either exception capture or a structured log record; it does not emit both.

Do not:

- import Sentry in feature code;
- automatically forward every `console.*` or `debug` call;
- send routine debug traffic; or
- report a handled error again at every layer.

The adapter maps the application record to Sentry attributes and applies `beforeSend`/`beforeSendLog` redaction, filtering, and sampling. Sentry delivery failure remains invisible to business code.

Reference: [Sentry structured logs](https://docs.sentry.io/platforms/javascript/guides/nextjs/logs/).

## Sensitive Data and Redaction

Apply redaction before fan-out so every sink follows the same baseline.

Never log:

- passwords, tokens, cookies, authorization headers, or secrets;
- raw request/response bodies by default;
- full URLs containing query strings or fragments;
- payment or sensitive personal data; or
- unrestricted objects supplied by callers.

Allowlist safe actor/account identifiers according to the application's privacy policy. Exception messages and stack traces may contain sensitive data and must pass through the redaction policy before remote export.

## Runtime Placement

```text
src/common/logging/
  types.ts
  attributes.ts
  logger.ts
  factory.ts              # createAppLogger
  feature.ts
  context.ts
  adapters/
    debug.ts
    console.ts
    noop.ts
    sentry.ts             # optional
  wrappers/
    with-context.ts
    with-redaction.ts
    with-sampling.ts
```

The composition root calls `createAppLogger`; feature code receives `AppLogger` or a feature-scoped child and never imports provider adapters.

## Testing

Unit tests use a spy or no-op logger:

```ts
const logger = createLoggerSpy();
const api = createProfileApi({ clientApi, toAppError, logger });
```

Assert logging only when emission is part of the public behavior being standardized—for example, a response-contract violation produces one `api.response.invalid` error record. Do not assert adapter formatting in feature tests.

Adapter tests cover:

- severity and event-name mapping;
- context enrichment;
- correlation-field precedence;
- redaction before fan-out;
- sampling/filtering; and
- sink failures remaining non-fatal.

## Checklist

- [ ] Feature code depends on `AppLogger`, never `debug`, console, or Sentry
- [ ] Attributes use telemetry-compatible primitive values
- [ ] Event names are stable and contain no dynamic values
- [ ] `clientApi` owns transport logging and response `requestId`
- [ ] `featureApi` logs only failures owned by its parsing/mapping boundary
- [ ] Each failure has one primary reporting owner
- [ ] Context enrichment is automatic; telemetry is absent from business DTOs
- [ ] Redaction occurs before all local and remote sinks
- [ ] `debug` namespaces follow `app:<feature>:<area>:<severity>`
- [ ] `localStorage.debug` affects only local output
- [ ] Sentry is optional, filtered, sampled, and hidden behind an adapter
- [ ] Product analytics uses `ProductAnalytics`, never `AppLogger`

## Related Docs

- [Product Analytics](./product-analytics.md)
- [Client API Architecture](./client-api-architecture.md)
- [Error Handling](./error-handling.md)
- [Testing](./testing.md)
- [Server Observability](../../server/core/observability.md)
- [Server Logging](../../server/core/logging.md)
