# Client Core Onboarding (Agnostic)

Use this as the default startup path for new projects and new contributors.

## Read Order

1. `client/core/README.md`
2. `client/core/architecture.md`
3. `client/core/conventions.md`
4. `client/core/folder-structure.md`
5. `client/core/composition-root.md`
6. `client/core/client-api-architecture.md`
7. `client/core/validation-zod.md`
8. `client/core/domain-logic.md`
9. `client/core/query-keys.md`
10. `client/core/server-state-tanstack-query.md`
11. `client/core/state-management.md`
12. `client/core/error-handling.md`
13. `client/core/logging.md`
14. `client/core/product-analytics.md`
15. `client/core/realtime.md`
16. `client/core/testing.md`
17. `client/core/testing-vitest.md`

Then move to framework/metaframework docs.

## New Project Bootstrap Checklist

- [ ] Decide route/metaframework folder (`<routes>/`).
- [ ] Set `src/features/*` as primary unit of organization.
- [ ] Define `src/common/query-keys/*` for non-tRPC adapters.
- [ ] Define `src/common/errors/*` for `AppError` normalization.
- [ ] Define `src/common/toast/*` facade so features do not couple to provider APIs.
- [ ] Define the OpenTelemetry-shaped `src/common/logging/*` port, enrichment/redaction wrappers, and `debug` adapter.
- [ ] Define a separate typed `src/common/analytics/*` port with consent-aware adapters.
- [ ] Keep optional Sentry integration behind the logger/error-reporting adapter.
- [ ] Add one client composition root for logger, analytics, transport, and feature API factories.
- [ ] Keep browser instances application-scoped and request-contextual SSR dependencies request-scoped.
- [ ] Inject specific ports; never inject the complete runtime container.
- [ ] Adopt client call chain: `components -> query adapter -> featureApi -> clientApi` (typed results return in the opposite direction).
- [ ] Enforce feature API contract: `I<Feature>Api` + `class <Feature>Api` + `create<Feature>Api`.
- [ ] Put public Zod input/response contracts in `src/lib/modules/<module>/shared/contracts/`.
- [ ] Import the same contracts from client `featureApi` and server transport adapters.
- [ ] Keep domain transform precedence: `src/lib/modules/<module>/shared/*` first, then feature-local.
- [ ] Set up Vitest as the unit test runner per `client/core/testing-vitest.md`.
- [ ] Add `test:unit` and `test:unit:watch` scripts to `package.json`.
- [ ] Create `src/test/vitest.setup.ts` with framework-specific cleanup.
- [ ] Verify runner with a smoke test before adding feature tests.

## First Feature Definition of Done

- [ ] Feature has required starter files (`api.ts`, `hooks.ts`, `schemas.ts`, components).
- [ ] Public wire contracts are shared imports, not client copies or ORM/server types.
- [ ] `schemas.ts` contains only client form/UI composition.
- [ ] Query/mutation units are single-responsibility.
- [ ] Hook naming uses `useQuery*` / `useMut*` / `useMod*`.
- [ ] Presentation components have no direct transport or cache manipulation.
- [ ] Errors are normalized to `AppError` before UI branching.
- [ ] Invalidation is centralized and deterministic.
- [ ] Operational logging uses `src/common/logging/*`, not `console`, `debug`, or Sentry imports in features.
- [ ] Product events use typed `ProductAnalytics`, not operational logs or vendor imports.
- [ ] Transport errors have one logging owner and preserve `requestId` when available.
- [ ] `api.ts` is unit-tested with mocked injected deps (`clientApi`, `toAppError`, and logger when used).
- [ ] Mutation/workflow analytics are tested with a spy/fake and emit only after success.
- [ ] Feature runtime modules reference composition-root-owned instances instead of constructing hidden singletons.
- [ ] `domain.ts` / `helpers.ts` are unit-tested as pure functions (no mocks).

## Contributor PR Checklist (Client Core Contracts)

- [ ] Core docs remain framework-agnostic.
- [ ] Framework-specific implementation details stay in `client/frameworks/*`.
- [ ] New rule placement follows contract ownership (core vs framework).
- [ ] No contradictory guidance introduced across `client/core/*`.
- [ ] Non-trivial doc changes include a `change-logs/*` entry.

## Canonical vs Drafts

- `client/core/*` and `client/frameworks/*` are canonical.
- `legacy/client/*` is reference-only and may be outdated.
- Never copy legacy patterns into canonical docs without re-validating ownership/boundaries.
