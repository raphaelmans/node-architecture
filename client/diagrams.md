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
  - depends on featureApi (interface)
  |
  v
[featureApi (endpoint-scoped)]
  - one per feature domain (profileApi, billingApi, ...)
  - owns endpoint paths + request/response typing
  - parses at boundaries (Zod)
  - maps DTO -> feature model
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
