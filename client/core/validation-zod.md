# Zod Validation (Agnostic)

Use Zod at **boundaries** to validate and normalize data.

## Rules

- Parse inputs at the edge (UI boundary, API boundary).
- Normalize ambiguous UI values (e.g. `""` to `undefined`) at the schema boundary.
- Keep reusable primitives in shared schema modules; keep feature-specific composition in the feature.

## Recommended Schema Layers

- DTO schema (API contract)
- Feature/UI schema (composed from DTO schema + UI-only fields)
- Inferred TypeScript types from schemas

For detailed reference examples, see `client/drafts/01-zod-schema-architecture.md`.

