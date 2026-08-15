---
name: client
description: Apply this repository's client architecture when designing, explaining, reviewing, testing, implementing, or refactoring frontend features. Use for React or Next.js client work involving feature boundaries, shared contracts, client APIs, TanStack Query, state, realtime, operational logging, product analytics, composition roots, dependency injection, error handling, forms, or Vitest. Route each request through the smallest relevant architecture slices and do not use for backend-only work.
---

# Client Architecture

Route client work through modular architecture slices. Load only the references required by the task, compose multiple slices when concerns cross boundaries, and preserve the user's requested operation: explanation, diagnosis, review, planning, or implementation.

## Start

1. Inspect the target repository, requested files, and applicable stack before proposing changes.
2. Determine whether the user asked to explain, diagnose, review, plan, implement, or refactor. Do not turn a read-only request into a mutation.
3. Select the smallest relevant slice set from the routing table.
4. Read every selected reference completely before acting.
5. Inspect existing project conventions and dependencies. Apply framework or vendor guidance only when that technology is present or explicitly requested.
6. For implementation, verify the result at the narrowest meaningful boundary and report unrelated drift without changing it.

## Route Slices

| Slice | Load when the task involves | Reference |
| --- | --- | --- |
| `foundations` | boundaries, folders, composition roots, factories, feature structure, domain placement | [references/foundations.md](references/foundations.md) |
| `contracts` | Zod wire contracts, validation, DTO mapping, `AppError`, safe error UX | [references/contracts.md](references/contracts.md) |
| `data-flow` | `clientApi`, `featureApi`, query adapters, TanStack Query, query keys, HTTP, tRPC | [references/data-flow.md](references/data-flow.md) |
| `state-realtime` | state ownership, Zustand, URL state, cache patches, subscriptions, reconnection | [references/state-realtime.md](references/state-realtime.md) |
| `telemetry` | `AppLogger`, `debug`, Sentry, product analytics, consent, correlation | [references/telemetry.md](references/telemetry.md) |
| `testing` | test placement, doubles, Vitest, hook/API/factory/telemetry tests | [references/testing.md](references/testing.md) |
| `react` | React composition, hooks, forms, presentation boundaries, UI and toast facades | [references/react.md](references/react.md) |
| `nextjs` | App Router, SSR/RSC, params, environment, tRPC/Ky adapters, Next.js tests | [references/nextjs.md](references/nextjs.md) |

Treat `core` and `architecture` as aliases for `foundations`; `api`, `query`, and `transport` as aliases for `data-flow`; `logging`, `analytics`, and `observability` as aliases for `telemetry`; and `next` as an alias for `nextjs`.

When the user names multiple concerns, load all matching references. Examples:

- Next.js logging or Sentry: `telemetry` + `nextjs`
- Create a React feature: `foundations` + `contracts` + `data-flow` + `react` + `testing`; add `telemetry` when the implementation emits operational records or product events
- Realtime React cache synchronization: `state-realtime` + `data-flow` + `react` + `testing`
- Form validation and error UX: `contracts` + `react` + `testing`

When invoked without a task, show the slice menu with two or three context-aware examples. Do not start an audit or implementation automatically.

## Preserve These Invariants

- Use the call chain `components -> query adapter -> featureApi -> clientApi -> network`; typed results return in reverse.
- Keep presentation components render-only. Business components coordinate UI flows but do not own transport or concrete cache mechanics.
- Define one shared Zod request/response contract under the owning module's isomorphic `shared/contracts` boundary. Do not duplicate wire DTOs.
- Normalize provider errors once to `AppError`. Preserve only user-safe messages and assign one operational reporting owner per failure.
- Keep server state in TanStack Query, client coordination state in an appropriate store, shareable state in the URL, and local ephemeral state in the component.
- Use factories for dependency-heavy infrastructure and assemble it in one composition root. Inject specific ports, never the complete runtime container.
- Keep `AppLogger` operational diagnostics separate from typed `ProductAnalytics` behavioral events. Never thread telemetry metadata through business DTOs.
- Keep tests under a mirrored `src/__tests__/` tree and test each layer through its public boundary.
- Apply core rules before React or Next.js additions. Framework guidance extends core; it does not override it.
- Do not introduce libraries, adapters, controllers, stores, or factories merely because a reference mentions them. The target stack and actual complexity must justify them.

## Review and Change Discipline

For reviews and audits:

1. Report evidence with file and line references.
2. Separate contract violations from optional improvements.
3. Explain impact and the owning layer.
4. Do not fix findings unless the user asks for changes.

For implementation and refactoring:

1. Preserve unrelated user changes.
2. Make new or modified files comply with the selected slices.
3. Keep migrations incremental when legacy code uses compatibility patterns.
4. Add or update tests at the same boundary as the behavior.
5. Run targeted validation first, then broader checks when justified.
