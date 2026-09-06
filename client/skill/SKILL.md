---
name: client
description: Apply this repository's client architecture when designing, explaining, reviewing, scaffolding, testing, implementing, or refactoring frontend features. Use for any client framework when work involves repository bootstrapping, feature scaffolds, feature boundaries, shared contracts, client APIs, state synchronization, telemetry, composition roots, dependency injection, errors, forms, shadcn components, themes, variants, or tests. Known React and Next.js slices are specializations, not an allowlist. Route each request through the smallest relevant architecture slices and do not use for backend-only work.
---

# Client Architecture

For Next.js local startup, Portless setup, or worktree origins, select `nextjs` and coordinate with installed `$development` when available.

Route client work through modular architecture slices. Load only the references required by the task, compose multiple slices when concerns cross boundaries, and preserve the user's requested operation: explanation, diagnosis, review, planning, or implementation.

## Start

1. Inspect the target repository, requested files, and applicable stack before proposing changes.
2. Determine whether the user asked to explain, diagnose, review, plan, implement, or refactor. Do not turn a read-only request into a mutation.
3. Select the smallest relevant slice set from the routing table.
4. Read every selected reference completely before acting.
5. Inspect existing project conventions and dependencies. Apply framework or vendor guidance only when that technology is present or explicitly requested.
6. For version-sensitive framework, dependency, configuration, lifecycle, module-format, build, or deployment decisions, retrieve current version-applicable primary documentation before acting. Retain named libraries and official links when they clarify a supported specialization, its role, rationale, or selection criteria. Treat vendor API symbols, framework-owned filenames, configuration keys, flags, version thresholds, deprecations, and migration recipes as version-sensitive even when repository examples or training data state them confidently; detect the installed version and derive the exact implementation at execution time.
7. If the detected stack has no named slice, apply core guidance and derive the integration from repository evidence and official stack resources; do not reject it merely because it is unlisted.
8. For implementation, verify the result at the narrowest meaningful boundary and report unrelated drift without changing it.

## Route Slices

| Slice | Load when the task involves | Reference |
| --- | --- | --- |
| `scaffolding` | `$client scaffold`, repository preflight, missing infrastructure, dependency approval, vertical feature generation | [references/scaffolding.md](references/scaffolding.md) |
| `foundations` | boundaries, folders, composition roots, configuration surfaces, factories, feature structure, domain placement | [references/foundations.md](references/foundations.md) |
| `workspace` | single-project/monorepo topology, client app ownership, shared packages, or cross-package coordination | [references/workspace.md](references/workspace.md) |
| `contracts` | Zod wire contracts, validation, DTO mapping, `AppError`, safe error UX | [references/contracts.md](references/contracts.md) |
| `data-flow` | `clientApi`, `featureApi`, query adapters, TanStack Query, query keys, HTTP, tRPC | [references/data-flow.md](references/data-flow.md) |
| `state-realtime` | state ownership, Zustand, URL state, cache patches, subscriptions, reconnection | [references/state-realtime.md](references/state-realtime.md) |
| `telemetry` | `AppLogger`, `debug`, Sentry, product analytics, consent, correlation | [references/telemetry.md](references/telemetry.md) |
| `testing` | test placement, doubles, Vitest, hook/API/factory/telemetry tests | [references/testing.md](references/testing.md) |
| `react` | React composition, hooks, forms, presentation boundaries, UI and toast facades | [references/react.md](references/react.md) |
| `nextjs` | App Router, SSR/RSC, params, environment, tRPC/Ky adapters, Next.js tests | [references/nextjs.md](references/nextjs.md) |

## Convention Leaves

Slices may route to a convention leaf for a narrower, opinionated concern. Load a leaf only when its trigger matches; do not load every child reference whenever its parent slice is selected.

| Parent slice | Convention leaf | Load when the task involves | Reference |
| --- | --- | --- | --- |
| `react` | `react/shadcn` | creating/updating UI components, shared compositions, themes, variants, or reviewing feature styling | [references/react/shadcn.md](references/react/shadcn.md) |
| `react`; add `data-flow` for access queries/mutations | `react/access-control` | permission gates, role-sensitive UX, membership management, organization/branch switching | [references/react/access-control.md](references/react/access-control.md) |
| `nextjs` + `react` | `nextjs/access-control` | protected SSR/RSC, access hydration, Next.js workspace navigation, client/server access composition | [references/nextjs/access-control.md](references/nextjs/access-control.md) |
| `nextjs`; add `state-realtime` while state ownership is undecided | `nextjs/routing` | `appRoutes`, route policies, links/redirects, dynamic path builders, params/search params, nuqs, or URL-backed interaction state | [references/nextjs/routing.md](references/nextjs/routing.md) |

