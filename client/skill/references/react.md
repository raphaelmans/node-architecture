# React Slice

Use this slice for React component boundaries, composition, browser configuration, server-state hooks, forms, error/toast facades, Zustand integration, realtime lifecycle, and shadcn/Radix UI structure.

## Contents

- [Scaffolding](#scaffolding)
- [Component layers](#component-layers)
- [Hooks and composition](#hooks-and-composition)
- [Configuration](#configuration)
- [Forms](#forms)
- [Error and toast handling](#error-and-toast-handling)
- [UI and state](#ui-and-state)
- [Review checklist](#review-checklist)

## Scaffolding

Load the generic scaffolding contract first. Detect the installed React version, renderer, build tool/metaframework, language and module mode, source layout, JSX transform, providers, state/query layer, and test environment. Retrieve current official documentation for version-sensitive lifecycle, peer, configuration, and build decisions. React and Next.js are documented specializations, not requirements for other client frameworks.

Adaptive placement preserves compatible repository conventions. React canonical mode maps the generic contract to `common`, `features`, shared contracts, a composition root, and mirrored tests. Resolve concrete packages only after capability activation, installed-graph inspection, exact-version selection, and approval.

## Component Layers

Apply: coordinate high, fetch low, render dumb.

- Providers coordinate the server-state cache client, theme, toast, and specific infrastructure ports. They do not fetch bootstrap server data, construct vendors, or expose a runtime service locator.
- Business components call feature hooks, own forms, compose loading/error states, and coordinate route-local UX.
- Presentation components render from props or form context and do not fetch, mutate, navigate, or import telemetry vendors.

"Fetch low" means close to the consuming feature section through `features/<feature>/hooks.ts`; it does not mean inline transport/query calls in TSX.

Split a screen into a coordinator and cohesive leaf business sections rather than one god component. Use explicit slots/children to keep presentation flexible without boolean-prop explosions.

## Hooks and Composition

Server-state hook naming:

- query: `useQuery<Feature><Noun><Qualifier?>`;
- mutation: `useMut<Feature><Verb><Object?>`;
- multi-unit composition or cache sync: `useMod<Descriptive>`.

Each `useQuery*` owns one key/fetcher; each `useMut*` owns one mutation. Compose independent units with `useMod*` rather than expanding one hook across domains.

Prefer hook-owned invalidation for reusable behavior. For route-specific `submit -> sync -> navigate`, let the business component call a named `useMod*Sync` operation while query keys and direct cache-client operations remain in `hooks.ts` or `sync.ts`.

Do not add a workflow hook merely to emit telemetry. Introduce it when the UX has meaningful coordinated steps.

## Configuration

React consumes configuration but does not define how environment values are loaded. Detect the installed build tool/metaframework and retrieve its current primary documentation.

Use an app-owned executable schema for public `BrowserBuildConfig`, map external names into normalized values at composition, and provide focused ports/options rather than a generic configuration context. Activate `BrowserRuntimeConfig` only when public values must be delivered independently of the build. Load and validate it when its dependent shell or capability begins; failure remains scoped to that work.

The schema is authoritative. `.env.example` is a checked projection of build-environment fields, while browser runtime resources use their own schema/example. Unknown host variables are permitted and excluded from normalized configuration.

## Forms

Use Zod, react-hook-form, its Zod resolver, and shared StandardForm primitives when present.

- Define form schemas in `features/<feature>/schemas.ts` by composing the shared input contract.
- Map form values through the shared input schema before calling the mutation.
- Keep UI-only fields out of business payloads.
- Subscribe to every form state needed by rendering during render, using the installed form library's supported mechanism.
- Await mutation completion in submit handlers through the installed query/mutation integration.
- Disable submit during submission; gate clean forms only where avoiding a no-op edit is intentional.
- Never reset on failure. Reset after success only when the workflow requires it.
- When external query data supplies defaults, isolate query-result-to-form-reset synchronization in a focused hook.
- Map `AppError.kind === "validation"` to fields/root; show other safe messages through the toast/error facade.
- Never cast a caught `unknown` value to `AppError`. Normalize it through the error facade/adapter (which returns an existing `AppError` unchanged) or use a helper that returns a typed result.

Presentation field components use form context; the business form owns form construction, submit orchestration, mutation, and navigation.

## Error and Toast Handling

React consumes normalized `AppError` through an error facade. Provider-specific checks remain in adapters. Direct-provider compatibility hooks must project an app-facing result instead of spreading a raw query/mutation object whose `error` leaks the provider type.

Keep toast vendors behind a small `ToastFacade`. Helpers such as `useCatchErrorToast` may wrap an async operation and return a typed `{ ok, data | error }` result, but success notification occurs only after the entire callback resolves.

The framework error boundary owns unhandled render/runtime exceptions. Do not blanket-report handled server-state cache errors already owned by client or feature API boundaries.

## UI and State

Use this hierarchy when present:

```text
components/ui/          shadcn/Radix primitives
components/form/        reusable form abstractions
components/custom-ui/   application-wide composed UI
features/<feature>/components/  feature business and presentation UI
```

Keep primitives generic and business-free. Use semantic design tokens, `cn` for class composition, CVA for meaningful variants, mobile-first styles, and `gap` for sibling spacing.

Use Zustand only for client coordination state. Keep stores feature-local, select narrow values, persist an explicit allowlist, and account for SSR hydration. Use refs for subscription bookkeeping that does not affect rendering.

For realtime, subscribe in an effect, return teardown, use a stable feature realtime API, keep reducers pure, and reconcile cache state after safe patches.

## Review Checklist

- Routes/pages compose feature components; feature components do not parse route shape.
- Providers coordinate infrastructure but do not fetch server entities.
- Query and mutation definitions stay in feature hooks.
- Business components own workflow; presentation components render only.
- Forms compose shared contracts and send mapped inputs.
- Cache keys and direct cache-client calls stay outside TSX.
- Raw provider errors, SDKs, and runtime containers do not enter components.
- React providers expose focused configured ports; they do not expose complete environment/configuration surfaces.
- State uses TanStack Query, URL, form, store, machine, or local state according to ownership.
- Tests mock hooks for business components and use fixtures for presentation components.

## Official Implementation References

- [React documentation](https://react.dev/)
- [T3 Env Core](https://env.t3.gg/docs/core)
- [React Hook Form documentation](https://react-hook-form.com/docs)
- [Zod documentation](https://zod.dev/)
- [TanStack Query React documentation](https://tanstack.com/query/latest/docs/framework/react/overview)
- [shadcn/ui documentation](https://ui.shadcn.com/docs)
- [Radix Primitives documentation](https://www.radix-ui.com/primitives/docs/overview/introduction)
- [Class Variance Authority documentation](https://cva.style/docs)

React Hook Form is the documented form-state specialization, Zod owns executable validation, and TanStack Query owns asynchronous server state. shadcn/ui, Radix Primitives, and Class Variance Authority are reference specializations for accessible primitives, composition, and variant styling. Preserve those responsibilities when another compatible library is selected; resolve exact components, hooks, state properties, and mutation methods from installed-version documentation.

## Derivation Sources

Derived from all source repository documents under the React framework directory: scaffolding, overview, conventions, composition, environment configuration, error handling, forms, server-state patterns, Zustand, UI patterns, and realtime lifecycle. These paths are provenance only in an installed skill.
