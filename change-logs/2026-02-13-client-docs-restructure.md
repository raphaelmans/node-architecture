# 2026-02-13: Client Docs Restructure

## Summary

Restructured `client/` documentation into:

- `client/core/` for framework-agnostic guidelines and architecture
- `client/frameworks/reactjs/` for React-specific docs (RHF, StandardForm, shadcn/Radix, Zustand)
- `client/frameworks/reactjs/metaframeworks/nextjs/` for Next.js-specific docs (routing/SSR/params, nuqs, env, adapters)

## Notable Changes

- Renamed `client/references/` to `client/drafts/` and fixed `client/drafts/client-side-architecture.md` links.
- Moved client skills out of `client/` into `skills/client/` (including the Next.js auth/routing skill).
- Updated `client/README.md` and root `README.md` to reflect the new structure.

