# Unit Testing Standard (Client)

> Framework/library-agnostic. Applies to all client-side code regardless of test runner.
> For server-side layers see `server/core/testing-service-layer.md`.

## Folder Structure: `__tests__` Mirror Layout

All test files live in a `__tests__/` directory that **mirrors the source tree exactly**.
Never colocate test files next to source files.

```text
src/
  __tests__/
    features/
      <feature>/
        api.test.ts          # <Feature>Api class, mocks clientApi + toAppError
        hooks.test.ts        # query adapter, mocks I<Feature>Api
        domain.test.ts       # pure function tests (no mocks)
        helpers.test.ts      # pure function tests (no mocks)
    common/
      errors/
        error-adapter.test.ts
      query-keys/
        query-keys.test.ts
    lib/
      modules/
        <module>/
          shared/
            domain.test.ts   # pure shared domain rules
            transform.test.ts
```

**Why mirroring:** navigating between source and test is mechanical — replace
`src/` with `src/__tests__/` and append `.test.ts`. No guessing, no scrolling.

## Test Anatomy: AAA Pattern

Every test follows **Arrange → Act → Assert**, one behavioral assertion per test.

```typescript
it("returns AppError when clientApi rejects", () => {
  // Arrange
  const clientApi = stubClientApi({ rejects: networkError });
  const api = new FeatureApi({ clientApi, toAppError });

  // Act
  const result = await api.fetchItem("id-1");

  // Assert
  expect(result).toEqual(AppError.from(networkError));
});
```

Rules:
- One `Act` section per test. Multiple acts = split into separate tests.
- Name tests as `"<subject> <condition> <expected outcome>"`.
- Prefer `describe` blocks per class or module, `it` blocks per behavior.

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
- Keep cases in source order matching the function's branching logic.
- Name `label` as the scenario, not the assertion.

## Dependency-Injected Tests (api.ts classes)

Test `<Feature>Api` by mocking **only its injected dependencies**, not internals.

```typescript
describe("FeatureApi.fetchItem", () => {
  it("returns parsed data on success", async () => {
    // Arrange
    const raw = { id: "1", name: "Item" };
    const clientApi = stubClientApi({ resolves: raw });
    const api = createFeatureApi({ clientApi, toAppError });

    // Act
    const result = await api.fetchItem("1");

    // Assert
    expect(result).toEqual(featureItemSchema.parse(raw));
  });

  it("returns AppError when transport fails", async () => {
    // Arrange
    const error = new Error("network");
    const clientApi = stubClientApi({ rejects: error });
    const toAppError = (e: unknown) => AppError.unknown(e);
    const api = createFeatureApi({ clientApi, toAppError });

    // Act
    const result = await api.fetchItem("1");

    // Assert
    expect(result).toBeInstanceOf(AppError);
  });
});
```

Rules:
- Mock at the injected interface boundary — not at the HTTP client or fetch level.
- Do not test Zod schema behavior here; that belongs in schema-specific tests.
- Assert returned values, not internal implementation details.

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
- **Mixing layer concerns**: service logic assertions inside controller/hook tests.
- **Duplicating invariant tests**: shared domain rules tested once in `shared/`; client and server do not repeat them.
- **Fragile snapshot tests for logic**: use explicit value assertions for behavioral tests.

## Related Docs

- `client/core/domain-logic.md` — pure function placement and testing strategy
- `client/core/client-api-architecture.md` — testability contract per layer
- `client/core/folder-structure.md` — `__tests__` layout
- `server/core/testing-service-layer.md` — server-side layer testing standard
