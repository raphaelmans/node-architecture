# AGENTS-MD-ALIGNMENT

> How to wire the architecture guides into your project's `AGENTS.md` or `CLAUDE.md`
> after running `copy-guides.sh`.

---

## What Was Copied

Running `copy-guides.sh` placed all architecture guides under `guides/` in your repo:

```text
guides/
  client/
    core/          ← MANDATORY for all client work
    frameworks/    ← Opt-in per tech stack
  server/
    core/          ← MANDATORY for all server work
    runtime/       ← Opt-in per tech stack
  README.md
  AGENTS-MD-ALIGNMENT.md   ← this file
```

This file tells you how to reference these guides in `AGENTS.md` (for Codex / OpenAI agents)
or `CLAUDE.md` (for Claude / Claude Code). Both formats are supported; the template below works
for either filename.

---

## Critical AI Behavior Rules

These rules MUST appear in your `AGENTS.md` / `CLAUDE.md`. They govern how any AI agent
interacts with the codebase.

### 1. No Automatic Refactoring

> **If existing code does not follow a guide, note it — do NOT fix it unless explicitly
> instructed by the user.**

Existing codebases have history, constraints, and in-progress migrations. Touching code
outside the scope of a task creates noise, unexpected diffs, and broken migrations.
The agent's job is to produce correct new work and flag deviations, not to refactor proactively.

This rule applies even when the guide is MANDATORY.

### 2. Core Standards Are Non-Negotiable for New and Modified Files

Any file that is **created or modified** in a task must comply with the core standards.
No exceptions. If compliance requires a design discussion, surface it before writing code.

### 3. Framework Docs Are Additive, Not Override

Framework-specific guides (React, Next.js, tRPC, etc.) layer on top of core. They do not
replace core contracts. When a framework doc conflicts with core, core wins.

### 4. Ignore Guides That Do Not Apply

If a guide references a library or pattern not present in this project, ignore it entirely.
Do not import libraries, create abstractions, or suggest patterns from inapplicable guides.

---

## Step 1 — Identify Your Stack

Mark which technologies are in use. This determines which guides to include.

**Client**
- [ ] React
- [ ] Next.js (App Router)
- [ ] Other (framework docs not available — client core only)

**Server**
- [ ] Next.js Route Handlers
- [ ] tRPC
- [ ] Supabase (auth / DB)
- [ ] OpenAPI / REST
- [ ] Async background jobs (outbox pattern)
- [ ] Webhooks (inbound)
- [ ] Express
- [ ] NestJS

---

## Step 2 — Select Guide References

### Always Include: Client Core (MANDATORY)

```
guides/client/core/overview.md
guides/client/core/architecture.md
guides/client/core/conventions.md
guides/client/core/folder-structure.md
guides/client/core/client-api-architecture.md
guides/client/core/domain-logic.md
guides/client/core/error-handling.md
guides/client/core/validation-zod.md
guides/client/core/server-state-tanstack-query.md
guides/client/core/query-keys.md
guides/client/core/state-management.md
guides/client/core/logging.md
guides/client/core/testing.md
```

### Always Include: Server Core (MANDATORY)

```
guides/server/core/overview.md
guides/server/core/conventions.md
guides/server/core/api-contracts-zod-first.md
guides/server/core/api-response.md
guides/server/core/error-handling.md
guides/server/core/endpoint-naming.md
guides/server/core/id-generation.md
guides/server/core/transaction.md
guides/server/core/logging.md
guides/server/core/rate-limiting.md
guides/server/core/testing-service-layer.md
```

---

### If React → add

```
guides/client/frameworks/reactjs/overview.md
guides/client/frameworks/reactjs/conventions.md
guides/client/frameworks/reactjs/composition-react.md
guides/client/frameworks/reactjs/error-handling.md
guides/client/frameworks/reactjs/server-state-patterns-react.md
guides/client/frameworks/reactjs/forms-react-hook-form.md
guides/client/frameworks/reactjs/state-zustand.md
guides/client/frameworks/reactjs/ui-shadcn-radix.md
```

### If Next.js (client) → add (requires React block above)

```
guides/client/frameworks/reactjs/metaframeworks/nextjs/overview.md
guides/client/frameworks/reactjs/metaframeworks/nextjs/folder-structure.md
guides/client/frameworks/reactjs/metaframeworks/nextjs/routing-ssr-params.md
guides/client/frameworks/reactjs/metaframeworks/nextjs/environment.md
guides/client/frameworks/reactjs/metaframeworks/nextjs/url-state-nuqs.md
guides/client/frameworks/reactjs/metaframeworks/nextjs/trpc.md         ← only if tRPC
guides/client/frameworks/reactjs/metaframeworks/nextjs/ky-fetch.md     ← only if REST/fetch
guides/client/frameworks/reactjs/metaframeworks/nextjs/query-keys.md
```