A convention leaf refines its parent slices; it does not become a top-level routing alias or override their invariants.

For Next.js access-control work, compose the React and Next.js access-control leaves; standalone React needs only its own mapping. Product workspaces are organization/access state, not the monorepo `workspace` slice unless package topology is involved. Client controls are UX only; coordinate authoritative capability changes with installed `$server` when available.

Treat `bootstrap`, `initialize`, and `generate structure` as aliases for `scaffolding`; `core`, `architecture`, `config`, and `environment` as aliases for `foundations`; `workspace`, `package`, and `monorepo` as aliases for `workspace`; `api`, `query`, and `transport` as aliases for `data-flow`; `logging`, `analytics`, and `observability` as aliases for `telemetry`; and `next` as an alias for `nextjs`.

When the user names multiple concerns, load all matching references. Examples:

- `$client scaffold foundation`: `scaffolding` + `foundations` + capability slices discovered during preflight
- `$client scaffold foundation` in a workspace: add `workspace`; remain inside resolved packages unless cross-package coordination is activated
- `$client scaffold users/create`: `scaffolding` + `foundations` + `contracts` + `data-flow` + `react` + `testing`; add `nextjs`, `telemetry`, or state slices only when detected/requested capabilities require them
- `$client scaffold users/create` in Vue or Svelte: `scaffolding` + capability slices; derive framework integration from repository evidence and current official docs
- Next.js logging or Sentry: `telemetry` + `nextjs`
- Next.js route registry or nuqs implementation: `nextjs` + `nextjs/routing`; add `state-realtime` if deciding whether the state belongs in the URL
- Standalone React configuration: `foundations` + `react`; add `workspace` or `nextjs` only when those boundaries exist
- Create a React feature: `foundations` + `contracts` + `data-flow` + `react` + `testing`; add `telemetry` when the implementation emits operational records or product events
- Realtime React cache synchronization: `state-realtime` + `data-flow` + `react` + `testing`
- Create/update a shadcn component or theme: `react` + `react/shadcn`; add `workspace` when package ownership is involved
- Form validation and error UX: `contracts` + `react` + `testing`

When invoked without a task, show the slice menu with two or three context-aware examples. Do not start an audit or implementation automatically.

When invoked as `$client scaffold`, read `scaffolding` first, then every capability slice selected by preflight. Load `workspace` when a package/workspace boundary exists and load `react` or `nextjs` only when detected or requested. For an unlisted framework, retain the generic slice and retrieve the official resources needed to derive its specialization. Complete evidence, atomicity, and dependency approval before writing. If required changes cross packages, stop before partial writes and apply the `$monorepo` coordination contract; otherwise remain within `$client`.

## Preserve These Invariants

- Use the call chain `components -> query adapter -> featureApi -> clientApi -> network`; typed results return in reverse.
- Keep presentation components render-only. Business components coordinate UI flows but do not own transport or concrete cache mechanics.
- Define one shared Zod request/response contract under the topology's resolved isomorphic contract boundary. Do not duplicate wire DTOs or import it from a server application package.
- Normalize provider errors once to `AppError`. Preserve only user-safe messages and assign one operational reporting owner per failure.
- Keep server state in TanStack Query, client coordination state in an appropriate store, shareable state in the URL, and local ephemeral state in the component.
- Use factories for dependency-heavy infrastructure and assemble it in one composition root. Inject specific ports, never the complete runtime container.
- Keep `BrowserBuildConfig` limited to public build values and separate from live runtime dependencies and opt-in `BrowserRuntimeConfig`; executable schemas are deployable-owned and external names stop at composition.
- Keep `AppLogger` operational diagnostics separate from typed `ProductAnalytics` behavioral events. Never thread telemetry metadata through business DTOs.
- Keep tests under a mirrored `src/__tests__/` tree and test each layer through its public boundary.
- Apply core rules before React or Next.js additions. Framework guidance extends core; it does not override it.
- Persist durable concepts, rationale, selection criteria, ownership, safety, and verification outcomes in this skill. Named libraries may remain as linked reference implementations; their currently correct syntax does not become a permanent skill rule.
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
