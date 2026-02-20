# Service Layer Testability Standard

> Canonical testing standard for controller/usecase/service/repository layers.

## Folder Structure: `__tests__` Mirror Layout

All test files live in `src/__tests__/` and mirror the source tree exactly.
Never colocate test files next to source files.

```text
src/
  __tests__/
    modules/
      <module>/
        <module>.controller.test.ts   # input validation, error mapping
        <module>.service.test.ts      # domain rules, SRP behavior
        <module>.repository.test.ts   # persistence contract, query semantics
        <module>.usecase.test.ts      # orchestration (if usecase layer present)
    common/
      errors/
        error-handler.test.ts
    lib/
      modules/
        <module>/
          shared/
            domain.test.ts            # shared pure domain rules
```

Navigation rule: `src/modules/<module>/<module>.service.ts` → `src/__tests__/modules/<module>/<module>.service.test.ts`.

## Architecture Flow (Canonical)

The server flow is:

`controller -> usecase (optional) -> service -> repository`

Where:

- `controller` handles transport concerns
- `usecase` is optional and only used for complex orchestration/side effects
- `service` owns SRP domain logic
- `repository` owns persistence logic

## MUST Rules

These are mandatory for new and modified modules.

- Dependencies across service/usecase/repository boundaries MUST be interface-based.
- Constructors in service and usecase classes MUST accept interface types, not concrete classes.
- Each module MUST have layer-appropriate tests for all implemented layers.
- Test doubles MUST be used at boundaries to keep layer tests isolated and deterministic.
- External/provider boundaries MUST include contract/regression tests with fixtures where applicable.

## Required Test Matrix

| Layer | Required tests | Typical doubles |
| --- | --- | --- |
| Controller/Router | input validation, envelope/error mapping, boundary auth/rate-limit behavior | stubs/fakes for downstream calls |
| Use Case (if present) | orchestration sequence, transaction boundaries, side effects order | spies/mocks for service interfaces |
| Service | domain rules, SRP behavior, null/not-found semantics, transaction participation decisions | fakes/stubs for repositories + tx manager |
| Repository | query/persistence contract, transaction context handling, null behavior | integration harness or DB test doubles |

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

controller/router (tRPC or OpenAPI)
  -> CreateProfileUseCase
      -> UserService (resolve/validate user.userId)
      -> ProfileService
          -> ProfileRepository
```

Update profile is single-service and should be tested as controller->service path.

```text
update profile path

controller/router (tRPC or OpenAPI)
  -> ProfileService
      -> ProfileRepository
```

Recommended test split:

- `CreateProfileUseCase` unit tests: orchestration order, tx boundary, user dependency behavior
- `ProfileService` unit tests: update rules and repository interaction
- transport adapter tests: input/error mapping for each endpoint/procedure

## Layer-Specific Guidance

### Controller/Router

- Test request parsing and schema validation paths.
- Test known domain errors and unknown errors map to correct response contracts.
- Do not test business rules here; stub downstream service/usecase.

### Use Case

- Verify orchestration decisions, call ordering, and side-effect timing.
- Verify transaction scope boundaries (inside vs outside tx work).
- Use service interface doubles; no DB/network dependencies in usecase unit tests.

### Service

- Test pure domain rules and branching.
- Test behavior with repository returning null/conflict/existing states.
- Test transaction participation (`ctx.tx` path) vs self-owned transactions.

### Repository

- Validate persistence semantics and query filters.
- Validate `ctx.tx` vs base client usage.
- Keep domain rule assertions out of repository tests.

## Anti-Patterns

- Over-mocking internals instead of asserting behavior
- Testing service logic through controller tests only
- Skipping fixtures for unstable boundary contracts
- Using concrete class dependencies that block isolated unit tests
- Asserting fragile log message strings instead of structured fields

## Related Docs

- `./conventions.md`
- `./transaction.md`
- `./error-handling.md`
- `./rate-limiting.md`
- `./webhook/testing-overview.md` (specialized extension for webhook domain)
- `client/core/testing.md` (shared concepts: AAA pattern, test doubles policy, anti-patterns, naming convention)
