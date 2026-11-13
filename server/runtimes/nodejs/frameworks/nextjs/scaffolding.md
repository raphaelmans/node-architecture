# Next.js Server Scaffolding

This adapter specialization extends [Node.js scaffolding](../../scaffolding.md) for an existing Next.js server boundary.

## Preflight

Detect the installed Next.js and Node.js versions, App/Pages Router, route-handler placement, config module format, runtime target, authentication/session integration, environment validation, response envelope, and tests. Retrieve version-applicable official Next.js documentation for every config, request-lifecycle, runtime, caching, or deployment decision.

## Adapter Mapping

For App Router JSON endpoints, map the framework-adapter role to the repository's `app/**/route` convention and follow [Route Handlers](./route-handlers.md). The route handler:

- extracts and parses the request through the shared contract;
- authenticates and applies rate limits or transport-wide gates;
- establishes request observability;
- calls one controller factory with narrow plain input/actor values;
- applies the established response envelope, status mapping, and central error integration.

It does not query repositories, orchestrate services, or enforce ownership/tenant/domain capability policy.

Preserve supported configuration format and runtime host. Follow [Environment Variables](./environment-variables.md), [Next Config Security](./next-config-security.md), and version-applicable caching guidance when those capabilities are activated.

## Verification

Test the real route adapter with its controller factory replaced, then run typecheck and the actual Next.js production build. Verify authentication/transport gates separately from service/use-case capability authorization.
