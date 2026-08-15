# Client Composition Root and Factories

> Core standard for constructing dependency-heavy client infrastructure with explicit ownership and testable lifetimes.

## Core Decision

Use factories for dependency-heavy, swappable infrastructure:

- `createAppLogger`
- `createProductAnalytics`
- `createClientApi`
- `create<Feature>Api`

Assemble them once in a client composition root. The composition root owns construction order and lifecycle; feature modules consume specific ports and never construct providers or receive the complete runtime container.

## Dependency Direction

```text
composition root
  |
  +-- createAppLogger(sinks, context, redaction, sampling)
  +-- createProductAnalytics(adapters, consent, logger)
  +-- createClientApi(transport, logger)
  +-- createProfileApi(clientApi, toAppError, logger)
  +-- createBillingApi(clientApi, toAppError, logger)
```

The container/object returned during assembly is private to the composition root. Inject only the dependency a consumer declares:

```ts
createProfileApi({ clientApi, toAppError, logger });

// Do not:
createProfileApi({ runtime });
```

## Factory Boundaries

Factories own:

- provider/vendor construction;
- adapter and wrapper composition;
- environment-specific strategy selection;
- dependency validation;
- safe defaults; and
- lifecycle setup/cleanup when required.

Factories return application ports, not vendor SDK types:

```ts
export function createAppLogger(config: LoggerConfig): AppLogger;
export function createProductAnalytics(
  config: AnalyticsConfig,
): ProductAnalytics;
export function createClientApi(deps: ClientApiDeps): IClientApi;
export function createProfileApi(deps: ProfileApiDeps): IProfileApi;
```

## Lifetime Rules

| Runtime | Default lifetime | Rule |
| --- | --- | --- |
| Browser | application-scoped single instance | Compose once; reuse logger, analytics, transport, and feature APIs |
| SSR | application-scoped when stateless | Safe only when the dependency contains no request/user context |
| SSR | request-scoped when contextual | Create per request when headers, cookies, actor, request ID, or trace context are captured |
| Unit test | per test | Build through the same factories with spies/fakes/no-op adapters |

Never store request/user context in an application-scoped SSR singleton. Contextual logging may read from request-local runtime context, but any dependency that closes over request values is request-scoped.

## Browser Composition Root

```ts
// src/common/runtime/browser.ts
export function createBrowserRuntime(config: BrowserRuntimeConfig) {
  const logger = createAppLogger({
    sinks: createBrowserLogSinks(config),
    context: createBrowserLogContext(config),
    redaction: defaultClientRedaction,
  });

  const analytics = createProductAnalytics({
    adapters: createAnalyticsAdapters(config),
    consent: config.consent,
    logger,
  });

  const clientApi = createClientApi({
    transport: createBrowserTransport(config),
    logger,
  });

  const profileApi = createProfileApi({
    clientApi,
    toAppError,
    logger: logger.child("profile:api"),
  });

  return { logger, analytics, clientApi, profileApi };
}
```

Cache the browser runtime only in this composition-root module:

```ts
let browserRuntime: ReturnType<typeof createBrowserRuntime> | undefined;

function getBrowserRuntime() {
  browserRuntime ??= createBrowserRuntime(readPublicRuntimeConfig());
  return browserRuntime;
}

export const getAppLogger = () => getBrowserRuntime().logger;
export const getProductAnalytics = () => getBrowserRuntime().analytics;
export const getClientApi = () => getBrowserRuntime().clientApi;
export const getProfileApi = () => getBrowserRuntime().profileApi;
```

Only the composition-root module can access the complete runtime object. Other modules import specific accessors.

Feature modules must not implement their own hidden singletons.

## Supplying Dependencies to UI Frameworks

Framework integration may expose specific stable ports created by the composition root:

```ts
registerAnalyticsPort(getProductAnalytics());
registerProfileApi(getProfileApi());
```

Prefer feature API runtime modules that re-export a composition-root-owned instance or accessor. They remain stable test-mock targets but do not construct the singleton themselves.

Do not expose `useRuntime()` returning every dependency. That is a service locator and hides actual dependencies.

## SSR / Request Composition

```ts
export function createRequestRuntime(input: RequestRuntimeInput) {
  const logger = createAppLogger({
    sinks: input.sinks,
    context: createRequestLogContext(input.headers),
    redaction: defaultClientRedaction,
  });

  const clientApi = createClientApi({
    transport: createServerTransport(input),
    logger,
  });

  return {
    logger,
    profileApi: createProfileApi({ clientApi, toAppError, logger }),
  };
}
```

Only use request scope when request context is required. Stateless schema registries, pure configuration, and safe vendor clients may remain application-scoped.

## Testing

Tests call the same factories with test adapters:

```ts
const logSink = createLogSinkSpy();
const analyticsAdapter = createAnalyticsSpyAdapter();

const logger = createAppLogger({
  sinks: [logSink],
  context: createFixedLogContext(),
  redaction: defaultClientRedaction,
});

const analytics = createProductAnalytics({
  adapters: [analyticsAdapter],
  consent: allowAllConsent,
  logger,
});

const clientApi = createClientApi({ transport: fakeTransport, logger });
const profileApi = createProfileApi({ clientApi, toAppError, logger });
```

This tests the same construction seams used by production without loading live vendors.

## Do Not Add Factories For

- UI components (including React components);
- Zod schemas;
- pure domain/helpers;
- simple hooks with no construction lifecycle; or
- plain immutable value objects.

A factory is justified by dependency composition, runtime strategy, lifecycle, or test substitution—not by naming preference.

## Checklist

- [ ] Dependency-heavy infrastructure is created through named factories
- [ ] One composition root owns browser application-scoped instances
- [ ] SSR dependencies are request-scoped only when they capture request context
- [ ] Request/user state never leaks into an SSR application singleton
- [ ] Consumers receive specific ports, never the complete runtime container
- [ ] Provider/vendor construction remains inside factories/adapters
- [ ] Feature modules do not create hidden singletons
- [ ] Tests use the same factories with spies, fakes, or no-op adapters
- [ ] Components, schemas, pure helpers, and simple hooks do not get unnecessary factories

## Related Docs

- [Client Architecture](./architecture.md)
- [Client API Architecture](./client-api-architecture.md)
- [Operational Logging](./logging.md)
- [Product Analytics](./product-analytics.md)
- [Testing](./testing.md)
