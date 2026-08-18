# Testing Slice

Use this slice for server test placement, behavioral tests by layer, test doubles, real database/provider boundaries, webhook fixtures and simulators, transaction tests, and tRPC/OpenAPI parity.

## Mirror the Source Tree

Keep tests under a mirrored `src/__tests__/` tree:

```text
src/lib/modules/user/controllers/create-user.controller.ts
src/lib/modules/user/use-cases/create-user.use-case.ts
src/lib/modules/user/repositories/user.repository.ts

src/__tests__/lib/modules/user/controllers/create-user.controller.test.ts
src/__tests__/lib/modules/user/use-cases/create-user.use-case.test.ts
src/__tests__/lib/modules/user/repositories/user.repository.test.ts
```

Use Arrange, Act, Assert; one observable behavior per test; and deterministic doubles. Test public boundaries, not private methods.

## Test by Layer

- Contract: representative valid/invalid wire values and serialization; own the full schema matrix once.
- Framework adapter: real framework request/response integration with a stub controller; assert extraction, validation normalization, authentication/coarse-gate/rate-limit behavior, status/envelope, and one controller call.
- Controller: stub one service/use case; assert input/actor mapping, null-to-domain-error policy, and public response mapping.
- Use case: fake/stub ports; assert orchestration, transaction boundary, outbox/post-commit ordering, compensation, logs, and analytics ownership.
- Service: fake repositories/providers; assert domain policy, ownership/tenant/operation-specific capability authorization, and self-contained reads/writes.
- Repository: real test database when SQL, constraints, transaction visibility, upserts, or concurrency matter.
- Runtime adapter: assert provider mapping, redaction, retry/failure policy, and translated error causes without live network access.

Do not repeat a contract's entire validation matrix in every adapter. Prove that each adapter invokes the contract and maps failure correctly.

For Hono, include a type-checked adapter test for the shared error-status
mapping and its 500 fallback. For OAuth callbacks, cover a backslash-normalized
external `next` value, an ordinary safe relative path, a missing code, and a
rejected/expired code; every failure redirect must remain on the configured
application origin.

## Test Doubles

- Fake: working in-memory port; preferred for services/use cases.
- Stub: fixed success/failure response.
- Spy: records calls when count/arguments are behavior.
- Mock: strict interaction expectation only when ordering is essential.
- Simulator: controlled provider-like system for integration/contract scenarios.

Never mock pure functions, Zod schemas, or standard-library behavior. Do not make unit tests call live databases, Supabase, queues, webhook providers, analytics, or logging vendors.

## Transactions and Concurrency

Unit-test transaction ownership with a fake `TransactionManager` that supplies an opaque context. Use a real database for rollback, exact constraint translation, transaction participation, atomic upsert, and concurrent webhook delivery.

Webhook idempotency requires a concurrency test that delivers the same event simultaneously and proves one business effect. A sequential fake-repository test cannot establish that property.

## Webhook Matrix

Cover raw signature verification, base and event-specific schema validation, registry routing, mapping, duplicate delivery, unknown-event acknowledged skip, retryable/permanent failures, safe logging, and the standard envelope.

Store regression fixtures by provider and event type. Keep fixtures minimal, deterministic, sanitized, and labeled with provider/version provenance. A vendor simulator emits realistic callbacks but does not replace schema fixtures or real route tests.

## Transport Parity

`createCaller` tests tRPC procedures only. It does not prove HTTP context creation, raw parsing, observability, headers/cookies, or serialized formatter output; cover those with real HTTP adapter tests.

When tRPC and OpenAPI coexist, run the same fixtures through both transports and compare payloads, authorization, app error codes, safe details, and side effects. Allow only deliberate transport differences such as HTTP status versus tRPC code.

## Review Checklist

- Test paths mirror source paths.
- Each layer is tested through its public boundary with the next dependency stubbed/faked.
- Repositories use a real database for database-owned guarantees.
- Framework adapters have real HTTP/request tests.
- Redirect tests assert the final parsed origin, not only a path prefix.
- Webhook concurrency is proven atomically.
- tRPC procedure tests are not mislabeled as HTTP integration tests.
- Telemetry assertions target stable app-facing fields and ownership.
- No unit test reaches live infrastructure.

## Derivation Sources

Derived from the server layer-testing standard, webhook testing suite, transaction testing, OpenAPI parity, and runtime adapter test guidance. Exact paths and fingerprints are maintained outside the portable skill package.
