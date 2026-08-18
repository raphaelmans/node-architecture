# Express Scaffolding

This adapter specialization extends [Node.js scaffolding](../../scaffolding.md) for an existing Express application.

## Preflight and Evidence

Detect the installed Express and Node.js versions, router/middleware composition, async error integration, body parsing, authentication, rate limiting, request context, response envelope, and adapter-test harness. Retrieve version-applicable official Express documentation for middleware, error propagation, request parsing, and routing behavior.

## Adapter Mapping

Place the route in the repository's existing router/module convention and follow [Express](./README.md). Middleware may authenticate, enrich transport context, establish observability, and apply coarse transport gates. The route parses the shared input, calls one controller factory with plain values, and maps the result through centralized response/error handling.

Do not perform repository lookups or ownership, tenant, domain-role, or operation-specific authorization in middleware or the route.

## Verification

Exercise the actual Express router with its controller factory replaced. Verify malformed input, authentication/transport gates, envelope/status mapping, and centralized errors; verify capability authorization in service/use-case tests.
