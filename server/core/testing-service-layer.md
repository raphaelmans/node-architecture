# Server Layer Testability Standard

> Canonical testing standard for framework-adapter/controller/usecase/service/repository layers.

## Folder Structure: `__tests__` Mirror Layout

All test files live in `src/__tests__/` and mirror the source tree exactly.
Never colocate test files next to source files.

```text
src/
  __tests__/
    app/
      api/
        <resource>/
          route.test.ts                  # Next.js adapter behavior
    lib/
      modules/
        <module>/
          <module>.router.test.ts       # tRPC adapter behavior
          controllers/
            <capability>.controller.test.ts # mapping + delegation
          services/
            <module>.service.test.ts    # domain rules, SRP behavior
          repositories/
            <module>.repository.test.ts # persistence contract, query semantics
          use-cases/
            <capability>.use-case.test.ts # orchestration (when present)
          shared/
            contracts/
              <capability>.contract.test.ts # canonical wire schema tests
            domain.test.ts              # shared pure domain rules
      shared/
        infra/
          http/
            error-handler.test.ts
```

Navigation rule: `src/lib/modules/<module>/services/<module>.service.ts` → `src/__tests__/lib/modules/<module>/services/<module>.service.test.ts`.

## Architecture Flow (Canonical)

The server flow is:

```text
framework adapter -> controller
                         ├─> service -> repository/provider
                         └─> usecase -> service(s) -> repository/provider(s)
```

Where:

- `framework adapter` handles transport/framework concerns
- `controller` is framework-neutral and maps the public capability boundary
- `usecase` is optional and only used for complex orchestration/side effects
- `service` owns SRP domain logic
- `repository` owns persistence logic

## MUST Rules

These are mandatory for new and modified modules.

- Dependencies across controller/usecase/service/repository boundaries MUST be interface-based.
- Constructors in controller, service, and usecase classes MUST accept interface types, not concrete classes.
- Each module MUST have layer-appropriate tests for all implemented layers.
- Test doubles MUST be used at boundaries to keep layer tests isolated and deterministic.
- External/provider boundaries MUST include contract/regression tests with fixtures where applicable.

## TDD Behavioral Testing with Stubbed Boundaries

Service-layer development MUST follow red-green-refactor with vertical slices:

- RED: write one failing behavior test at the owning layer boundary.
- GREEN: implement the minimum change needed to pass that test.
- REFACTOR: improve structure only after GREEN while preserving existing behavior assertions.

Execution rules:

- New or changed behavior MUST start with a failing test in the owning layer (`controller`, `usecase`, `service`, or `repository`).
- Tests MUST assert behavior through public layer interfaces/service functions, not private methods.
- Tests in this phase MUST remain deterministic and offline by stubbing external boundaries (for example Supabase) via test doubles.
- Tests MUST NOT depend on live external infrastructure (live DB/server/provider) in the development loop.
- Internal call-count/order assertions SHOULD be avoided unless ordering is itself the behavior under test.
- Bug fixes MUST start with a failing regression test/fixture before implementation.
- Horizontal slicing (all tests first, all code later) MUST NOT be used.

## Required Test Matrix

| Layer | Required tests | Typical doubles |
| --- | --- | --- |
| Shared API contract | representative valid/invalid wire payloads, sensitive-field exclusion, serialization boundaries | no doubles; table-driven Zod parsing |
| Framework adapter | malformed-body/input validation, envelope/error mapping, boundary auth/rate-limit/observability behavior | controller stub returned by a mocked controller factory |
| Controller | input-to-command and actor mapping, null-to-domain-error decisions, exactly one downstream call, public response mapping | use-case or service interface stub/spy |
| Use Case (if present) | orchestration sequence, transaction boundaries, side effects order | spies/mocks for service interfaces |
| Service | domain rules, SRP behavior, null/not-found semantics, transaction participation decisions | fakes/stubs for repositories + tx manager |
| Repository | query/persistence contract, transaction context handling, null behavior | integration harness or DB test doubles |
| Observability/analytics adapters | context isolation, structured fields, vendor mapping, partial destination failure | logger/analytics spies and fixture-backed adapter tests |

## Test Doubles Policy (Global)

Use these definitions consistently across server modules:

- **Stub**: fixed response
- **Spy**: records calls for assertions
- **Mock**: strict call expectations
- **Fake**: simplified working implementation (often in-memory)

