---
name: server
description: Apply this repository's server architecture when designing, explaining, reviewing, testing, implementing, or refactoring backend features. Use for Node.js server work involving framework-neutral controllers, use cases, services, repositories, transactions, Zod contracts, errors, logging, tracing, product analytics, authentication, authorization, webhooks, jobs, tRPC, OpenAPI, Next.js route handlers, Express, Hono, Pino, or Supabase. Route each request through the smallest relevant architecture slices and do not use for client-only work.
---

# Server Architecture

Route server work through modular architecture slices. Load only the references required by the task, compose slices when concerns cross boundaries, and preserve the user's requested operation: explanation, diagnosis, review, planning, or implementation.

## Start

1. Inspect the target repository, requested files, applicable instructions, and installed stack before proposing changes.
2. Determine whether the user asked to explain, diagnose, review, plan, implement, or refactor. Do not turn a read-only request into a mutation.
3. Select the smallest relevant slice set from the routing table.
4. Read every selected reference completely before acting.
5. Apply provider or framework guidance only when that technology is present or explicitly requested.
6. For implementation, verify the narrowest meaningful boundary first and preserve unrelated user changes.

## Route Slices

| Slice | Load when the task involves | Reference |
| --- | --- | --- |
| `foundations` | kernel boundaries, modules, controllers, services/use cases, repositories, factories, DI, folder structure | [references/foundations.md](references/foundations.md) |
| `contracts` | Zod wire contracts, commands/view models, envelopes, pagination, public errors, endpoint naming, OpenAPI generation | [references/contracts.md](references/contracts.md) |
| `data-flow` | adapter-to-controller flow, reads/writes, transactions, persistence, IDs, repository boundaries, result mapping | [references/data-flow.md](references/data-flow.md) |
| `operations` | jobs, outbox, events, rate limiting, cron, webhooks, retries, idempotency, side-effect timing | [references/operations.md](references/operations.md) |
| `security` | authentication, sessions, authorization, cookies, redirects, keys, RLS, secrets, security headers | [references/security.md](references/security.md) |
| `telemetry` | `AppLogger`, Pino, OpenTelemetry, correlation, event naming, product analytics, privacy | [references/telemetry.md](references/telemetry.md) |
| `testing` | adapter/controller/application/repository tests, database concurrency, webhook fixtures, transport parity | [references/testing.md](references/testing.md) |
| `runtimes` | Node.js, tRPC, OpenAPI, Next.js, Express, Hono, NestJS, FormData, caching, Supabase | [references/runtimes.md](references/runtimes.md) |

Treat `core`, `architecture`, `layers`, and `module` as aliases for `foundations`; `schema`, `api`, `dto`, and `error` as aliases for `contracts`; `transaction`, `database`, `repository`, and `persistence` as aliases for `data-flow`; `job`, `event`, `outbox`, `webhook`, and `cron` as aliases for `operations`; `auth` as an alias for `security`; `logging`, `analytics`, `observability`, and `tracing` as aliases for `telemetry`; and `framework`, `adapter`, `trpc`, `openapi`, `next`, `express`, `hono`, and `supabase` as aliases for `runtimes`.

When the user explicitly names slices, load those slices. Add another slice only when the task clearly crosses its boundary, and state the added slice briefly. Examples:

- Add a Next.js JSON endpoint: `contracts` + `data-flow` + `runtimes` + `testing`
- Migrate a tRPC capability to Express: `foundations` + `contracts` + `runtimes` + `testing`
- Implement a Stripe webhook: `contracts` + `operations` + `security` + `telemetry` + `testing` + `runtimes`
- Add Supabase authentication: `security` + `runtimes` + `testing`; add `data-flow` when application roles or user provisioning use the database
- Audit logs and analytics: `telemetry`; add `operations` for outbox-backed reliable delivery

When invoked without a task, show the slice menu with two or three context-aware examples. Do not start an audit or implementation automatically.

## Preserve These Invariants

- Use the call chain `framework adapter -> framework-neutral controller -> one service or one use case -> repository/provider port`; return typed results in reverse.
- Keep controllers plain TypeScript. They map shared inputs and outputs, call exactly one application boundary, and never import framework request/response types.
- Use a service for one-domain behavior and a use case for multi-service workflows, transaction ownership, outbox coordination, or post-commit side effects.
- Keep repositories responsible for persistence only. Translate known provider/database failures at the adapter boundary and never leak vendor errors inward.
- Define one shared Zod wire contract under the owning module's isomorphic `shared/contracts` boundary. Keep envelopes in the shared kernel and server-only commands inside the server module.
- Normalize malformed input to `ValidationError`; throw typed `AppError` subclasses for expected failures; expose only allowlisted public details.
- Keep `TransactionContext` opaque and database-only. Do not merge request, tracing, logger, actor, or analytics data into transaction options.
- Inject narrow ports through factories. Never pass a container or generic context object through application layers.
- Keep operational `AppLogger` records separate from typed `ProductAnalytics` events. Obtain request and trace correlation from active runtime context rather than business DTOs.
- Apply core rules before runtime additions. Framework and provider guidance extends the architecture; it never overrides it.
- Do not introduce a library, provider, outbox, controller, use case, or abstraction merely because a reference mentions it. The target stack and behavior must justify it.

## Review and Change Discipline

For reviews and audits:

1. Report evidence with file and line references.
2. Separate contract violations, correctness or security risks, and optional improvements.
3. Explain the impact and owning layer.
4. Do not fix findings unless the user asks for changes.

For implementation and refactoring:

1. Preserve unrelated and in-progress changes.
2. Make new or modified files comply with the selected slices.
3. Keep compatibility migrations incremental.
4. Add or update tests at the same boundary as the behavior.
5. Run targeted checks first, then broader validation when justified.
