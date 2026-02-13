# Domain Logic (Shared vs Client-Only)

This document describes where **domain-specific rules and transformations** should live, especially when the same logic is needed by both server and client.

## Two Kinds of “Domain Logic”

### 1) Shared Domain Logic (Reusable)

Use this for:

- deterministic calculations (pure functions)
- invariants (validations like “must sum to 100%”)
- canonical transforms that should behave the same everywhere

### 2) Client-Only Transformations (UI/View-Model)

Use this for:

- view-model shaping for a specific screen (grouping, sorting, labeling)
- UX-only reconciliation (placeholders, bucketing, presentation concerns)

## Precedence Rule

When deciding where logic goes:

1. Prefer module-owned shared code: `src/lib/modules/<module>/shared/*`
2. Otherwise keep it feature-local: `src/features/<feature>/(domain.ts|helpers.ts)`

## Module-Owned Shared Code (`<module>/shared/`)

In a Next.js-first repo, place reusable domain logic under:

```text
src/lib/modules/<module>/
  shared/
    schemas.ts      # (optional) Zod schemas + inferred types
    types.ts        # (optional) non-Zod types
    domain.ts       # pure rules + calculations
    transform.ts    # pure canonical transforms (non-UI)
    index.ts        # (optional) stable exports
```

Import from anywhere (client or server) via:

- `@/lib/modules/<module>/shared/...` (preferred)
- `@lib/modules/<module>/shared/...` (if your repo uses `@lib` as the alias)

### Allowed Dependencies

`<module>/shared/*` may import:

- Zod and other packages that are present and safe in both runtimes

`<module>/shared/*` must not import:

- server-only infra (DB/ORM clients, logger, auth session attachment, tRPC router setup)
- client-only UI (React/Next components, shadcn/ui, browser-only APIs)
- environment/config access (`process.env`-driven config)

**Goal:** if a file is under `<module>/shared/`, it should remain importable by both server and client without side effects.

## Feature-Local Logic (`features/<feature>/*`)

Keep client-only transforms inside the feature:

- `src/features/<feature>/domain.ts`: client-only “domain-ish” logic for that feature
- `src/features/<feature>/helpers.ts`: small pure helpers

Use this layer for view-model shaping and screen-specific decisions.

## Example: Ledger Breakdown

Scenario: the server returns ledger entities/records, and the client needs to compute a breakdown and render it.

Shared domain logic (reusable):

```typescript
// src/lib/modules/ledger/shared/domain.ts

export function calcLedgerBreakdown(/* records */) {
  // deterministic calculation
}

export function assertBreakdownSumsTo100(/* breakdown */) {
  // invariant validation (throw or return a typed result)
}
```

Client-only view-model shaping (UI-specific):

```typescript
// src/features/ledger/domain.ts

export function toLedgerBreakdownViewModel(/* breakdown */) {
  // grouping/sorting/labels specific to the screen
}
```

## Monorepo Extraction (Future)

If/when you move to a monorepo:

- `src/lib/modules/<module>/shared/*` becomes the seed that can be extracted into `packages/<module>/src/*`
- imports move from `@/lib/modules/<module>/shared` to `@acme/<module>` (placeholder scope)
