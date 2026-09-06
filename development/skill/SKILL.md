---
name: development
description: Configure, explain, review, and troubleshoot local application startup, stable origins, and concurrent worktrees. Install and configure Portless for Next.js, Express, Hono, and other Node.js HTTP servers, including Turborepo workspaces. Production deployment is outside this skill.
---

# Local Development

Preserve the requested operation. Setup includes necessary installation, package scripts, configuration, and verification; explanation and review remain read-only.

Read [foundations](references/foundations.md) for all work. Select additional references by the processes being configured:

| Slice | Load when |
| --- | --- |
| [portless](references/portless.md) | Portless installation, startup, routing, or worktree integration |
| [nextjs](references/nextjs.md) | A Next.js app, including its integrated server routes |
| [nodejs](references/nodejs.md) | An Express, Hono, or other Node.js HTTP server process |

For a Next.js frontend and separate API, load both runtime mappings plus Portless. Do not load the generic Node.js mapping merely because Next.js runs on Node. Other server frameworks use the Node.js contract with their own version-matched official startup documentation; non-HTTP workers do not need proxy routes.

Examples: `$development setup nextjs`, `$development setup hono`, `$development setup nextjs and express in this monorepo`, `$development troubleshoot worktree callbacks`. Treat `express`, `hono`, and `node` as selectors for `nodejs` while preserving the detected framework.

Inspect the consuming repository and installed versions. Resolve version-sensitive behavior from matching official documentation before changing files or installing tools. Keep application code unaware of the development proxy by supplying its existing origin variable at startup.

Coordinate with `$client` for browser configuration, `$server` for callback/cookie/trusted-origin behavior, and `$monorepo` for cross-package manifests and task coordination when available. These skills own their existing boundaries. The references here retain the minimum required coordination rules when companion skills are unavailable.

When invoked without a task, show the relevant setup/review/troubleshooting choices; do not start installation automatically.
