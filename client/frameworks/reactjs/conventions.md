# ReactJS Conventions

> React-specific conventions layered on top of the core client architecture.

## Component Layers (React)

- Pages/routes are owned by the metaframework (e.g. Next.js App Router). React components should treat “page params” and SSR behavior as a metaframework concern.
- Business components orchestrate data + form state and compose sections.
- Presentation components render-only and consume props and/or form context.

## Server State (React Query Adapter)

React-specific rule:

- Define server-state hooks in `src/features/<feature>/hooks.ts`.
- Components do not inline server-state calls.

Where the hooks get data from is an adapter choice:

- Next.js + tRPC: see `client/frameworks/reactjs/metaframeworks/nextjs/trpc.md`
- Next.js + route handlers (HTTP): see `client/frameworks/reactjs/metaframeworks/nextjs/ky-fetch.md`

## Forms

All form implementation details live in:

- `client/frameworks/reactjs/forms-react-hook-form.md`

