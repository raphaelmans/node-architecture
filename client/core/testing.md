# Unit Testing Standard (Client)

> Framework/library-agnostic. Applies to all client-side code regardless of test runner.
> For server-side layers see `server/core/testing-service-layer.md`.

The layout below is relative to the selected client app/package. In a monorepo, each activated package owns and verifies its tests; do not centralize package tests under another deployable application.

## Folder Structure: `__tests__` Mirror Layout

All test files live in a `__tests__/` directory that **mirrors the source tree exactly**.
Never colocate test files next to source files.

```text
src/
  __tests__/
    features/
      <feature>/
        api.test.ts          # <Feature>Api class, mocks injected IClientApi/toAppError/logger
        hooks.test.ts        # query adapter, mocks I<Feature>Api
        helpers.test.ts      # pure function tests (no mocks)
        sync.test.ts         # cache sync composition (if sync.ts exists)
        machines/            # XState guard/action tests (if machines/ exists)
          <machine>.guards.test.ts
          <machine>.actions.test.ts
    common/
      errors/
        error-adapter.test.ts
      query-keys/
        query-keys.test.ts
      logging/
        logger.test.ts
        adapters/
          debug.test.ts
          sentry.test.ts
      analytics/
        analytics.test.ts
      runtime/
        browser.test.ts
    lib/
      modules/
        <module>/
          shared/
            contracts/
              <capability>.contract.test.ts # shared wire schema acceptance/rejection
            domain.test.ts   # pure shared domain rules
            transform.test.ts
```

**Why mirroring:** navigating between source and test is mechanical — replace
`src/` with `src/__tests__/` and append `.test.ts`. No guessing, no scrolling.

## Test Anatomy: AAA Pattern

Every test follows **Arrange → Act → Assert**, one behavioral assertion per test.

```typescript
it("throws the normalized AppError when clientApi rejects", async () => {
  // Arrange
  const appError: AppError = {
    kind: "network",
    message: "Unable to reach the service",
  };
  const clientApi = stubClientApi({ rejects: networkError });
  const toAppError = () => appError;
  const logger = createLoggerSpy();
  const api = createFeatureApi({ clientApi, toAppError, logger });

  // Act + Assert: rejection is the observable behavior.
  await expect(api.fetchItem("id-1")).rejects.toEqual(appError);
});
```

Rules:
- One `Act` section per test. Multiple acts = split into separate tests.
- Name tests as `"<subject> <condition> <expected outcome>"`.
- Prefer `describe` blocks per class or module, `it` blocks per behavior.

## TDD Behavioral Testing with Stubbed Boundaries

Follow red-green-refactor with vertical slices:

- RED: write one failing behavior test.
- GREEN: write the minimum implementation to pass.
- REFACTOR: improve internals only after GREEN while preserving behavior assertions.

Rules:
- Tests SHOULD describe what the system does through public interfaces and service functions, not internal implementation.
- Tests in this phase SHOULD be deterministic and offline by stubbing external boundaries (for example Supabase) with test doubles.
- Tests MUST NOT call live server/database infrastructure in the development loop.
- Tests MUST NOT target private methods.
- Avoid internal call-count/order assertions unless interaction order is itself the behavior under test.
- Do not horizontal-slice work (all tests first, all implementation later); keep one behavior per red-green cycle.

## Pure Function Tests (domain.ts / helpers.ts)

No mocks. No network. No framework runtime. Use **table-driven cases**.

```typescript
describe("calcLedgerBreakdown", () => {
  const cases = [
    {
      label: "distributes evenly across equal records",
      input: [{ amount: 50 }, { amount: 50 }],
      expected: [{ pct: 50 }, { pct: 50 }],
    },
    {
      label: "returns empty array for no records",
      input: [],
      expected: [],
    },
    {
      label: "rounds to two decimal places",
      input: [{ amount: 1 }, { amount: 2 }],
      expected: [{ pct: 33.33 }, { pct: 66.67 }],
    },
  ];

  for (const { label, input, expected } of cases) {
    it(label, () => {
      expect(calcLedgerBreakdown(input)).toEqual(expected);
    });
  }
});
```

Rules:
- Cover edge conditions: empty input, zero values, boundary values, type coercions.
- Order cases by readable behavior groups; do not couple the test table to private branching order.
- Name `label` as the scenario, not the assertion.

## Shared Contract Tests (`shared/contracts/`)

Test canonical Zod wire contracts once in the mirrored shared-contract test path.

Rules:

- Assert representative valid request and response payloads.
- Assert sensitive/internal fields are not part of serialized responses.
- Cover wire-specific boundaries such as UUIDs, pagination, enums, nullable values, and ISO datetimes.
- Do not duplicate the same schema acceptance tests in client and server suites; both runtimes import the same schema.
- Transport tests should still verify that the route and `featureApi` actually invoke the shared contract boundary.

## Dependency-Injected Tests (api.ts classes)

Test `<Feature>Api` by mocking **only its injected dependencies**, not internals.

```typescript
describe("FeatureApi.fetchItem", () => {
  it("returns parsed data on success", async () => {
    // Arrange
    const raw = { id: "1", name: "Item" };
    const expected: FeatureItem = { id: "1", name: "Item" };
    const clientApi = stubClientApi({ resolves: raw });
    const logger = createLoggerSpy();
    const api = createFeatureApi({ clientApi, toAppError, logger });

    // Act
    const result = await api.fetchItem("1");

    // Assert
    expect(result).toEqual(expected);
  });

  it("throws the normalized AppError when transport fails", async () => {
    // Arrange
    const error = new Error("network");
    const clientApi = stubClientApi({ rejects: error });
    const appError: AppError = {
      kind: "network",
      message: "Unable to reach the service",
      cause: error,
    };
    const toAppError = (_error: unknown) => appError;
    const logger = createLoggerSpy();
    const api = createFeatureApi({ clientApi, toAppError, logger });

    // Act + Assert
    await expect(api.fetchItem("1")).rejects.toEqual(appError);
  });
});
```

