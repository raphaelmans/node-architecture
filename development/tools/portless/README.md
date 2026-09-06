# Portless Integration

Apply the [local development contract](../../core/local-development.md). Portless supplies the local routing layer for both [Next.js](../../frameworks/nextjs/README.md) and [Node.js servers](../../runtimes/nodejs/README.md). Framework-specific listening and configuration behavior belongs in those mappings.

## Source Resolution and Installation

Inspect the installed or selected Portless/Node versions, package manager, lockfile, scripts, worktrees, proxy state, and workspace orchestrator. Resolve current installation requirements, naming, child environment, configuration, machine effects, and lifecycle from the [official Portless documentation and source](https://github.com/vercel-labs/portless#readme), using release-matched sources where needed. Follow repository dependency policy and obtain outstanding machine-effect authorization described in the core contract.

Install required development tooling and wire package startup while preserving the direct command, arguments, signals, and exit behavior. A wrapper must not recursively invoke itself. Preserve existing orchestration; [Turborepo's development guide](https://turborepo.dev/docs/crafting-your-repository/developing-applications) and [environment guide](https://turborepo.dev/docs/crafting-your-repository/using-environment-variables) own task lifecycle, environment filtering, and cache behavior. Keep local dev tasks non-cached and long-running where appropriate. Do not replace root orchestration with a second process supervisor.

## Startup Values

Verify the selected release's child environment. Portless currently supplies `PORT` and its resolved `PORTLESS_URL`; these represent different things: the internal listener and externally reachable origin. The framework mapping must prove the server listens on the assigned port. A hardcoded port or explicit CLI flag may override the environment.

When an application needs a self-origin, a development launcher maps the resolved origin into that deployable's existing variable before startup. Portless-specific variables stay out of application schemas and source. Receive injected values in the child context; parent-shell expansion can occur before they exist. Preserve environment precedence and framework materialization timing. A server with no self-origin consumer needs no new origin variable.

## Multiple Applications and Worktrees

Resolve each process independently, then connect consumers to the intended server in the same checkout through their existing service-origin settings. Never assign every app the frontend origin or construct the API origin by string replacement on a frontend hostname. Use authoritative tool resolution or an explicit project-owned mapping verified against registered routes. Resolve required peer URLs before starting consumers that capture them; preserve startup ordering and readiness handling. A filtered single-app start must report a missing required peer rather than silently falling back to another checkout.

Origin isolation does not isolate databases, queues, or other stateful services. Preserve their existing configuration and report shared state when assessing checkout isolation.

For browser-to-API calls, retain the app's chosen direct cross-origin or same-origin proxy arrangement. Verify CORS/cookies for the actual frontend origin. For forwarding between Portless routes, check upstream Host routing and TLS trust against official guidance; do not disable certificate verification or broaden trusted proxies to resolve a local failure.

Verify two concurrent application sets, including frontend-to-server requests reaching the matching checkout, and verify the direct startup path. Exercise existing WebSocket/streaming behavior when used. Stop only owned test processes and routes; preserve shared proxy state.
