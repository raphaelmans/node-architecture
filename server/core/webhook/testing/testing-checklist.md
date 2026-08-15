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
- [ ] Unknown `event.type` returns HTTP 200 with `processed: false`
- [ ] Unknown events emit `webhook.skipped` with reason `unhandled_event_type`

---

## 4. Handler Behavior

- [ ] Payload validation failures return `WEBHOOK_PAYLOAD_INVALID`
- [ ] Handler delegates to use case (not service directly)
- [ ] Mapping from payload → use case input is tested

---

## 5. Idempotency + Retries

- [ ] Duplicate webhook delivery is safe (no double side effects)
- [ ] Concurrent duplicate deliveries are protected by a database unique constraint
- [ ] Response indicates skip via `processed: false`
- [ ] Skip reasons are logged

---

## 6. Response + Observability

- [ ] Success response matches envelope schema (`received: true`, `eventId`, `processed`)
- [ ] Errors use standard error envelope and codes
- [ ] Logs use `APP_ATTRIBUTES` for provider/event metadata and contextual request ID
- [ ] Operational event names use `otel.event.name`
- [ ] Trace correlation uses `trace_id`, `span_id`, and `trace_flags`
- [ ] Logs emit: `webhook.received`, `webhook.processed`, `webhook.skipped`, `webhook.failed`

---

## 7. Vendor Simulator (Internal Sandbox)

- [ ] Simulator can run at least one happy-path scenario
- [ ] Simulator can produce at least one failure-path scenario
- [ ] Simulator can deliver duplicates to test idempotency
- [ ] Simulator or integration harness can deliver duplicates concurrently
- [ ] Simulator payloads are validated against schemas
- [ ] Simulator supports correlation via `e2eTag` (or equivalent)
