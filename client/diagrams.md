# Client Architecture Diagrams (ASCII)

This file is a visual companion to the written docs in `client/core/` and `client/frameworks/`.

Path labels use the single-project topology. In a monorepo, substitute activated contract/domain/UI packages and keep client features plus composition in the deployable client app; the arrows and ownership do not change.

---

## 1) Documentation Structure (This Repo)

```
client/
  README.md
  diagrams.md

  core/                           # framework-agnostic
    README.md
    architecture.md
    conventions.md
    composition-root.md
    client-api-architecture.md
    validation-zod.md
    domain-logic.md
    server-state-tanstack-query.md
    query-keys.md
    state-management.md
    error-handling.md
    logging.md
    product-analytics.md
    testing.md
    testing-vitest.md
    realtime.md
    folder-structure.md

  frameworks/                      # framework-specific
    README.md
    reactjs/
      README.md
      overview.md
      conventions.md
      composition-react.md
      error-handling.md
      forms-react-hook-form.md
      realtime-react.md
      ui-shadcn-radix.md
      state-zustand.md
      metaframeworks/
        nextjs/
          README.md
          overview.md
          routing-ssr-params.md
          environment.md
          folder-structure.md
          url-state-nuqs.md
          trpc.md
          ky-fetch.md
          realtime-supabase.md
          query-keys.md            # moved to client/core/query-keys.md (keep as redirect)
          testing-vitest.md

legacy/
  client/                         # detailed historical references (non-canonical)
    01-zod-schema-architecture.md
    ...
```

---

## 2) Runtime Structure (Layers + Data Flow)

Key rule:

- Components never call transport (HTTP) directly.

Preferred call chain:

```
UI interaction
  |
  v
[Route layer (metaframework)]
  - SSR/RSC, params/searchParams parsing
  - composes feature business components
  |
  v
[Feature business component]
  - orchestrates sections, form wiring, loading/error UI
  - calls query adapter (does NOT call transport)
  |
  v
[Query adapter (server/IO state)]
  - defines queryKey + useQuery/useMutation
  - owns invalidation / optimistic updates
  - emits typed success analytics when it owns the action
  - depends on I<Feature>Api contract
  |
  v
[featureApi boundary]
  - one per feature domain: I<Feature>Api + class <Feature>Api + create<Feature>Api(...)
  - owns endpoint paths + contract parsing/mapping
  - imports schemas from the resolved isomorphic contract boundary
  - parses network responses at the boundary (Zod)
  - maps DTO -> feature model
  - normalizes unknown -> AppError via toAppError
  - logs contract/mapping failures it owns
  - depends on clientApi (interface)
  |
  v
[clientApi (transport + cross-cutting)]
  - base URL, headers/auth attachment
  - response envelope decoding
  - typed, inspectable errors
  - retry/timeouts (if global)
  - owns transport logs + response requestId correlation
  |
  v
Network
```

Where the hard rules live:

```
Zod parsing boundary:      featureApi
Cache + invalidation:      query adapter
Transport details:         clientApi (implementation varies)
Route parsing + SSR:       metaframework docs (Next.js)
Wire contract source:      resolved module-local or contract-package boundary
Operational logging:       AppLogger -> debug/Sentry adapters
Product analytics:         ProductAnalytics -> consent-aware adapter(s)
Dependency lifecycle:      client composition root + named factories
```

Shared contract flow:

```text
src/lib/modules/<module>/shared/contracts/<capability>.contract.ts
                         |
             +-----------+-----------+
             |                       |
             v                       v
      client featureApi       server route/tRPC adapter
      parses response         parses input + response
             |                       |
             v                       v
      client feature model    controller
                                      |
                                      v
                               use case/service
```

The shared module contains wire contracts only. Database entities stay server-side; form schemas and view models stay client-side.

---

## 3) State Management (Decision Flow)

Use this as a PR review checklist.

```
What kind of state is it?

1) Is it async / IO / server-derived?
   -> Server-state cache (TanStack Query)

2) Is it shareable/bookmarkable via URL?
   -> URL state adapter (Next.js: nuqs)

3) Is it form state (validation + dirty/submission state)?
   -> Form library (React: react-hook-form)

4) Does it have explicit states, guarded transitions, or a complex workflow?
   -> State machine (XState)

5) Is it shared UI coordination state (client-derived)?
   -> Store/provider (React: Zustand)

6) Is it local and ephemeral?
   -> Component-local state
```

Rule of thumb:

```
Do NOT duplicate server/IO state into a store.
Store only IDs/flags and derive server objects from the query cache.
```

---

## 4) Logging, Analytics, and Correlation

```text
Client composition root
  |
  +--> createAppLogger() ---------> debug sink (local)
  |                          \----> Sentry sink (optional/filtered)
  |
  +--> createProductAnalytics() -> consent -> analytics adapter(s)
  |
  +--> createClientApi(logger)
  |
  +--> createFeatureApi(clientApi, logger, toAppError)
```

```text
Create mutation
  -> featureApi
  -> clientApi --------------------> AppLogger transport record
  -> server
  <- response + requestId
  <- typed result / AppError
  +-> ProductAnalytics success event
  +-> cache update
  -> toast/navigation
```

```text
Common context (route/release/trace/safe actor)
  -> logger adapter enrichment
  -> analytics adapter identity/consent

Never:
  business DTO + { logger, analytics, requestId, traceId, runtimeContainer }
```

---

## 5) Edit/Update Form Success Flow (External Data Re-Sync)

```text
Edit/Update Form (reads external query data)
  |
  v
useForm(...) + useQueryProfileCurrent()
  |
  +--> useProfileFormSyncFromQueryData({ data: query.data, reset })
  |       - whenever query.data changes:
  |         reset(mapQueryDataToFormDefaults(query.data))
  |
  v
onSubmit = useCatchErrorToast(async () => {
  await updateMut.mutateAsync(payload)
  await onSubmitInvalidateQueries()    // active matches refetch during invalidation
  // optional navigation
})
  |
  v
query.data refreshes from server
  |
  v
sync hook runs reset(...) with fresh values
  |
  v
UI now matches persisted server truth
(same state as page refresh; checkbox/config values included)
```

Rules:

- Edit/update forms do not reset to empty defaults on success.
- Success path re-syncs from refreshed external data.
- Keep each unit single-responsibility:
  - `onSubmitInvalidateQueries`: invalidation only
  - `useProfileFormSyncFromQueryData`: query-data -> form reset only
- Add explicit `query.refetch()` only for a documented exception: invalidation is configured not to refetch, the target is disabled/inactive but must refresh immediately, or the flow skips invalidation.
