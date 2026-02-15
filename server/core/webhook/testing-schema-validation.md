# Webhook Testing: Schema Validation (Zod)

> **Purpose**: Catch payload drift and vendor surprises early by validating webhook payloads against Zod schemas.

---

## 1. Architecture Alignment

This follows the webhook flow defined in `server/core/webhook/architecture.md`:

1. Verify signature
2. Parse base event (Zod)
3. Route by `event.type`
4. Validate event-specific payload (Zod)
5. Delegate to use case

---

## 2. Fixture Strategy

Maintain fixtures as your long-term regression safety net.

For each `event.type`, keep:

- **golden fixture**: representative real payload
- **minimal valid fixture**: smallest payload that should still pass
- **invalid fixtures**: common breakages

Suggested structure (conceptual):

- `tests/fixtures/webhooks/<provider>/<event.type>.golden.json`
- `tests/fixtures/webhooks/<provider>/<event.type>.minimal.json`
- `tests/fixtures/webhooks/<provider>/<event.type>.invalid-*.json`

---

## 3. What To Test

### 3.1 Base Event Parsing

Ensure your base schema accepts what you need to route:

- `id`
- `type`
- `data.object` (or equivalent vendor structure)

### 3.2 Event-Specific Parsing

For each event:

- `safeParse(goldenFixture)` succeeds
- `safeParse(invalidFixture)` fails with meaningful issues

### 3.3 Negative Cases You Want Early

- missing `id`
- unknown `type`
- wrong nested type (string vs number)
- missing `data.object.id`

---

## 4. Mapping Errors to Standard Error Codes

If parsing fails, you should return (or throw) a consistent error:

- `WEBHOOK_PAYLOAD_INVALID`

If signature verification fails:

- `WEBHOOK_VERIFICATION_FAILED`

These codes are documented in `server/core/webhook/architecture.md`.

---

## 5. Vendor Simulator Alignment

The Vendor Simulator should validate its outgoing payloads against these same schemas.

See: [Vendor Simulator](./testing-vendor-simulator.md)
