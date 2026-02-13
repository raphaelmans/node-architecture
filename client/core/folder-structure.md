# Folder Structure (Agnostic)

This document describes framework-agnostic client directory conventions.

## High-Level Structure

```text
src/
  <routes>/            # Metaframework-owned routes (Next.js: app/)
  common/              # App-wide shared utilities
  components/          # Shared UI components
  features/            # Feature modules (primary unit of organization)
  hooks/               # Global framework hooks (React only)
  lib/                 # Core logic & integrations
```

Metaframework-specific routing conventions:

- Next.js: `client/frameworks/reactjs/metaframeworks/nextjs/folder-structure.md`

## Feature Module Structure

```text
src/features/<feature>/
  components/
    <feature>-view.tsx          # business component (composition + wiring)
    <feature>-fields.tsx        # presentation components (render-only)
  hooks.ts                      # query adapter (framework-specific)
  api.ts                        # featureApi (endpoint-scoped)
  dtos.ts                       # DTO schemas/types + mapping helpers
  types.ts                      # non-DTO types
  domain.ts                     # pure business rules
  helpers.ts                    # small pure helpers
```

