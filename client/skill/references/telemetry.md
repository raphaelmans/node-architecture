# Telemetry Slice

Use this slice for client operational logging, browser debug scopes, Sentry, product analytics, consent, identity, correlation, redaction, and telemetry factory wiring.

## Contents

- [Separate ports](#separate-ports)
- [Operational logging](#operational-logging)
- [Ownership and correlation](#ownership-and-correlation)
- [Product analytics](#product-analytics)
- [Runtime assembly](#runtime-assembly)
- [Safety and tests](#safety-and-tests)

## Separate Ports

Keep four concerns distinct:

| Concern | Port or owner | Typical destination |
| --- | --- | --- |
| Runtime diagnostics | `AppLogger` | `debug`, console, optional Sentry |
| User/business behavior | `ProductAnalytics` | analytics adapter(s) |
| Trace correlation | runtime instrumentation | tracing backend |
| User notification | toast/UI facade | rendered UI |

Do not create a combined telemetry service or a controller solely for telemetry. Logging and analytics branch from existing owners without changing business DTOs or method signatures.

## Operational Logging

Application code depends on an OpenTelemetry-shaped port:

```ts
type LogAttributeValue =
  | string
  | number
  | boolean
  | readonly string[]
  | readonly number[]
  | readonly boolean[];

interface AppLogger {
  debug(event: LogEvent, message: string): void;
  info(event: LogEvent, message: string): void;
  warn(event: LogEvent, message: string): void;
  error(event: LogEvent, message: string): void;
  child(scope: string, attributes?: LogAttributes): AppLogger;
}
```

Callers supply severity via the method, stable `eventName`, readable message, occurrence attributes, and the original error when applicable. Adapters supply timestamps, normalized severity, resource/release/environment fields, instrumentation scope, trace context, safe route/actor context, and serialized exceptions.

Use dotted operational event names such as `<domain>.<operation>.<outcome>`. Never put IDs, URLs, timestamps, or other dynamic values in the name.

Use ownership-first `debug` namespaces:

```text
app:<feature>:<area>:<severity>
```

`localStorage.debug` controls only the local sink. It must never affect remote collection.

## Ownership and Correlation

Record a failure once:

- `clientApi`: method, sanitized path, duration, status, retry exhaustion, network failure, server `requestId`.
- `featureApi`: response-contract or mapping failure introduced there.
- query adapter: only a distinct final/cache outcome not already owned below.
- workflow/business component: a multi-step workflow outcome distinct from one transport call.
- framework error boundary: unhandled render/runtime exception.
- presentation component: no routine operational logging.

Do not call `featureApi.create(input, { logger, traceId, requestId, pathname })`. Inject the logger into emitting objects, establish runtime context once, let instrumentation supply trace/span fields, and preserve a server request ID through typed errors for support.

Redact before fan-out. Never log secrets, credentials, cookies, authorization headers, raw bodies by default, query-bearing URLs, payment data, unrestricted objects, or unapproved personal data.

## Product Analytics

Use a typed discriminated union or schema registry:

```ts
type ProductEvent =
  | { name: "profile_created"; properties: { source: "settings" | "onboarding" } }
  | { name: "checkout_completed"; properties: { plan: "starter" | "pro"; currency: string } };

interface ProductAnalytics {
  track(event: ProductEvent): void;
  identify(actor: { userId: string; accountId?: string }): void;
  reset(): void;
}
```

Use past-tense `snake_case` event names with bounded properties. Emit completion events only after the meaningful operation succeeds. Attempt events are separate occurrences. Keep durable financial, compliance, or critical business facts on the server/outbox path rather than browser-only analytics.

Adapters own consent gating, identity/session lifecycle, batching, retry, common context, vendor mapping, and non-fatal failure reporting. Call `identify` after identity is available and `reset` on logout/account reset. Do not send email or raw form data by default.

## Runtime Assembly

Use the canonical infrastructure paths:

```text
src/common/
  logging/
    types.ts
    attributes.ts
    factory.ts
    adapters/
    wrappers/
  analytics/
    types.ts
    factory.ts
    consent.ts
    adapters/
  runtime/
    browser.ts
    request.ts
```

Do not place this infrastructure in a parallel `src/runtime/` or `src/lib/common/` tree.

```text
composition root
  -> createAppLogger(sinks, context, redaction, sampling)
  -> createProductAnalytics(adapters, consent, logger)
  -> createClientApi(transport, logger)
  -> create<Feature>Api(clientApi, toAppError, child logger)
```

- Browser instances are application-scoped.
- SSR instances are request-scoped only when they capture headers, cookies, actor, request ID, or trace context.
- Feature code receives `AppLogger` or `ProductAnalytics`, never `debug`, Sentry, a vendor SDK, or the runtime container.
- Development uses opt-in local `debug`; tests use spies/no-ops; production uses filtered remote errors/warnings and sampled records.
- Sentry is optional. For one occurrence, capture either the exception or a structured log record, not both.

## Safety and Tests

- Logging or analytics delivery failures must never alter business behavior.
- Test logger severity/event mapping, enrichment, redaction-before-fan-out, sampling, and non-fatal sink failures at adapter boundaries.
- Test analytics success-only emission, failure suppression, consent, identify/reset, and non-fatal delivery with a fake port.
- Feature tests assert only standardized records/events, not vendor formatting.
- Never initialize live telemetry vendors in unit tests.

## Derivation Sources

Derived from the source repository's logging, product-analytics, composition-root, error-handling, client API, React conventions, and Next.js transport/runtime documents. These paths are provenance only in an installed skill.
