# Node.js Server Local Development

Apply the [local development contract](../../core/local-development.md) and [Portless integration](../../tools/portless/README.md) to Express, Hono on Node.js, and other Node.js HTTP servers. Inspect the real executable entrypoint, runner/watch command, HTTP adapter, environment boundary, listener, and shutdown handling before changing startup.

## Listening Boundary

The assigned internal port must reach the server's actual listening call. A framework being compatible with Node.js does not establish that its application consumes an environment-provided port. Reuse existing validated port/host configuration. If listening is hardcoded, make the smallest generic configuration change at the deployable bootstrap boundary, retaining direct-start defaults. This can require application startup code changes, but must not introduce Portless-specific reads or dependencies.

Validate the port as a usable TCP port and bind the local child listener to an address reachable by the proxy, normally loopback. Inspect an existing container/network boundary before assuming the host's loopback reaches the server. Do not change production binding policy merely to configure local startup.

| Server | Evidence to resolve |
| --- | --- |
| Express | Trace bootstrap to the actual listener, including a separately created HTTP/HTTPS server; pass the existing validated host/port configuration there. Resolve the installed major's [Express API](https://expressjs.com/en/api.html) and [Node.js HTTP documentation](https://nodejs.org/api/http.html). |
| Hono on Node.js | Inspect the installed Node adapter and its server options; Hono routing alone does not establish a listener. Use the [Hono Node.js guide](https://hono.dev/docs/getting-started/nodejs) and [Node adapter source](https://github.com/honojs/node-server) matching the selected version. |
| Other Node.js HTTP servers | Find the server/adapter's official listen, environment, watch, and shutdown documentation. Verify actual host/port consumption and protocol compatibility before claiming support. |

Preserve the existing runner, compilation and watch pipeline, and graceful shutdown. Ensure restart keeps the assigned listener configuration and stopping dev leaves no orphan listener. Workers without an HTTP endpoint retain ordinary process orchestration and receive no invented hostname.

## Origins and Verification

A self-origin is optional: retain the existing server variable only when absolute links/callbacks consume it. Do not introduce a Next.js public-variable prefix into an API server. Keep the internal listener distinct from the external HTTPS origin; TLS termination does not require adding TLS code to the app.

For a separate frontend, configure the correct same-checkout API target and validate existing CORS, cookie, redirect, and proxy-trust behavior with the server architecture owner. Do not infer a trusted origin from arbitrary forwarded headers.

Verify an existing HTTP endpoint through the named URL, the actual internal listener, restart/watch behavior, signal shutdown, and independent direct startup. Test activated streaming or WebSocket endpoints. With concurrent checkouts, verify each frontend reaches its own API and each server's generated absolute URLs point to the intended origin. Report untested frameworks or external dependencies explicitly.
