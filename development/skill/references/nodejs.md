# Node.js Servers

Use for Express, Hono on Node.js, and other Node.js HTTP servers alongside foundations and the selected proxy-tool reference. Inspect the real bootstrap/listener, HTTP adapter, runner, watch/build pipeline, environment validation, and shutdown behavior.

Prove the assigned internal port reaches the listening call. Environment injection alone does not configure an Express app, Hono adapter, or custom server with a hardcoded listener. Reuse validated port/host configuration; if absent, make the smallest generic deployable-bootstrap change while retaining direct defaults. Keep Portless-specific reads and dependencies out of application code and schemas. Verify a usable port and proxy-reachable local bind address without altering production policy.

- Express: trace the actual listener, including separately constructed servers. Resolve the installed major's [Express API](https://expressjs.com/en/api.html) and [Node HTTP API](https://nodejs.org/api/http.html).
- Hono: detect the Node adapter and resolve listen options and shutdown from the [Node.js guide](https://hono.dev/docs/getting-started/nodejs) and [adapter source](https://github.com/honojs/node-server). Hono routes alone do not establish listener configuration.
- Other HTTP servers: derive configuration from their installed framework/adapter's official docs; do not infer compatibility merely from Node.js usage. Non-HTTP workers retain ordinary orchestration without proxy routes.

Keep the external self-origin optional and reuse its existing server variable when callbacks/absolute links require it. Do not add browser-prefixed variables to an API server. Preserve runner/watch behavior, assigned-port propagation across restarts, and signal cleanup. Check container reachability when applicable.

Verify an existing endpoint through the named URL, actual listener, watch/restart, clean shutdown, direct startup, and activated streaming/WebSocket behavior. For a separate frontend, test the configured API target and CORS/cookies in each concurrent checkout. Do not claim unsupported protocols or unexercised frameworks are verified.
