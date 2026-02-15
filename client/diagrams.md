# Client Architecture Diagrams (ASCII)

This file is a visual companion to the written docs in `client/core/` and `client/frameworks/`.

---

## 1) Documentation Structure (This Repo)

```
client/
  README.md
  diagrams.md

  core/                           # framework-agnostic
    overview.md
    architecture.md
    conventions.md
    client-api-architecture.md
    validation-zod.md
    domain-logic.md
    server-state-tanstack-query.md
    query-keys.md
    state-management.md
    error-handling.md
    logging.md
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
          query-keys.md            # moved to client/core/query-keys.md (keep as redirect)

  drafts/                          # detailed legacy references (non-canonical)
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
  - depends on I<Feature>Api contract
  |
  v
[featureApi boundary]
  - one per feature domain: I<Feature>Api + class <Feature>Api + create<Feature>Api(...)
  - owns endpoint paths + request/response schemas
  - parses at boundaries (Zod)
  - maps DTO -> feature model
  - normalizes unknown -> AppError via toAppError
  - depends on clientApi (interface)
  |
  v
[clientApi (transport + cross-cutting)]
  - base URL, headers/auth attachment
  - response envelope decoding
  - typed, inspectable errors
  - retry/timeouts (if global)
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
```

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

4) Is it shared UI coordination state (client-derived)?
   -> Store/provider (React: Zustand)

5) Is it local and ephemeral?
   -> Component-local state
```

Rule of thumb:

```
Do NOT duplicate server/IO state into a store.
Store only IDs/flags and derive server objects from the query cache.
```

---

## 4) Request and Error Correlation (Boundary-Owned)

```text
Request
  |
  v
Route / proxy boundary
  - attach/propagate request metadata (e.g. requestId, pathname)
  |
  v
Server transport handler (tRPC / route.ts)
  - enforce security/rate limits
  - return structured error envelope (code/message/requestId/details)
  |
  v
clientApi / transport adapter
  - map transport error -> typed client error
  |
  v
toAppError(err)
  - normalize to AppError
  |
  +--> logger facade (correlated logs)
  |
  +--> toast facade (user-facing message)
  |
  v
UI branches on AppError.kind only
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
  await onSubmitInvalidateQueries()    // Promise.all([...]) when needed
  await onSubmitRefetch()              // query.refetch()
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
  - `onSubmitRefetch`: refetch only
  - `useProfileFormSyncFromQueryData`: query-data -> form reset only