Rules:
- Mock at the injected interface boundary — not at the HTTP client or fetch level.
- Do not repeat the schema's full acceptance/rejection matrix here; schema-specific tests own that behavior.
- Do verify boundary integration: the API parses representative responses and maps a rejected response parse to the expected normalized contract error.
- Assert returned values, not internal implementation details.
- Inject a no-op/spy logger when required; assert records only for boundary-owned diagnostics, not provider formatting.

## Hook / Query Adapter Tests (hooks.ts)

Mock `I<Feature>Api`, not transport providers or network clients.

```typescript
describe("useQueryFeatureItem", () => {
  it("exposes data from api.fetchItem", async () => {
    // Arrange
    const api = fakeFeatureApi({ fetchItem: async () => mockItem });

    // Act
    const { result } = renderHook(() => useQueryFeatureItem("id-1", { api }));
    await waitForQuery(result);

    // Assert
    expect(result.current.data).toEqual(mockItem);
  });
});
```

Rules:
- Use a fake `I<Feature>Api` implementation, not a mock of the class.
- Verify cache invalidation and query key usage if they are behavioral decisions.
- Do not assert network calls — that belongs in `api.test.ts`.
- Use a `ProductAnalytics` spy when the mutation/workflow owns a typed event; assert completion events occur once after success and never after failure.

## Logging and Product Analytics Tests

Application tests use ports, never live providers:

- logger spy/no-op for `AppLogger`;
- analytics spy/fake for `ProductAnalytics`;
- no `debug`, Sentry, or analytics vendor network calls.

Adapter tests separately cover enrichment, redaction, filtering/sampling, consent, identity/reset, and non-fatal sink failures. A test should fail if a delivery adapter can reject the business workflow.

## Factory and Composition-Root Tests

Call the same named factories used by production:

```ts
const logger = createAppLogger({ sinks: [logSinkSpy], context: fixedContext });
const analytics = createProductAnalytics({
  adapters: [analyticsSpy],
  consent: allowAllConsent,
  logger,
});
const clientApi = createClientApi({ transport: fakeTransport, logger });
const api = createFeatureApi({ clientApi, toAppError, logger });
```

Verify:

- browser composition creates stable application-scoped instances;
- request composition does not leak request/user context between invocations;
- consumers receive specific ports rather than the full runtime container; and
- provider construction remains behind factories.

## Test Doubles Policy

Use these definitions consistently:

| Double | Definition | When to use |
| --- | --- | --- |
| **Stub** | Returns fixed responses | Simple success/failure paths |
| **Spy** | Records calls for assertion | Verifying a dependency was called with correct args |
| **Mock** | Strict call expectations | When call order or call count is the behavior |
| **Fake** | Working in-memory implementation | Interface-level doubles (e.g., `I<Feature>Api`) |

**Default preference:**

1. Fakes/stubs for happy path and data-path tests.
2. Spies when interaction (call count, args) is the subject.
3. Mocks only for strict sequence/ordering verification.

Never mock:
- Pure functions in `domain.ts` / `helpers.ts`
- Zod schemas
- Standard library utilities

## Test File Naming

| Source file | Test file |
| --- | --- |
| `api.ts` | `api.test.ts` |
| `hooks.ts` | `hooks.test.ts` |
| `domain.ts` | `domain.test.ts` |
| `helpers.ts` | `helpers.test.ts` |
| `shared/domain.ts` | `__tests__/.../shared/domain.test.ts` |

Test description convention:

```text
describe("<ClassName or moduleName>")
  describe("<methodName or functionName>")
    it("<condition> → <expected outcome>")
```

## Anti-Patterns

- **Mocking internals**: assert behavior via the public API, not private calls.
- **Over-specifying**: asserting exact argument shapes on stubs that don't affect output.
- **Testing multiple behaviors in one `it`**: split when you see multiple `act` sections.
- **Mixing layer concerns**: service logic assertions inside server framework-adapter/controller tests or client hook tests.
- **Duplicating invariant tests**: shared domain rules tested once in `shared/`; client and server do not repeat them.
- **Fragile snapshot tests for logic**: use explicit value assertions for behavioral tests.
- **Horizontal slicing**: writing all tests up front and then implementing in bulk; prefer one behavior per red-green loop.
- **Live telemetry in unit tests**: loading `debug`, Sentry, or analytics vendors instead of spies/fakes.
- **Testing through a service locator**: obtaining every dependency from a runtime container instead of constructing the subject with specific ports.

## Related Docs

- `client/core/testing-vitest.md` — Vitest runner configuration, scripts, setup file
- `client/core/domain-logic.md` — pure function placement and testing strategy
- `client/core/client-api-architecture.md` — testability contract per layer
- `client/core/composition-root.md` — factory/lifetime test boundaries
- `client/core/logging.md` — operational logging adapter tests
- `client/core/product-analytics.md` — analytics event and delivery tests
- `client/core/folder-structure.md` — `__tests__` layout
- `server/core/testing-service-layer.md` — server-side layer testing standard
- `https://github.com/mattpocock/skills/tree/main/tdd` — optional reference workflow for red-green-refactor execution