Default preference:

1. fixtures + fakes/stubs
2. spies for interaction checks
3. mocks only when strict interaction verification is necessary

## Fixtures + Regression Policy

For boundary contracts (transport/provider/adapter payloads), maintain fixtures:

- `golden` (representative valid sample)
- `minimal` (smallest valid sample)
- `invalid-*` (expected failures)

Bugfix rule:

- each bug fix MUST add/adjust a fixture or test case that would have caught the bug.

The shared Zod payload contract is tested once in `src/__tests__/lib/modules/<module>/shared/contracts/`. Client and server transport tests verify envelope + payload integration with that schema but do not maintain competing copies of its validation cases.

## Contract Testing Scope

Contract/regression tests are REQUIRED when modules cross unstable boundaries, including:

- external payload contracts (for example webhook/provider payloads)
- adapter contracts (storage/auth/transport boundaries)
- scheduler/cron route boundary contracts
- rate-limit and auth enforcement boundaries

## Dual-Transport Parity (tRPC + OpenAPI)

When a capability is exposed in both transports during migration, parity tests are REQUIRED.

- Same input validation semantics
- Same business outcome semantics
- Same error category/code semantics
- Same auth/rate-limit boundary semantics

See `../runtime/nodejs/libraries/openapi/parity-testing.md`.

## Profile Endpoint Test Visualization

Create profile is orchestration-heavy and should be tested through a use case boundary.

```text
create profile path

framework adapter (tRPC, Next.js, Express, Hono, or OpenAPI)
  -> CreateProfileController
    -> CreateProfileUseCase
      -> UserService (resolve/validate user.userId)
      -> ProfileService
          -> ProfileRepository
```

Update profile is single-service and should be tested as controller->service path.

```text
update profile path

framework adapter (tRPC, Next.js, Express, Hono, or OpenAPI)
  -> UpdateProfileController
    -> ProfileService
      -> ProfileRepository
```

Recommended test split:

- `CreateProfileUseCase` unit tests: orchestration order, tx boundary, user dependency behavior
- `CreateProfileController` unit tests: public input/actor mapping and public response mapping
- `ProfileService` unit tests: update rules and repository interaction
- transport adapter tests: input/error mapping for each endpoint/procedure

## Layer-Specific Guidance

### Framework Adapter

- Test procedure/handler delegation separately from the real HTTP boundary.
- Test request parsing and schema validation through the real HTTP adapter.
- Test known domain errors and unknown errors map to serialized response contracts.
- Test response-schema drift is sanitized as an internal error, not reported as client validation failure.
- Do not test command mapping or business rules here; stub the controller.

#### Procedure test: `createCaller` + factory mock

Router tests use `vi.mock` at the module level to replace factory functions, then invoke procedures via `createCaller`:

```typescript
vi.mock("@/modules/reservation/factories/reservation.factory", () => ({
  makeGetReservationController: vi.fn(),
}));

describe("reservationRouter", () => {
  it("returns reservation on success", async () => {
    // Arrange
    const fakeContext = createFakeContext({ userId: "user-1" });
    const caller = reservationRouter.createCaller(fakeContext);
    const controllerStub = {
      execute: vi.fn().mockResolvedValue(mockReservationResponse),
    } as IGetReservationController;
    vi.mocked(makeGetReservationController).mockReturnValue(
      controllerStub,
    );

    // Act
    const result = await caller.getById({ id: "res-1" });

    // Assert
    expect(GetReservationResponseSchema.parse(result.data)).toEqual(
      expect.objectContaining({ id: "res-1" }),
    );
  });
});
```

Rules:
- Mock controller factory functions, not controller/service/use-case constructors
- Use `createCaller(fakeContext)` to invoke procedures without HTTP
- Assert procedure input, controller delegation, and the success envelope
- Do not claim `createCaller` verifies the HTTP adapter, context factory,
  request observability scope, raw-body parsing, or serialized `errorFormatter`

#### HTTP adapter integration test

Exercise the actual fetch/Express/Hono entrypoint for transport behavior:

```typescript
it("serializes a known domain error with request correlation", async () => {
  vi.mocked(makeGetReservationController).mockReturnValue({
    execute: vi.fn().mockRejectedValue(new ReservationNotFoundError("res-1")),
  });

  const response = await fetchTestServer("/api/reservations/res-1", {
    headers: { "x-request-id": "trusted-test-request" },
  });

  expect(response.status).toBe(404);
  await expect(response.json()).resolves.toMatchObject({
    code: "RESERVATION_NOT_FOUND",
    requestId: expect.any(String),
  });
});
```

