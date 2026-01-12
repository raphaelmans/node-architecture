# Webhook Testing Checklist

> A concise checklist you can share with engineering leadership and product to show a robust testing posture for webhook integrations.

---

## 1. Schema + Payload Safety

- [ ] Base event schema parses all supported webhook types
- [ ] Event-specific schemas exist for each supported `event.type`
- [ ] Golden fixtures exist for each supported `event.type`
- [ ] Invalid fixtures exist for common breakages (missing id, wrong nested types)

---

## 2. Signature Verification

- [ ] Missing signature header fails with `WEBHOOK_VERIFICATION_FAILED`
- [ ] Invalid signature fails with `WEBHOOK_VERIFICATION_FAILED`
- [ ] Signature verification happens before payload processing

---

## 3. Routing

- [ ] Known `event.type` resolves to a handler
- [ ] Unknown `event.type` fails with `WEBHOOK_HANDLER_NOT_FOUND`
- [ ] No events are silently ignored

---

## 4. Handler Behavior

- [ ] Payload validation failures return `WEBHOOK_PAYLOAD_INVALID`
- [ ] Handler delegates to use case (not service directly)
- [ ] Mapping from payload → use case input is tested

---

## 5. Idempotency + Retries

- [ ] Duplicate webhook delivery is safe (no double side effects)
- [ ] Response indicates skip via `processed: false`
- [ ] Skip reasons are logged

---

## 6. Response + Observability

- [ ] Success response matches envelope schema (`received: true`, `eventId`, `processed`)
- [ ] Errors use standard error envelope and codes
- [ ] Logs include `provider`, `eventType`, `eventId`, `requestId`
- [ ] Logs emit: `webhook.received`, `webhook.processed`, `webhook.skipped`, `webhook.failed`

---

## 7. Vendor Simulator (Internal Sandbox)

- [ ] Simulator can run at least one happy-path scenario
- [ ] Simulator can produce at least one failure-path scenario
- [ ] Simulator can deliver duplicates to test idempotency
- [ ] Simulator payloads are validated against schemas
- [ ] Simulator supports correlation via `e2eTag` (or equivalent)
