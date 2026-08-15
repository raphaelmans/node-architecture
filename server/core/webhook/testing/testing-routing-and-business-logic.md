# Webhook Testing: Routing + Business Logic

> **Purpose**: Validate that incoming webhook events are routed to the correct specialized controller/handler and safely delegated to one use case.

---

## 1. Routing Tests (Event Type → Handler)

Routing lives in the provider handler registry (for example
`src/lib/modules/webhooks/<provider>/handlers/index.ts`).

Test cases:

- known `event.type` resolves a handler
- unknown `event.type` returns `null`; the route acknowledges it with HTTP 200,
  `processed: false`, and a structured skip record

Key assertion: unsupported events are explicitly observed and acknowledged, not
silently discarded or retried forever.

---

## 2. Handler/Controller Tests (The Most Valuable Layer)

Handlers should:

- validate payload with event-specific Zod schema
- map provider data to the use-case command
- call the appropriate use case (not service directly)

### 2.1 Mapping Tests

Use a **spy** or **mock** use case and assert:

- called once
- called with mapped inputs derived from payload

This is where most webhook bugs happen (field mapping and assumptions).

### 2.2 Idempotency Use-Case Tests

You want explicit tests for duplicates:

- same provider event delivered twice
- same provider event delivered concurrently from two requests/workers
- different provider events referencing the same external object

Expected outcome:

- first run: `processed: true`
- second run: `processed: false` (skipped) with a reason
- concurrent run: exactly one attempt processes and one skips; ordering is not assumed

Use a fake for fast sequential use-case tests. Prove the concurrent outcome
against a real test database so the production unique constraint and
insert-on-conflict behavior are exercised. This aligns with the response
structure in `server/core/webhook/README.md`.

### 2.3 Error Path Tests

- invalid payload → `WEBHOOK_PAYLOAD_INVALID`
- invalid signature → `WEBHOOK_VERIFICATION_FAILED`
- unsupported event type → HTTP 200, `processed: false`, logged skip reason

---

## 3. Framework-Adapter Route Tests (Thin Layer)

The route should remain thin:

- verify signature
- parse base event
- resolve handler
- delegate to handler
- return response envelope

Use a stubbed signature verifier + handler to test:

- correct HTTP status
- correct envelope shape
- safe behavior on errors

---

## 4. Logging Expectations (Optional Assertions)

If you assert logs, focus on structured context (not strings):

- namespaced provider/event metadata from `APP_ATTRIBUTES`
- contextual request ID plus `trace_id` and `span_id`
- event names: `webhook.received`, `webhook.processed`, `webhook.skipped`, `webhook.failed`

These expectations are documented in `server/core/webhook/README.md`.
