# Webhook Testing: Routing + Business Logic

> **Purpose**: Validate that incoming webhook events are routed to the correct handler and processed safely (idempotency + use case delegation).

---

## 1. Routing Tests (Event Type → Handler)

Routing lives in the provider handler registry (e.g. `modules/webhooks/<provider>/handlers/index.ts`).

Test cases:

- known `event.type` resolves a handler
- unknown `event.type` returns `null` (or throws a `WEBHOOK_HANDLER_NOT_FOUND` error at the route layer)

Key assertion: no event type is silently ignored.

---

## 2. Handler Tests (The Most Valuable Layer)

Handlers should:

- validate payload with event-specific Zod schema
- enforce idempotency through domain logic (repository check)
- call the appropriate use case (not service directly)

### 2.1 Mapping Tests

Use a **spy** or **mock** use case and assert:

- called once
- called with mapped inputs derived from payload

This is where most webhook bugs happen (field mapping and assumptions).

### 2.2 Idempotency Tests

You want explicit tests for duplicates:

- same provider event delivered twice
- different provider events referencing the same external object

Expected outcome:

- first run: `processed: true`
- second run: `processed: false` (skipped) with a reason

This aligns with the response structure in `server/core/webhook/architecture.md`.

### 2.3 Error Path Tests

- invalid payload → `WEBHOOK_PAYLOAD_INVALID`
- invalid signature → `WEBHOOK_VERIFICATION_FAILED`
- handler not found → `WEBHOOK_HANDLER_NOT_FOUND`

---

## 3. Route/Controller Tests (Thin Layer)

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

- `provider`, `eventType`, `eventId`, `requestId`
- event names: `webhook.received`, `webhook.processed`, `webhook.skipped`, `webhook.failed`

These expectations are documented in `server/core/webhook/architecture.md`.
