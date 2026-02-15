# Next.js Documentation

> Next.js-specific conventions layered on top of `client/core/` and `client/frameworks/reactjs/`.

This section focuses on App Router patterns, routing/params, SSR/RSC considerations, server-side auth guarding, and backend IO adapters used by React features (tRPC and/or route-handler HTTP clients).

Read order before using this folder:

1. [Client Core Onboarding](../../../../core/onboarding.md)
2. [ReactJS Index](../../README.md)
3. This Next.js folder

| Document | Description |
| --- | --- |
| [Overview](./overview.md) | App Router conventions, guards, route registry |
| [Routing + SSR + Params](./routing-ssr-params.md) | Where route parsing/validation belongs |
| [Environment Variables](./environment.md) | Type-safe env vars (`@t3-oss/env-nextjs`) |
| [Folder Structure (Next.js)](./folder-structure.md) | App Router file layout and route groups |
| [URL State (nuqs)](./url-state-nuqs.md) | URL query state patterns |
| [tRPC (Next.js)](./trpc.md) | tRPC strategy within the client-api architecture |
| [Ky Fetch](./ky-fetch.md) | Non-tRPC HTTP clients with `ky` + typed errors |
| [React Server-State Cookbook](../../server-state-patterns-react.md) | Mixed invalidation ownership patterns (hook-owned/component-coordinator/hybrid) |
| [Query Keys](../../../../core/query-keys.md) | Query key conventions (Query Key Factory) |
| [Auth + Routing Skill](../../../../../skills/client/metaframeworks/nextjs/nextjs-auth-routing/SKILL.md) | Type-safe routing + proxy-based auth guarding |
| [Form Standards (Draft)](../../../../drafts/09-standard-form-components.md) | StandardForm components reference |