### If Next.js Route Handlers (server) → add

```
guides/server/runtime/nodejs/metaframeworks/nextjs/route-handlers.md
guides/server/runtime/nodejs/metaframeworks/nextjs/caching-revalidation.md
guides/server/runtime/nodejs/metaframeworks/nextjs/next-config-security.md
guides/server/runtime/nodejs/metaframeworks/nextjs/formdata-transport.md  ← only if FormData uploads
guides/server/runtime/nodejs/metaframeworks/nextjs/cron-routes.md         ← only if cron jobs
guides/server/runtime/nodejs/metaframeworks/nextjs/metadata-seo.md        ← only if SEO metadata
```

### If tRPC → add

```
guides/server/runtime/nodejs/libraries/trpc/integration.md
guides/server/runtime/nodejs/libraries/trpc/authentication.md
guides/server/runtime/nodejs/libraries/trpc/rate-limiting.md
```

### If Supabase → add

```
guides/server/runtime/nodejs/libraries/supabase/integration.md
guides/server/runtime/nodejs/libraries/supabase/auth.md
```

### If OpenAPI / REST → add

```
guides/server/core/zod-openapi-generation.md
guides/server/runtime/nodejs/libraries/openapi/parity-testing.md  ← only if dual tRPC+OpenAPI
```

### If Async Jobs → add

```
guides/server/core/async-jobs-outbox.md
```

### If Webhooks → add

```
guides/server/core/webhook/architecture.md
guides/server/core/webhook/testing-overview.md
guides/server/core/webhook/testing-checklist.md
guides/server/core/webhook/testing-schema-validation.md
guides/server/core/webhook/testing-routing-and-business-logic.md
guides/server/core/webhook/testing-contract-and-regression.md
guides/server/core/webhook/testing-test-doubles.md
guides/server/core/webhook/testing-vendor-simulator.md
```

### Discard — Do Not Reference

These exist in the guides tree but should not be referenced in `AGENTS.md` / `CLAUDE.md`
unless your project explicitly uses them:

| Path | Discard when |
| --- | --- |
| `guides/server/runtime/nodejs/metaframeworks/express/` | Not using Express |
| `guides/server/runtime/nodejs/metaframeworks/nestjs/` | Not using NestJS |
| `guides/server/core/webhook/` | No inbound webhooks |
| `guides/server/core/async-jobs-outbox.md` | No background jobs |
| `guides/server/runtime/nodejs/metaframeworks/nextjs/cron-routes.md` | No cron jobs |
| `guides/server/runtime/nodejs/metaframeworks/nextjs/metadata-seo.md` | No SEO metadata |
| `guides/server/runtime/nodejs/metaframeworks/nextjs/formdata-transport.md` | No file uploads |
| `guides/server/runtime/nodejs/libraries/openapi/parity-testing.md` | Single transport only |
| `guides/client/frameworks/reactjs/metaframeworks/nextjs/trpc.md` | No tRPC |
| `guides/client/frameworks/reactjs/metaframeworks/nextjs/ky-fetch.md` | Using tRPC only |
| `guides/*/drafts/` | Always — drafts are never canonical |

---

## Step 3 — AGENTS.md / CLAUDE.md Template

Copy this into your project's `AGENTS.md` or `CLAUDE.md`. Replace the `[INCLUDE IF ...]`
placeholders with the relevant paths from Step 2, or delete the block if it does not apply.

