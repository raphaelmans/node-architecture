# Client Routing Convention Leaf

Date: 2026-08-31

## Summary

Added an opinionated Next.js routing convention beneath the existing `$client` slices. The broad `nextjs` and `state-realtime` slices now conditionally disclose a `nextjs/routing` convention leaf instead of adding another top-level slice.

## Canonical Guidance

- Added `client/frameworks/reactjs/metaframeworks/nextjs/routing-convention.md` as the canonical ownership and implementation convention for `appRoutes`, route policies, route inputs, and nuqs-backed query state.
- Replaced the legacy-style global query-key example with feature-owned nuqs parser maps reused by client hooks, page loaders, and link serializers.
- Distinguished client-cache-driven shallow updates from query-driven RSC updates.
- Kept domain validation separate from query representation parsing.
- Updated the Next.js overview, folder structure, routing/params guide, and index to point to the new convention.

## Progressive Skill Loading

- Added `client/skill/references/nextjs/routing.md` as a convention leaf.
- Added conditional leaf routing to `client/skill/SKILL.md` and the broad Next.js slice.
- Kept state ownership in `state-realtime`; activated Next.js URL-state implementation routes to the convention leaf.
- Recorded `Skill slice` and `Convention leaf` as distinct project terms in `CONTEXT.md`.

## Maintenance

- Upgraded the client source-map schema to version 2 with separate `slices` and `leaves` collections.
- Added convention-leaf parent validation and targeted fingerprint refresh support.
- Updated contributor guidance to review and refresh either kind of portable reference.

## Validation

- Confirmed current Next.js typed-route and route-type generation guidance against official Next.js documentation.
- Confirmed current nuqs parser reuse, multi-key state, server loader, serializer, and shallow-update behavior against official nuqs documentation.
- Ran the official skill validator against `client/skill/`.
- Confirmed all mapped slice and convention-leaf fingerprints are current.
- Confirmed local links and code fences resolve in every changed or new Markdown file.
- Confirmed Python syntax, JSON structure, and `git diff --check` pass.
