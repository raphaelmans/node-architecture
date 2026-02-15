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

## Layer Boundaries (Conceptual)

| Layer | Owns | Does not own |
| --- | --- | --- |
| App coordination | provider wiring, theming, toasts | backend data fetching |
| Feature business | orchestration, forms, loading/error wiring | transport details |
| Presentation | render-only UI | fetching/mutations |
| UI primitives | generic, reusable UI | business rules |