The HTTP-adapter suite owns malformed JSON/encoding, authentication attachment,
observability setup, request-ID propagation, envelope serialization, and safe
unknown-error behavior. A tRPC HTTP test must call its fetch handler or a test
server—not `createCaller`—when asserting `errorFormatter` output.

### Controller

- Test with plain contract/application values; do not construct framework requests or tRPC context.
- Stub the one service or use-case interface selected by the controller.
- Verify public input and actor values map to the expected internal command.
- Verify capability-level `null` becomes the correct typed domain error.
- Verify internal entities/results map to the shared response shape, including serialization such as `Date` to ISO strings.
- Keep transaction, orchestration, and domain-rule assertions in the owning use-case/service tests.

### Use Case

- Verify orchestration decisions, call ordering, and side-effect timing.
- Verify transaction scope boundaries (inside vs outside tx work).
- Use service interface doubles; no DB/network dependencies in usecase unit tests.
- Inject `AppLogger` and `ProductAnalytics` spies when the use case emits operational logs or product events.
- Assert structured fields and typed events; do not depend on Pino, Mixpanel, or Google Analytics in unit tests.

### Service

- Test pure domain rules and branching.
- Test behavior with repository returning null/conflict/existing states.
- Test transaction participation (`options.tx` path) vs self-owned transactions.

**Concrete Pattern: Harness Factory**

Service tests use a `createHarness()` function that wires up all dependencies as stubs:

```typescript
function createHarness(overrides?: Partial<HarnessOptions>) {
  const reservationRepo = {
    findById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    ...overrides?.reservationRepo,
  };
  const transactionManager = {
    run: vi.fn((fn) => fn({})),
    ...overrides?.transactionManager,
  };

  const service = new ReservationService(
    reservationRepo as IReservationRepository,
    transactionManager as TransactionManager,
  );

  return { service, reservationRepo, transactionManager };
}
```

This provides typed partial stubs for all repository dependencies without touching the DB. Helper functions like `toEntityRecord(partial)` construct test entity records from partial data typed against real schema types.

### Repository

- Validate persistence semantics and query filters.
- Validate `options.tx` vs base client usage.
- Keep domain rule assertions out of repository tests.

### Logging and Product Analytics

Keep the ports independent in tests:

```typescript
const logger = createLoggerSpy();
const analytics = createProductAnalyticsSpy();

const useCase = new CreateUserUseCase(
  userService,
  logger,
  analytics,
);

await useCase.execute(input);

// `user.created` belongs to UserService; the use-case test does not require a
// duplicate log from CreateUserUseCase.
expect(analytics.track).toHaveBeenCalledWith({
  name: "user_created",
  userId: "user-1",
  properties: { signupMethod: "email" },
});
```

Required boundaries:

- A logger failure must not change business behavior.
- A direct analytics delivery failure must not fail a committed business operation.
- Composite analytics tests verify that one rejected destination does not prevent the others.
- Outbox tests verify the domain write and analytics delivery intent commit or roll back together.
- Async observability integration tests verify concurrent requests do not share `requestId`, `traceId`, or `spanId`.

## Anti-Patterns

- Over-mocking internals instead of asserting behavior
- Testing service logic through controller tests only
- Testing controller mapping through framework-adapter tests only
- Mocking service/use-case factories in framework-adapter tests instead of the controller factory
- Skipping fixtures for unstable boundary contracts
- Using concrete class dependencies that block isolated unit tests
- Asserting fragile log message strings instead of structured fields
- Horizontal slicing (bulk test writing followed by bulk implementation) instead of one behavior per red-green loop

## Related Docs

- `./conventions.md`
- `./controllers.md`
- `./transaction.md`
- `./error-handling.md`
- `./observability.md`
- `./product-analytics.md`
- `./rate-limiting.md`
- `./webhook/testing/README.md` (specialized extension for webhook domain)
- `client/core/testing.md` (shared concepts: AAA pattern, test doubles policy, anti-patterns, naming convention)
- `https://github.com/mattpocock/skills/tree/main/tdd` (optional reference workflow for red-green-refactor execution)
