# Client Core Onboarding (Agnostic)

Use this as the default startup path for new projects and new contributors.

## Read Order

1. `client/core/overview.md`
2. `client/core/architecture.md`
3. `client/core/conventions.md`
4. `client/core/folder-structure.md`
5. `client/core/client-api-architecture.md`
6. `client/core/server-state-tanstack-query.md`
7. `client/core/error-handling.md`
8. `client/core/logging.md`

Then move to framework/metaframework docs.

## New Project Bootstrap Checklist

- [ ] Decide route/metaframework folder (`<routes>/`).
- [ ] Set `src/features/*` as primary unit of organization.
- [ ] Define `src/common/query-keys/*` for non-tRPC adapters.
- [ ] Define `src/common/errors/*` for `AppError` normalization.
- [ ] Define `src/common/toast/*` facade so features do not couple to provider APIs.
- [ ] Define `src/common/logging/*` facade/adapters (`debug` default).
- [ ] Adopt client API chain: `clientApi -> featureApi -> query adapter -> components`.
- [ ] Enforce feature API contract: `I<Feature>Api` + `class <Feature>Api` + `create<Feature>Api`.
- [ ] Keep domain transform precedence: `src/lib/modules/<module>/shared/*` first, then feature-local.

## First Feature Definition of Done

- [ ] Feature has required starter files (`api.ts`, `hooks.ts`, `schemas.ts`, components).
- [ ] Query/mutation units are single-responsibility.
- [ ] Hook naming uses `useQuery*` / `useMut*` / `useMod*`.
- [ ] Presentation components have no direct transport or cache manipulation.
- [ ] Errors are normalized to `AppError` before UI branching.
- [ ] Invalidation is centralized and deterministic.
- [ ] Logging uses `src/common/logging/*`, not ad-hoc `console.log`.
- [ ] `api.ts` is unit-tested with mocked injected deps (`clientApi`, `toAppError`).
- [ ] `domain.ts` / `helpers.ts` are unit-tested as pure functions (no mocks).

## Contributor PR Checklist (Client Core Contracts)

- [ ] Core docs remain framework-agnostic.
- [ ] Framework-specific implementation details stay in `client/frameworks/*`.
- [ ] New rule placement follows contract ownership (core vs framework).
- [ ] No contradictory guidance introduced across `client/core/*`.
- [ ] Non-trivial doc changes include a `change-logs/*` entry.

## Canonical vs Drafts

- `client/core/*` and `client/frameworks/*` are canonical.
- `client/drafts/*` is reference-only and may be outdated.
- Never copy draft patterns into canonical docs without re-validating ownership/boundaries.
