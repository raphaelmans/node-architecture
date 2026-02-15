# Webhook Testing Overview

> **Purpose**: Provide a practical, tool-agnostic testing strategy for inbound webhooks that keeps our system stable while the vendor is unstable.

This guide is a specialized extension of the global server testing standard:

- [Testing Service Layer](../testing-service-layer.md)

---

## 1. What We’re Trying to Prove

Webhook integrations are high-risk because we don’t control delivery timing, retries, duplicates, or vendor payload drift.

This testing guide aims to ensure:

- We reject invalid or unverifiable webhooks safely
- We parse and validate payloads deterministically (Zod)
- We route each `event.type` to the correct handler
- Handlers delegate to **use cases** (not services directly)
- Idempotency rules prevent double-processing
- Responses follow our standard envelope and are safe for vendor retries
- We can run end-to-end scenarios using a **Vendor Simulator** (internal sandbox)

---

## 2. Testing Layers (Fast → Realistic)

Use multiple layers so failures are caught early and cheaply.

| Layer | What it validates | Typical technique |
| --- | --- | --- |
| Schema tests | Payload shape + invariants | Zod parsing with fixtures |
| Routing tests | `event.type` → handler resolution | handler registry tests |
| Handler tests | Mapping + use case invocation + idempotency | spies/mocks + fakes |
| Route/controller tests | Signature verification + envelope response | stub verifier + call route directly |
| Contract/regression tests | “We still accept what we used to accept” | fixture suite + golden payloads |
| End-to-end (internal) | Full flow under real HTTP | Vendor Simulator callbacks |

---

## 3. “No Vendor Dependency” Principle

All tests in this guide are designed to run without the vendor’s sandbox.

We achieve this by:

- Treating vendor payloads as fixtures (golden samples)
- Using test doubles at the edges (signature verification, external I/O)
- Using a **Vendor Simulator** as a controlled source of webhook callbacks for full-flow tests

---

## 4. Document Index

- [Testing Test Doubles](./testing-test-doubles.md)
- [Vendor Simulator](./testing-vendor-simulator.md)
- [Schema Validation](./testing-schema-validation.md)
- [Routing + Business Logic](./testing-routing-and-business-logic.md)
- [Contract + Regression](./testing-contract-and-regression.md)
- [Testing Checklist](./testing-checklist.md)

---

## 5. Recommended Starting Point (If You’re New)

1. Add/maintain fixtures for each webhook event type.
2. Write schema tests that parse the fixtures.
3. Add routing tests for known/unknown `event.type`.
4. Write handler tests that:
   - assert mapping to use case input
   - enforce idempotency
5. Add a minimal Vendor Simulator scenario for the main “happy path”.

---

## 6. Non-Goals

These docs do not attempt to:

- Validate the vendor’s uptime or retry guarantees
- Replace proper staging environments
- Mandate a specific test runner (Jest/Vitest/etc.)
- Redefine global service-layer testing rules (see core testing standard)
