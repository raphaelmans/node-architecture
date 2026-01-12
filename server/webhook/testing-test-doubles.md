# Webhook Testing: Test Doubles (Stub / Mock / Spy / Fake / Simulator)

> **Purpose**: Establish shared language and clear guidelines for “mocking” in webhook tests.

---

## 1. Key Idea

Webhook code has two distinct concerns:

1. **Boundary concerns**: signature verification, reading raw body, extracting headers
2. **Business concerns**: schema validation, routing, idempotency, delegation to use cases

We use test doubles to isolate and prove behavior at each layer.

---

## 2. Test Double Types

### 2.1 Stub

A **stub** returns a fixed result. It does not record calls or enforce expectations.

**Use for:** returning a known user, a known repository result, or a known signature verification outcome.

**Example (conceptual):**

- `verifySignature(rawBody, signature) → parsedEvent` (always returns a fixture)

**Pros:** simplest, fastest.

**Cons:** can become unrealistic if fixtures are not maintained.

---

### 2.2 Spy

A **spy** records how it was called, so the test can assert interactions.

**Use for:** verifying that the handler calls the correct use case with the expected mapped input.

**Example assertions:**

- “use case called once”
- “called with `externalId = ...` derived from payload”

---

### 2.3 Mock

A **mock** is a spy with expectations baked in (call counts, parameters).

**Use for:** interaction-heavy tests (routing → correct handler; handler → correct use case).

**Guideline:** prefer spies unless you truly need strict expectations.

---

### 2.4 Fake

A **fake** is a working simplified implementation.

**Use for:** idempotency and stateful behavior without a real DB.

**Examples:**

- in-memory repository keyed by `providerEventId` or `externalId`
- fake clock/time provider to simulate delays/retries deterministically

**Pros:** realistic behavior, deterministic.

**Cons:** requires discipline to keep aligned with production behavior.

---

### 2.5 Simulator / Emulator (Vendor Simulator)

A **simulator** is a realistic replacement for an external system.

**In this architecture:** the Vendor Simulator triggers webhook callbacks to your real webhook endpoint.

**Use for:** end-to-end confidence, QA demos, scenario testing while vendor is unstable.

See: [Vendor Simulator](./testing-vendor-simulator.md)

---

## 3. What To Double In Webhook Code

| Boundary | What to double | Recommended type |
| --- | --- | --- |
| Signature verification | provider SDK call | stub or fake |
| Use cases | side effects orchestration | spy/mock |
| Repositories | idempotency checks | fake |
| Logger | event emission | spy (optional) |
| Time | delays/retries | fake clock (if needed) |

---

## 4. Anti-Patterns

- Over-mocking internals instead of asserting outcomes (brittle tests)
- Asserting exact log message strings (prefer structured fields if you assert logs)
- Using mocks everywhere (hard to refactor)
- Skipping fixtures maintenance (schemas drift silently)

---

## 5. Default Recommendation

- Use **fixtures + schema tests** as your “safety net”.
- Use **spies** to verify mapping and use case calls.
- Use **fakes** for idempotency and lightweight persistence.
- Use the **Vendor Simulator** for a small number of end-to-end scenarios.