```markdown
# Architecture Guides

This project uses architecture guides from `guides/`. They are maintained externally and
copied via `copy-guides.sh`. Do not edit files inside `guides/` directly.

## Behavior Rules

- **No automatic refactoring.** If existing code does not follow a guide, note the deviation
  and continue. Do NOT refactor code outside the current task scope unless explicitly asked.
- **Core is mandatory for new and modified files.** Any file you create or modify must comply
  with the core standards listed below.
- **Framework guides are additive.** They layer on top of core; they do not replace it.
- **Ignore guides that do not apply to this project.** Do not import new libraries or suggest
  patterns from irrelevant guides.

## Mandatory — Client Core

Read and follow all of these for any client-side work:

- guides/client/core/overview.md
- guides/client/core/architecture.md
- guides/client/core/conventions.md
- guides/client/core/folder-structure.md
- guides/client/core/client-api-architecture.md
- guides/client/core/domain-logic.md
- guides/client/core/error-handling.md
- guides/client/core/validation-zod.md
- guides/client/core/server-state-tanstack-query.md
- guides/client/core/query-keys.md
- guides/client/core/state-management.md
- guides/client/core/logging.md
- guides/client/core/testing.md

## Mandatory — Server Core

Read and follow all of these for any server-side work:

- guides/server/core/overview.md
- guides/server/core/conventions.md
- guides/server/core/api-contracts-zod-first.md
- guides/server/core/api-response.md
- guides/server/core/error-handling.md
- guides/server/core/endpoint-naming.md
- guides/server/core/id-generation.md
- guides/server/core/transaction.md
- guides/server/core/logging.md
- guides/server/core/rate-limiting.md
- guides/server/core/testing-service-layer.md

## Framework Guides — [INCLUDE IF REACT]

- guides/client/frameworks/reactjs/overview.md
- guides/client/frameworks/reactjs/conventions.md
- guides/client/frameworks/reactjs/composition-react.md
- guides/client/frameworks/reactjs/error-handling.md
- guides/client/frameworks/reactjs/server-state-patterns-react.md
- guides/client/frameworks/reactjs/forms-react-hook-form.md
- guides/client/frameworks/reactjs/state-zustand.md
- guides/client/frameworks/reactjs/ui-shadcn-radix.md

## Framework Guides — [INCLUDE IF NEXT.JS CLIENT]

- guides/client/frameworks/reactjs/metaframeworks/nextjs/overview.md
- guides/client/frameworks/reactjs/metaframeworks/nextjs/folder-structure.md
- guides/client/frameworks/reactjs/metaframeworks/nextjs/routing-ssr-params.md
- guides/client/frameworks/reactjs/metaframeworks/nextjs/environment.md
- guides/client/frameworks/reactjs/metaframeworks/nextjs/url-state-nuqs.md
- guides/client/frameworks/reactjs/metaframeworks/nextjs/query-keys.md
# [ADD trpc.md if tRPC, ky-fetch.md if REST/fetch]

## Framework Guides — [INCLUDE IF NEXT.JS SERVER]

- guides/server/runtime/nodejs/metaframeworks/nextjs/route-handlers.md
- guides/server/runtime/nodejs/metaframeworks/nextjs/caching-revalidation.md
- guides/server/runtime/nodejs/metaframeworks/nextjs/next-config-security.md
# [ADD cron-routes.md if cron, formdata-transport.md if uploads, metadata-seo.md if SEO]

## Framework Guides — [INCLUDE IF tRPC]

- guides/server/runtime/nodejs/libraries/trpc/integration.md
- guides/server/runtime/nodejs/libraries/trpc/authentication.md
- guides/server/runtime/nodejs/libraries/trpc/rate-limiting.md

## Framework Guides — [INCLUDE IF SUPABASE]

- guides/server/runtime/nodejs/libraries/supabase/integration.md
- guides/server/runtime/nodejs/libraries/supabase/auth.md

## Framework Guides — [INCLUDE IF OPENAPI]

- guides/server/core/zod-openapi-generation.md
# [ADD parity-testing.md only if running both tRPC + OpenAPI]

## Feature Guides — [INCLUDE IF ASYNC JOBS]

- guides/server/core/async-jobs-outbox.md

## Feature Guides — [INCLUDE IF WEBHOOKS]

- guides/server/core/webhook/architecture.md
- guides/server/core/webhook/testing-overview.md
- guides/server/core/webhook/testing-checklist.md
- guides/server/core/webhook/testing-schema-validation.md
- guides/server/core/webhook/testing-routing-and-business-logic.md
- guides/server/core/webhook/testing-contract-and-regression.md
- guides/server/core/webhook/testing-test-doubles.md
- guides/server/core/webhook/testing-vendor-simulator.md
```

---

## Step 4 — Keep Guides in Sync

When guides are updated in the source repo, re-run `copy-guides.sh` to refresh your
`guides/` directory. The script replaces the entire `client/` and `server/` trees,
so your `AGENTS.md` / `CLAUDE.md` references stay valid as long as you do not rename paths
in your local config manually.

```bash
# From the node-architecture repo:
./copy-guides.sh /path/to/your/project
```

No manual merging is required. The guide content is always replaced wholesale.
