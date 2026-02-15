# Client Logging (debug)

Replace ad-hoc `console.log` usage with **scoped logging** that is easy to enable/disable and consistent across the codebase.

We use the `debug` library as the client logging standard.

Reference: https://www.npmjs.com/package/debug

## Why `debug` Instead of `console.log`

- Toggle logs without code changes
- Namespace logs by feature/module
- Avoid polluting production logs by default
- Keep code readable (no `if (dev) log(...)` everywhere)

## Where We Log (By Layer)

Default rule: **log at boundaries**, not inside presentation components.

Primary (standard, repeatable logs):

- `clientApi` (transport boundary): request/response metadata, durations, typed failures, retry decisions.
- `featureApi` (domain boundary): mapping/normalization decisions and domain transforms (meaningful, not chatty).

Secondary (debugging only):

- Anywhere else in feature business components, query adapters, or hooks when debugging locally.

Avoid by default:

- Presentation components (`*-fields.tsx`, render-only components).

## Correlation Context

Carry request correlation metadata through boundary logs whenever available:

- `requestId` (primary)
- optional path context (for example current pathname)
- optional actor context (`userId`, `sessionId`) when safe

Convention:

- attach correlation metadata at transport/metaframework boundaries
- pass metadata into logger calls rather than rebuilding ad-hoc context per component

## Namespace Structure

Use a predictable namespace convention:

```text
app:<feature>:<area>
```

Examples:

- `app:profile:api`
- `app:profile:ui`
- `app:auth:api`
- `app:chat:stream`

Rule: namespaces reflect ownership (feature) and context (api/ui/etc).

## Architecture (Strategy + Adapter + Wrapper)

```text
features/* code
  |
  v
Logger API (our contract)
  |
  v
Wrappers (context/redaction/sampling)
  |
  v
Strategy selection (debug/console/noop)
  |
  v
Provider (debug lib / console)
```

## Runtime Placement (Next.js Convention)

Implementation lives under:

```text
src/common/logging/
  types.ts
  adapters/
    debug.ts
    console.ts
    noop.ts
  wrappers/
    with-context.ts
    with-redaction.ts
    with-sampling.ts
  strategy.ts
  feature.ts
```

## Logger Contract (App-Level API)

All app code uses this interface (never `debug` directly):

```ts
export type LogMeta = Record<string, unknown>

export interface Logger {
  debug(msg: string, meta?: LogMeta): void
  info(msg: string, meta?: LogMeta): void
  warn(msg: string, meta?: LogMeta): void
  error(msg: string, meta?: LogMeta): void

  child(scope: string): Logger
}
```

## Provider Strategy (Defaults + Break-Glass Override)

Defaults:

- Development: provider is `debug` (still off unless enabled via `localStorage.debug`).
- Production: provider is `noop` (ignore `localStorage.debug`).

Break-glass override (last effort debugging):

- If `NEXT_PUBLIC_ALLOW_BREAK_GLASS_LOGGING === "true"`, allow `localStorage["app:log:provider"]` to override the provider to one of:
  - `"debug"`
  - `"console"`
  - `"noop"`

This supports:

- force-enable logs when you must debug a production issue
- force-disable logs even in dev when noise is too high

## Toggle Logs (debug)

`debug` reads `localStorage.debug`.

Enable:

```js
localStorage.debug = "app:profile:*"
// or:
localStorage.debug = "app:*"
```

Disable:

```js
localStorage.debug = ""
```

Refresh after changing.

## Break-Glass Examples

Force-enable client logs (only if allowed by env):

```js
localStorage["app:log:provider"] = "debug"
localStorage.debug = "app:*"
```

Force-disable logs:

```js
localStorage["app:log:provider"] = "noop"
localStorage.debug = ""
```

Reset to defaults:

```js
localStorage.removeItem("app:log:provider")
```

## Do / Don't

Do:

- Use feature-scoped namespaces.
- Keep provider selection in one place (strategy).
- Keep provider specifics isolated (adapters).
- Add context/redaction once (wrappers).

Don't:

- Import `debug` directly inside features.
- Leave long-term `console.log` sprinkled throughout the codebase.
- Log sensitive data (tokens, passwords, PII).
