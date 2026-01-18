# Next.js Documentation

> Next.js-specific conventions layered on top of the frontend architecture.

## Overview

This section focuses on App Router patterns, route access control, server-side auth guarding, and client data fetching with both tRPC React Query hooks and non-tRPC HTTP clients (ky + Query Key Factory). Start with the overview, then use the skill guide for implementation details.

| Document | Description |
| --- | --- |
| [Overview](./overview.md) | App Router conventions, auth guards, route registry |
| [Ky Fetch](./ky-fetch.md) | Non-tRPC HTTP clients with `ky` + typed errors |
| [Query Keys](./query-keys.md) | Query Key Factory conventions for non-tRPC React Query |
| [Auth + Routing Skill](./skills/nextjs-auth-routing/SKILL.md) | Type-safe routing + proxy-based auth guarding |
| [Form Standards](../references/09-standard-form-components.md) | StandardForm components + RHF patterns |
