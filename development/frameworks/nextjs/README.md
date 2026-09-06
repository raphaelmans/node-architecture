# Next.js with Portless

Apply the [local development contract](../../core/local-development.md) and [shared Portless integration](../../tools/portless/README.md) to a detected Next.js application. This mapping owns framework startup and browser configuration. For a separate Express/Hono or other Node.js API process, also select the [Node.js server mapping](../../runtimes/nodejs/README.md) and verify same-checkout peer origins.

## Resolve the Implementation

Inspect Next.js, Node.js, Portless, the package manager, lockfile, router, environment adapter, scripts, worktree metadata, and any workspace orchestrator. Compare the desired outcomes with sources applicable to the installed or selected releases:

- [Portless documentation and source](https://github.com/vercel-labs/portless#readme), including installation, worktrees, child environment, proxy lifecycle, and workspace integration.
- [Next.js environment variables](https://nextjs.org/docs/app/guides/environment-variables), including load order and browser materialization.
- [Next.js CLI](https://nextjs.org/docs/app/api-reference/cli/next), for startup and port behavior.
- [Next.js development origins](https://nextjs.org/docs/app/api-reference/config/next-config-js/allowedDevOrigins), when the detected proxy/hostname needs framework origin configuration.
- [Turborepo documentation](https://turborepo.com/docs), only when detected, for package task execution and environment availability.

Use matching release documentation or tagged source when latest documentation differs from the selected version. Do not install the latest release merely to match an example. Record sources and versions in the implementation handoff.

## Preserve the Existing Origin Contract

When a codebase uses `NEXT_PUBLIC_APP_URL` for its own origin and callbacks, keep using it. Development startup supplies the resolved worktree URL to that variable before Next.js starts. If another name already owns this contract, preserve that name. Avoid introducing an additional app-origin configuration abstraction just for Portless.

Portless currently exposes its resolved origin to child processes as `PORTLESS_URL`. Verify this against the selected release. If a bridge is needed, it belongs in development startup tooling: receive the resolved origin, supply the existing application variable, then launch the original Next.js command with its arguments, assigned port, environment, signals, and exit behavior intact. Do not add Portless reads to application source or executable environment schemas.

Do not expand a child-injected value in the parent shell before it exists. Check environment precedence and public-value materialization against Next.js documentation. Keep per-checkout values process-local rather than committing branch-specific URLs or modifying shared environment files. Direct startup must supply or retain the correct direct origin without using the Portless bridge.

## Package and Framework Integration

Install and wire the selected integration using the existing package manager and dependency policy. Preserve a direct Next.js command, reuse coherent script names, and avoid recursion between the proxy entrypoint and original command. In a workspace, retain package-owned startup and existing orchestration; resolve strict task environment filtering at the actual injection boundary.

Read current Portless defaults before first startup and obtain authorization for machine effects that are not already approved. Do not automatically install a boot service or expose applications beyond the local machine. Keep framework origin allowances narrow and justified by actual requests; do not weaken application CSRF, cookie, callback, or proxy-trust checks to make development pass.

For authentication, compare callback registrations and cookie scope with both checkout origins. A provider may reject local hostnames or dynamic callbacks. Report that constraint and select an explicit supported setup with the user; do not claim end-to-end authentication from a successful local redirect alone.

Apply every verification and recovery outcome in the core contract, including two simultaneous checkouts and direct startup. This repository packages guidance; live application verification occurs in the consuming repository.
