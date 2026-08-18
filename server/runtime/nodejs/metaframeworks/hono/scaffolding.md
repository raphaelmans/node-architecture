# Hono Scaffolding

This adapter specialization extends [Node.js scaffolding](../../scaffolding.md) for an existing Hono application.

## Preflight and Evidence

Detect the installed Hono version, runtime host, router composition, validator middleware, authentication, rate limiting, context variables, response envelope, and adapter-test harness. Retrieve version-applicable official Hono and runtime-host documentation for validation, middleware, context, errors, and deployment behavior.

## Adapter Mapping

Place the route in the repository's existing convention and follow [Hono](./README.md). Middleware may authenticate, establish observability, and apply coarse transport gates. The handler parses the shared input, calls one controller factory with plain values, and maps the result through centralized response/error handling.

Framework context does not cross the controller boundary. Do not perform repository lookups or ownership, tenant, domain-role, or operation-specific authorization in middleware or the handler.

## Verification

Exercise the actual Hono application with its controller factory replaced. Include a type-checked adapter test for shared input validation and verify capability authorization separately in service/use-case tests.
