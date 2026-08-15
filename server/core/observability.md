# Observability

> Core standard for request correlation, tracing, and operational telemetry across every server transport.

## Scope

Observability answers operational questions: what happened, where did it fail, and how long did it take?

Keep these concerns separate:

| Concern | Purpose | Typical implementation |
| --- | --- | --- |
| Server logs | Debugging and operations | Structured backend through `AppLogger` |
| Distributed traces | Follow work across process and network boundaries | OpenTelemetry |
| Metrics | Aggregate rates, latency, and resource usage | OpenTelemetry metrics |
| Product analytics | Understand user and business behavior | `ProductAnalytics` adapters |
| Database transactions | Atomically commit or roll back database operations | `TransactionContext` |

Product analytics follows [Product Analytics](./product-analytics.md). Database transaction propagation follows [Transaction Management](./transaction.md).

## Standards Baseline

This architecture follows:

- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/) for standard span names and attributes
- [OpenTelemetry Logs Data Model](https://opentelemetry.io/docs/specs/otel/logs/data-model/) for log correlation and event records
- [Trace Context in non-OTLP Log Formats](https://opentelemetry.io/docs/specs/otel/compatibility/logging_trace_context/) for JSON field names
- [OpenTelemetry Attribute Naming](https://opentelemetry.io/docs/specs/semconv/general/naming/) for custom namespaces

Every telemetry field must be classified as one of:

1. OpenTelemetry standard;
2. logging-backend transport field; or
3. explicitly namespaced application attribute.

Do not present custom application fields as OpenTelemetry semantic conventions.

## Correlation Identifiers

| Concept | TypeScript/runtime name | JSON log representation | Owner |
| --- | --- | --- | --- |
| Application request ID | `requestId` | `<application-namespace>.request.id` | HTTP transport/application |
| Trace ID | `traceId` | `trace_id` | OpenTelemetry |
| Span ID | `spanId` | `span_id` | OpenTelemetry |
| Trace flags | `traceFlags` | `trace_flags` | OpenTelemetry |

`requestId` remains camelCase in TypeScript and public JSON API error responses. The logger adapter serializes it under the configured application namespace. OpenTelemetry defines `trace_id`, `span_id`, and `trace_flags` as the trace-context field names for non-OTLP JSON logs.

`traceId` and `spanId` should be obtained from the active OpenTelemetry span, not invented independently by services.

```text
User action (trace_id: trace-123)
  |
  +-- API request (request ID: req-a, span_id: span-1)
  |     +-- database query (span_id: span-2)
  |
  +-- provider request (span_id: span-3)
```

Do not use any of these as a business identifier. Continue using identifiers such as `userId`, `orderId`, and `paymentId` for domain entities.

## Application Attribute Namespace

OpenTelemetry reserves its registered namespaces, including `app.*` and `otel.*`. Custom fields must not claim those namespaces.

Choose one stable namespace for the application:

```text
Company-wide:  com.<company>.<application>
Internal app:  <unique_application_name>
```

Canonical example used in this guide:

```typescript
export const APP_ATTRIBUTES = {
  requestId: "com.example.api.request.id",
  causationRequestId: "com.example.api.causation.request.id",
  jobId: "com.example.api.job.id",
  codeLayer: "com.example.api.code.layer",
  operationName: "com.example.api.operation.name",
  operationType: "com.example.api.operation.type",
  operationOutcome: "com.example.api.operation.outcome",
  durationMs: "com.example.api.duration_ms",
  productEventName: "com.example.api.product_event.name",
  analyticsDestination: "com.example.api.analytics.destination",
  errorDetails: "com.example.api.error.details",
  debugData: "com.example.api.debug.data",
  webhookProvider: "com.example.api.webhook.provider",
  webhookEventType: "com.example.api.webhook.event.type",
  webhookEventId: "com.example.api.webhook.event.id",
  skipReason: "com.example.api.skip.reason",
  authVerificationType: "com.example.api.auth.verification.type",
  targetUserId: "com.example.api.target.user.id",
} as const;
```

Replace `com.example.api` once at project setup and use the constants everywhere. Do not create attribute names dynamically per module or request.

Values for the custom code-layer attribute are:

```text
transport | controller | use_case | service | repository | provider | worker
```

## Propagation Standard

Observability context is request-scoped and propagated through OpenTelemetry/Node.js async context. Do not add `requestId`, `traceId`, `spanId`, or a logger to `TransactionContext` or `TransactionOptions`.

```text
Transport boundary
  -> establish async observability scope
  -> framework-neutral controller
  -> service/use case
  -> repository/provider

TransactionManager.run
  -> separately supplies TransactionContext only to database operations
```

Transport adapters must:

1. Accept or generate a `requestId`.
2. Let OpenTelemetry extract or create the active trace.
3. Establish the async observability scope before calling application code.
4. Include `requestId` in public error responses.
5. Log request start, completion, duration, and status.

Controllers, services, use cases, repositories, and providers must not manually parse tracing headers.

Only preserve an inbound `x-request-id` when it comes from a trusted boundary and passes a bounded format/length check; otherwise generate a new internal ID. Never treat client-supplied correlation fields as authorization or identity.

Rate limiting may use a separately resolved client identifier, but only after deployment-specific proxy/header validation. It is not a trace field, is never derived from `requestId`, and should not be injected into application method parameters.

## Observability Context

The runtime-specific implementation may use `AsyncLocalStorage` directly or the OpenTelemetry context manager.

```typescript
// shared/infra/observability/request-context.ts

export interface ObservabilityContext {
  requestId: string;
  traceId?: string;
  spanId?: string;
  traceFlags?: string;
  userId?: string;
}

export function getObservabilityContext():
  | ObservabilityContext
  | undefined;

export interface HeaderReader {
  get(name: string): string | null;
}

export function getTrustedRequestId(headers: HeaderReader): string | undefined;

export interface TrustedClientIdentifier {
  value: string;
  source: "trusted_network";
}

export function getTrustedClientIdentifier(
  headers: HeaderReader,
): TrustedClientIdentifier | undefined;

export function runWithObservability<T>(
  initial: ObservabilityContext,
  fn: (context: ObservabilityContext) => Promise<T>,
): Promise<T>;
```

The core runtime primitive accepts plain context values and a minimal header
reader; it does not depend on Fetch `Request`, Express `Request`, or Hono
`Context`. Each framework adapter extracts trusted boundary values and then
calls it.

Node.js Fetch-based adapters may expose a convenience wrapper:

```typescript
export function withRequestObservability<T>(
  request: Request,
  fn: (context: ObservabilityContext) => Promise<T>,
): Promise<T> {
  const requestId = getTrustedRequestId(request.headers) ?? randomUUID();
  return runWithObservability({ requestId }, fn);
}
```

Express adapts with `{ get: (name) => req.get(name) ?? null }`; Hono adapts with
`{ get: (name) => c.req.header(name) ?? null }`. This runtime context is
infrastructure and is not passed as a service or repository method parameter.

## Async and Queue Boundaries

A worker invocation is a new processing boundary with its own request/invocation ID. If an outbox job needs origin correlation, persist a separate `causationRequestId`; do not reuse it as the worker's current request ID.

Propagate standard W3C/OpenTelemetry trace context through queue metadata when the queue adapter supports it. The consumer extracts that carrier and starts a consumer span according to the messaging instrumentation policy. Never copy an old `span_id` into the worker as though that span were still active.

```text
HTTP request: requestId=req-1, producer span=A
  -> outbox job: causationRequestId=req-1, trace carrier
  -> worker: requestId=job-invocation-7, consumer span=B
```

This metadata belongs to the outbox/queue adapter and observability scope, not `TransactionContext`.

## Logger Dependency Injection

Application code depends on a small logger port, not directly on a logging backend.

```typescript
// shared/kernel/logger.ts

export type LogFields = Record<string, unknown>;

export interface AppLogger {
  debug(fields: LogFields, message: string): void;
  info(fields: LogFields, message: string): void;
  warn(fields: LogFields, message: string): void;
  error(fields: LogFields, message: string): void;
}
```

The runtime logger adapter reads the active observability context and merges correlation fields into every record. Factories inject the stable `AppLogger`; they do not construct a logger per business method. The reference Node.js implementation is the [Pino Logger Adapter](../runtime/nodejs/libraries/pino/README.md).

```typescript
export class PinoAppLogger implements AppLogger {
  constructor(private readonly logger: PinoLogger) {}

  info(fields: LogFields, message: string): void {
    const context = getObservabilityContext();

    this.logger.info(
      {
        ...fields,
        trace_id: context?.traceId,
        span_id: context?.spanId,
        trace_flags: context?.traceFlags,
        "user.id": context?.userId,
        [APP_ATTRIBUTES.requestId]: context?.requestId,
      },
      message,
    );
  }

  // debug, warn, and error follow the same pattern
}
```

Controllers, services, and use cases receive only the dependencies they use:

```typescript
export class CreateUserUseCase {
  constructor(
    private readonly userService: IUserService,
    private readonly logger: AppLogger,
  ) {}

  async execute(command: CreateUserCommand): Promise<User> {
    this.logger.debug(
      {
        "otel.event.name": "user.create.started",
        "code.function.name": "CreateUserUseCase.execute",
      },
      "Creating user",
    );
    return this.userService.create(command);
  }
}
```

Rules:

- Do not import the concrete logger inside controllers, services, or use cases.
- Inject `AppLogger` through the factory/composition root.
- Do not inject a combined service locator containing logging, analytics, and tracing.
- The logger adapter applies trusted request/trace fields after caller fields so application code cannot overwrite correlation identifiers.
- The contextual `user.id` represents the authenticated actor. Use a namespaced application attribute when logging a different target entity.
- Emit a named operational event at one owning layer only. A service owns a
  single-domain state event such as `user.created`; a use case owns only a
  distinct workflow event such as `registration.completed`. Do not emit
  `user.created` from both.
- Repositories normally do not log; translate database failures to domain errors and let the boundary log them.
- Logging failures must never change business behavior.

## Span and Event Naming

Use the OpenTelemetry convention appropriate to the operation:

| Signal | Naming rule | Example |
| --- | --- | --- |
| HTTP server span | `{method} {route-template}` | `POST /users` |
| Custom business span | low-cardinality `{verb} {object}` | `create user` |
| Code implementation | `code.function.name` attribute | `CreateUserUseCase.execute` |
| Log event | OpenTelemetry `EventName`; `otel.event.name` in compatible JSON | `user.created` |

Do not use class hierarchy as the visible span name. Do not put IDs, outcomes, or request paths with concrete identifiers in span/event names.

```text
POST /users
  -> create user
       -> INSERT users
```

Do not create a custom span for every controller, service, and repository method. Add a span only for a significant operation with useful duration or child work. Automatic HTTP/database spans already cover transport and queries.

### Layer Flow Example

Do not encode the layer into an invented name such as `class.use-case.method`. Record implementation identity with `code.function.name`; record the architectural layer only in the custom `APP_ATTRIBUTES.codeLayer` attribute.

```text
POST /users                         trace_id=4bf... com.example.api.request.id=req-123
  route       [info]  http.request.started   code.function.name=POST
  controller  [none]  command/result mapping only; log failures at boundary
  use_case    [debug] user.create.started    code.function.name=CreateUserUseCase.execute
  service     [info]  user.created           code.function.name=UserService.create
  route       [info]  http.request.completed http.response.status_code=201
```

Every emitted record carries the same `trace_id` and namespaced request ID automatically. Records created inside child spans carry that child span's `span_id`. The controller line intentionally has no routine log: log ownership matters more than proving that every layer ran.

## Canonical Correlated JSON Record

```json
{
  "level": 30,
  "time": 1786723200000,
  "msg": "User created",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "trace_flags": "01",
  "otel.event.name": "user.created",
  "code.function.name": "UserService.create",
  "com.example.api.target.user.id": "user-456",
  "com.example.api.request.id": "req-123",
  "com.example.api.code.layer": "service",
  "com.example.api.operation.name": "user.create"
}
```

Field ownership:

| Fields | Source |
| --- | --- |
| `level`, `time`, `msg` | Example logging transport |
| `trace_id`, `span_id`, `trace_flags`, contextual `user.id` | OpenTelemetry/runtime context |
| `otel.event.name`, `code.function.name` | Caller, using OpenTelemetry semantic conventions |
| `com.example.api.*`, including target entity IDs | Explicit application convention |

When logs are emitted directly through the OpenTelemetry Logs API, populate the native `EventName`, `TraceId`, and `SpanId` fields instead of compatibility JSON attributes.

## Factory Pattern

```typescript
// modules/user/factories/create-user.factory.ts

export function makeCreateUserUseCase(): CreateUserUseCase {
  return new CreateUserUseCase(
    makeUserService(),
    getContainer().appLogger,
  );
}

export function makeCreateUserController(): ICreateUserController {
  return new CreateUserController(
    makeCreateUserUseCase(),
  );
}
```

The observability-aware logger is a shared infrastructure dependency. Request-specific fields come from the active async scope, so the factory remains transport-independent.

## Testing

Inject a spy or no-op logger in unit tests:

```typescript
const logger = createLoggerSpy();
const service = new UserService(userRepository, logger);

await service.create(input);

expect(logger.info).toHaveBeenCalledWith(
  {
    "otel.event.name": "user.created",
    "code.function.name": "UserService.create",
    [APP_ATTRIBUTES.targetUserId]: "user-1",
  },
  "User created",
);
```

Transport integration tests should additionally assert:

- an error response contains `requestId`;
- request start/end logs share the same namespaced request-ID attribute;
- `trace_id` and `span_id` are included when tracing is enabled;
- concurrent requests do not leak context into one another.

Test the adapter separately from use cases:

```typescript
vi.mocked(getObservabilityContext).mockReturnValue({
  requestId: "req-1",
  traceId: "4bf92f3577b34da6a3ce929d0e0e4736",
  spanId: "00f067aa0ba902b7",
  traceFlags: "01",
});

appLogger.info({}, "Test record");

expect(pino.info).toHaveBeenCalledWith(
  expect.objectContaining({
    trace_id: "4bf92f3577b34da6a3ce929d0e0e4736",
    span_id: "00f067aa0ba902b7",
    trace_flags: "01",
    [APP_ATTRIBUTES.requestId]: "req-1",
  }),
  "Test record",
);
```

## Checklist

- [ ] `AppLogger` is a vendor-neutral interface
- [ ] The concrete logger is confined to the infrastructure adapter
- [ ] Factories inject `AppLogger` into services/use cases that log
- [ ] Request observability scope is established at every transport boundary
- [ ] `requestId` is camelCase in API responses and namespaced in operational logs
- [ ] JSON logs use `trace_id`, `span_id`, and `trace_flags`
- [ ] `traceId` and `spanId` runtime values come from the active OpenTelemetry span
- [ ] Compatible JSON events use `otel.event.name` so they can map to OpenTelemetry `EventName`
- [ ] Custom fields use the configured company/application namespace, never `app.*` or `otel.*`
- [ ] Observability fields are not stored in transaction types
- [ ] Workers use a new invocation ID; origin request correlation uses `causationRequestId`
- [ ] Queue adapters propagate/extract trace carriers without reusing stale span IDs
- [ ] Product analytics uses its own interface
- [ ] Sensitive fields are redacted before export

## References

- [Logging](./logging.md)
- [Product Analytics](./product-analytics.md)
- [Transaction Management](./transaction.md)
- [Error Handling](./error-handling.md)
