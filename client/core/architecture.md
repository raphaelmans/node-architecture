# Client Architecture (Agnostic)

Core rules that should survive framework changes (React/Vue/Svelte) and metaframework changes (Next.js/etc).

## Principles

- **Feature-based organization:** co-locate components, hooks/adapters, schemas, and helpers by feature.
- **Business vs presentation split:** orchestration + IO wiring is separate from render-only components.
- **Coordinate high. Fetch low. Render dumb.:**
  - app-wide providers coordinate only (no server data bootstrapping into context)
  - server/IO state is fetched close to the consuming feature section
  - presentation remains render-only
- **Explicit boundaries:** IO happens behind interfaces; cache behavior is defined in one place.
- **Testable feature APIs:** feature endpoints are exposed via `I<Feature>Api` + class implementations with injected dependencies.
- **One wire contract:** client and server import the same Zod input/response schemas from `src/lib/modules/<module>/shared/contracts/`.
- **Separate telemetry ports:** operational diagnostics use `AppLogger`; behavioral events use `ProductAnalytics`.
- **Context at boundaries:** correlation, release, route, and safe actor context are enriched by adapters instead of traveling in business DTOs.
- **Composition-root ownership:** dependency-heavy infrastructure is built through factories and assembled once with explicit browser/SSR lifetimes.

## Layer Boundaries (Conceptual)

| Layer | Owns | Does not own |
| --- | --- | --- |
| App coordination | provider wiring, theming, toasts | backend data fetching |
| Composition root | provider construction, factories, environment strategy, dependency lifetimes | business behavior, service-locator access |
| Feature business | orchestration, forms, loading/error wiring | transport details |
| Query adapter | server-state/cache lifecycle; successful mutation analytics when it owns the action | transport logging, vendor SDKs |
| Feature API | endpoint paths, wire parsing, mapping, error normalization | cache behavior, product analytics by default |
| Client API | transport mechanics, request correlation, transport logs | domain behavior, product analytics |
| Shared contract | serialized API input/response shape | ORM entities, server commands, UI form state |
| Presentation | render-only UI | fetching/mutations |
| UI primitives | generic, reusable UI | business rules |

## Telemetry Flow

```text
feature/query/client boundary
       |                 |
       v                 v
   AppLogger       ProductAnalytics
       |                 |
 debug/Sentry      analytics adapter(s)
```

Neither port justifies a new controller layer. Add feature workflow orchestration only when the UX flow itself requires it.
