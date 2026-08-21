# Testing Slice

Use this slice for client test layout, behavioral unit tests, test doubles, feature API/query adapter tests, telemetry tests, composition-root tests, and Vitest configuration.

## Contents

- [Mirror layout](#mirror-layout)
- [Behavioral style](#behavioral-style)
- [Test by boundary](#test-by-boundary)
- [Factories and telemetry](#factories-and-telemetry)
- [Vitest baseline](#vitest-baseline)
- [Review checklist](#review-checklist)

## Mirror Layout

Within each client app/package, keep every test under its `src/__tests__/` and mirror the source path exactly. The example below is the single-project mapping:

```text
src/
  features/profile/api.ts
  features/profile/hooks.ts
  common/logging/adapters/debug.ts
  lib/modules/profile/shared/contracts/update.contract.ts
  __tests__/
    features/profile/api.test.ts
    features/profile/hooks.test.ts
    common/logging/adapters/debug.test.ts
    lib/modules/profile/shared/contracts/update.contract.test.ts
```

Never colocate `*.test.*` beside source files.

## Behavioral Style

Use Arrange, Act, Assert with one observable behavior per test. Name tests as subject, condition, and outcome. Prefer vertical red-green-refactor cycles rather than writing all tests and then all implementation.

Test public interfaces and returned behavior. Do not target private methods or assert internal call order unless ordering is itself the behavior.

Use doubles consistently:

- Fake: working in-memory interface implementation; preferred for feature boundaries.
- Stub: fixed success/failure response.
- Spy: records calls when arguments/count are the behavior.
- Mock: strict expectations only when sequence is meaningful.

Never mock pure domain/helpers, Zod schemas, or standard-library behavior.

## Test by Boundary

- Shared contract: representative valid/invalid wire payloads, serialized safety, UUID/date/enum/nullability edges. Test the schema matrix once.
- `domain.ts` and `helpers.ts`: pure table-driven cases without mocks or framework runtime.
- `api.ts`: construct through `create<Feature>Api`, stub injected `IClientApi`, inject `toAppError` and logger spy/no-op, assert representative response parsing/mapping and normalized failure.
- `hooks.ts`: fake `I<Feature>Api`, use a fresh QueryClient, assert keys, invalidation, status, optimistic rollback, and success analytics when owned.
- business component: mock feature hooks, not transport.
- presentation component: render with props/form fixtures only.
- realtime adapter: fake provider channel/client and test validation, status mapping, and idempotent teardown.
- realtime hook: fake `I<Feature>RealtimeApi`, verify subscription lifecycle and cache reconciliation.

Do not repeat a shared contract's full validation matrix in API or transport tests; only verify the boundary invokes it and maps failure correctly.

## Factories and Telemetry

Call production factories with test adapters:

```ts
const logger = createAppLogger({ sinks: [logSinkSpy], context: fixedContext });
const analytics = createProductAnalytics({
  adapters: [analyticsSpy],
  consent: allowAllConsent,
  logger,
});
const clientApi = createClientApi({ transport: fakeTransport, logger });
const profileApi = createProfileApi({ clientApi, toAppError, logger });
```

Verify stable browser instances, isolated request-scoped context, provider construction behind factories, and consumers receiving specific ports. Ensure telemetry adapters cannot reject or change the business result.

## Vitest Baseline

Require scripts:

```json
{
  "scripts": {
    "test:unit": "vitest run",
    "test:unit:watch": "vitest"
  }
}
```

Use `vitest.config.mts`, `vite-tsconfig-paths`, globals, a shared `src/test/vitest.setup.ts`, `restoreMocks`, `clearMocks`, and includes restricted to `src/__tests__/**/*.test.ts(x)`.

For Next.js/React, add the React plugin, Testing Library, and jsdom. Keep Node as the safe default and opt client component/hook tests into jsdom or use separate projects. Alias `server-only` to an empty test shim, but retain an independent build/import-boundary check so the shim cannot conceal a leaked server import.

Provide harmless fake env values only to tests whose import graph validates them. Never load production secrets or real infrastructure.

## Review Checklist

- Test path mirrors source path mechanically.
- Each test has one behavior and one act.
- API tests mock injected dependencies, not internals.
- Hook tests fake feature APIs rather than fetch/tRPC internals.
- Pure functions and shared contracts are not mocked.
- No unit test calls live network, database, Sentry, debug, or analytics vendors.
- Cache, analytics, error, and lifecycle assertions remain at their owning boundary.
- One smoke test proves config, aliases, setup, and discovery before expanding a suite.

## Derivation Sources

Derived from the source repository's client testing, Vitest, folder-structure, composition-root, React conventions/composition/server-state/realtime, and Next.js Vitest/realtime documents. These paths are provenance only in an installed skill.
