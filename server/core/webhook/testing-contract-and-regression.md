# Webhook Testing: Contract + Regression

> **Purpose**: Ensure your webhook integration remains stable over time as code changes and vendor payloads evolve.

---

## 1. Define “Contract” for Webhooks

In this architecture, the contract is:

- The payload shapes we accept (schemas)
- The invariants we rely on (required fields and meanings)
- The mapping from vendor payload → use case inputs

This is enforced by:

- Zod schemas (schema contract)
- mapping tests (behavior contract)
- fixture suites (regression contract)

---

## 2. Regression Fixture Suite

Maintain a set of “golden” fixtures that must always pass.

Guideline:

- Every supported `event.type` has at least one golden fixture
- Every bug fix adds a fixture that would have caught it

### 2.1 Fixture Naming Convention

Keep fixtures easy to scan and diff. Prefer predictable, file-system friendly names.

**Recommended structure (tool-agnostic):**

- `tests/fixtures/webhooks/<provider>/<event.type>/<variant>.json`

**Variants to standardize:**

- `golden.json` — representative “real” payload
- `minimal.json` — smallest payload that should still validate
- `invalid-<reason>.json` — intentional failures (e.g. `invalid-missing-id.json`, `invalid-wrong-type.json`)

**Examples:**

- `tests/fixtures/webhooks/stripe/invoice.paid/golden.json`
- `tests/fixtures/webhooks/stripe/invoice.paid/minimal.json`
- `tests/fixtures/webhooks/stripe/invoice.paid/invalid-missing-customer.json`

**Rules of thumb:**

- One folder per `event.type` keeps related fixtures together.
- Put IDs and timestamps in fixtures only if your parsing/mapping depends on them.
- Keep formatting stable (sorted keys if you can) so diffs stay readable.

---

## 3. Handling Vendor Changes

When the vendor changes payload shape:

1. Add a new fixture representing the vendor’s new payload
2. Decide whether to support both shapes (backward compatibility) or migrate
3. Update schemas and mapping tests
4. Re-run the full fixture suite

This creates an auditable story for stakeholders: “we version payloads intentionally.”

---

## 4. Using The Vendor Simulator as Contract Reinforcement

The simulator should:

- only emit payloads that pass schema validation
- include both happy-path and failure-path payloads
- model duplicates and retries

See: [Vendor Simulator](./testing-vendor-simulator.md)

---

## 5. Optional Future Upgrade: Consumer-Driven Contracts

If you want stronger guarantees later, consider CDC tooling.

Examples:

- Pact
- OpenAPI + schema validation

This is optional and not required to get strong coverage using fixtures + schemas.
