# Client Architecture Consistency Sweep

Date: 2026-08-15

## Summary

Applied a full consistency and correctness pass across the canonical client documentation and interactive client architecture guide.

## Locked Architecture

- Retained the call flow `components -> query adapter -> featureApi -> clientApi -> network`.
- Kept reusable cache behavior in query hooks or feature `sync.ts`; screen/business components may sequence named operations but do not inline query keys or query-client mechanics.
- Retained composition-root-owned factories and browser/request lifetime rules.
- Retained separate `AppLogger` and `ProductAnalytics` ports without adding telemetry fields to business DTOs.
- Confirmed that no generic client controller layer is required; `useMod*` workflows cover justified UI orchestration.

## Corrections

- Split query-key strategies by adapter: generated tRPC utilities, optional tRPC-interoperability keys, and plain key factories for Ky/fetch/realtime.
- Removed undocumented `._def` usage, redundant stable-object serialization, and mandatory invalidate-plus-refetch flows.
- Corrected `AppError` examples and added a distinct `contract` error kind for invalid API responses.
- Updated feature API tests to assert thrown discriminated-union errors through injected boundaries.
- Added explicit form-to-wire mapping so UI-only fields do not enter feature API inputs.
- Replaced deprecated Zod schema merging with Zod 4 `safeExtend` and fixed environment boolean parsing with `stringbool`.
- Updated Ky examples to the Ky 2 `baseUrl` API and clarified same-origin versus SSR URL behavior.
- Corrected React Hook Form subscription guidance and async-default hydration examples.
- Moved concrete cache mechanics out of TSX coordinators into named `useMod*Sync` operations.
- Split realtime guidance into provider-neutral core, React lifecycle, and Supabase-specific adapter/server-setup documents.
- Updated Zustand context stores to use a vanilla `createStore` owned by a provider instance.
- Added Next.js 16 asynchronous params/searchParams guidance and completed nuqs filter pagination reset behavior.
- Made Vitest's default environment Node-based with explicit jsdom opt-in and isolated server env setup.
- Refreshed read orders, diagrams, folder structures, terminology, and the interactive HTML guide.

## Validation

- All local Markdown links and anchors resolve.
- All Markdown code fences are balanced.
- `git diff --check` passes for the client documentation changes.
- A targeted stale-pattern scan reports no active examples using `._def`, Ky `prefixUrl:`, `z.coerce.boolean(...)`, deprecated `.merge()`, stale `callTrpc*` test guidance, or mandatory `onSubmitRefetch` flows.
