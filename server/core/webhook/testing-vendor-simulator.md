# Vendor Simulator (Webhook Emulator / Internal Sandbox)

> **Purpose**: Provide an internal replacement for the vendor during development, QA, and CI. This is not “just a mock”; it is a scenario-driven simulator that produces realistic webhook callbacks.

---

## 1. Terminology (Use These Words Internally)

Avoid calling this “just a mock”. Prefer:

- **Vendor Simulator**
- **Webhook Emulator**
- **Internal Sandbox**

This signals realism, discipline, and maintainability.

---

## 2. What The Simulator Should Do

### 2.1 Accept a Trigger

The simulator accepts a “trigger” event (or command) that starts a scenario.

Examples:

- “execute payment”
- “create subscription”
- “update status to FAILED”

### 2.2 Produce Webhook Callbacks

The simulator sends HTTP callbacks to your real webhook endpoints:

- `POST /api/webhooks/<provider>`

### 2.3 Support Scenarios

Scenarios model real-world behavior:

- success flow: `PENDING → PROCESSED`
- failure flow: `PENDING → FAILED`
- timeout flow: `PENDING → TIMEOUT`
- vendor retry behavior: duplicate delivery of the same event
- delays: simulate “processing takes 30s”

### 2.4 Preserve Correlation

Add a correlation field so you can trace end-to-end:

- `e2eTag`, `requestId`, or metadata field

Goal: “I can find the trigger request and the webhook callback for the same run.”

---

## 3. Contract Safety

To prevent drift:

- Validate outgoing simulator payloads against the same Zod schemas used by the app (or an equivalent JSON schema)
- Store “golden” payload fixtures per event type and scenario

See: [Schema Validation](./testing-schema-validation.md)

---

## 4. Suggested API Shape (Tool-Agnostic)

You can implement the simulator as:

- a separate service (recommended for isolation), or
- a route group within your app/metaframework

Example endpoints (conceptual):

- `POST /simulator/executions` → start a run for a scenario
- `GET /simulator/executions/:id` → inspect status + emitted events
- `POST /simulator/scenarios` → define reusable scenarios

---

## 5. How To Use It In Tests

### 5.1 Deterministic Scenarios

Tests should use:

- a fixed scenario name
- fixed timestamps (or a fake clock)
- fixed ids (where possible)

### 5.2 Assertions

End-to-end assertions typically verify:

- webhook route returned `received: true`
- handler routed correctly
- idempotency handled duplicates
- use case executed side effects exactly once

---

## 6. Minimal “First Scenario”

Start with a single scenario that represents your primary happy path.

Then add:

- 1 failure scenario
- 1 duplicate delivery scenario

This is usually enough to convince stakeholders and de-risk integration.
