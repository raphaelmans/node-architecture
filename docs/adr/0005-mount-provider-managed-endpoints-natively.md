---
status: accepted
---

# Mount provider-managed endpoints natively

Every application-owned public capability enters application code through a framework-neutral controller, but an adopted authentication provider's own protocol and plugin endpoints are mounted through its documented handler instead. Recreating them as controllers or rewriting them into the business response envelope would fork the provider's wire format, cookies, redirects, and lifecycle and break on every upgrade, so we accept one narrow exception to the controller rule in exchange for staying on the provider's supported path.

## Consequences

- The exception covers provider-managed behavior only. A custom business operation that calls the provider is still an application capability with a controller and capability authorization.
- An application wrapper cannot secure a weaker native route. Required restrictions must hold on the directly reachable provider endpoint through supported configuration or hooks, or the endpoint is not exposed.
- Provider types stop at the integration boundary. Sessions are mapped to a plain actor, and hook transaction guarantees are verified rather than assumed.
