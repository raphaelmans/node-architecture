# React Slice

Use this slice for React component boundaries, composition, server-state hooks, forms, error/toast facades, Zustand integration, realtime lifecycle, and shadcn/Radix UI structure.

## Contents

- [Component layers](#component-layers)
- [Hooks and composition](#hooks-and-composition)
- [Forms](#forms)
- [Error and toast handling](#error-and-toast-handling)
- [UI and state](#ui-and-state)
- [Review checklist](#review-checklist)

## Component Layers

Apply: coordinate high, fetch low, render dumb.

- Providers coordinate QueryClient, theme, toast, and specific infrastructure ports. They do not fetch bootstrap server data, construct vendors, or expose a runtime service locator.
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

Prefer hook-owned invalidation for reusable behavior. For route-specific `submit -> sync -> navigate`, let the business component call a named `useMod*Sync` operation while query keys and QueryClient remain in `hooks.ts` or `sync.ts`.

Do not add a workflow hook merely to emit telemetry. Introduce it when the UX has meaningful coordinated steps.

## Forms

Use Zod, react-hook-form, its Zod resolver, and shared StandardForm primitives when present.

- Define form schemas in `features/<feature>/schemas.ts` by composing the shared input contract.
- Map form values through the shared input schema before calling the mutation.
- Keep UI-only fields out of business payloads.
- Read required `formState` values unconditionally during render so subscriptions are established.
- Use `mutateAsync` in submit handlers.
- Disable submit during submission; use `!isDirty` only where avoiding a no-op edit is intentional.
- Never reset on failure. Reset after success only when the workflow requires it.
- When external query data supplies defaults, isolate `query.data -> reset(...)` synchronization in a focused hook.
- Map `AppError.kind === "validation"` to fields/root; show other safe messages through the toast/error facade.
- Never cast a caught `unknown` value to `AppError`. Normalize it through the error facade/adapter (which returns an existing `AppError` unchanged) or use a helper that returns a typed result.

Presentation field components use form context; the business form owns `useForm`, submit orchestration, mutation, and navigation.

## Error and Toast Handling

React consumes normalized `AppError` through an error facade. Provider-specific checks remain in adapters. Direct-provider compatibility hooks must project an app-facing result instead of spreading a raw query/mutation object whose `error` leaks the provider type.

Keep toast vendors behind a small `ToastFacade`. Helpers such as `useCatchErrorToast` may wrap an async operation and return a typed `{ ok, data | error }` result, but success notification occurs only after the entire callback resolves.

The framework error boundary owns unhandled render/runtime exceptions. Do not blanket-report handled QueryClient errors already owned by client or feature API boundaries.

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
- Cache keys and QueryClient calls stay outside TSX.
- Raw provider errors, SDKs, and runtime containers do not enter components.
- State uses TanStack Query, URL, form, store, machine, or local state according to ownership.
- Tests mock hooks for business components and use fixtures for presentation components.

## Derivation Sources

Derived from all source repository documents under the React framework directory: overview, conventions, composition, error handling, forms, server-state patterns, Zustand, UI patterns, and realtime lifecycle. These paths are provenance only in an installed skill.
