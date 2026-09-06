# Local Development Contract

## Ownership

Local development establishes reachable, stable application origins and repeatable process startup across client and server responsibilities. It preserves application architecture and supports both single-project and monorepo topologies. A full-stack application can serve browser and server roles at one origin; role names do not imply separate processes.

Application boundaries continue to own configuration validation, browser visibility, callbacks, cookie policy, and trusted origins. Workspace coordination retains package-local task commands and root orchestration. Development tooling supplies values to those existing boundaries.

## Application Origins and Worktrees

Reuse the deployable's existing application-origin variable and schema. Resolve the current checkout's local origin in development tooling before the application starts or materializes browser configuration. Application source and executable environment schemas need no development-proxy-specific variables, imports, or fallback branches.

Concurrent checkouts must receive distinct, predictable origins. Use the selected tool's authoritative resolved identity rather than duplicating its naming algorithm. Detect collisions across projects, apps, and worktrees; never take over an unrelated route or terminate its process automatically. Identify the checkout when reporting its origin.

The supplied origin must agree with the browser-visible URL and generated absolute callbacks or links. Within one application, browser API calls remain relative. Separate deployables retain their existing explicit service-origin configuration; another application's URL cannot be inferred from the caller's self-origin. Resolve peer targets before consumers materialize configuration and verify requests stay within the same checkout. Origin isolation does not imply isolated databases or queues. A server with no self-origin consumer needs no new origin variable.

Supply overrides only to the local child process where practical. Preserve existing environment files, secrets, production settings, and schema ownership. Do not create a shared root environment file. Public origin values contain no credentials. Restart when an origin changes so already-materialized configuration cannot retain another checkout's URL.

## Installation and Startup

An explicit setup request includes installing necessary development dependencies, updating manifests and lockfiles with the existing package manager, configuring startup, and verifying the result. Reuse existing compatible installations and configuration. Record selected versions and their official sources; follow existing dependency pinning and tool-management conventions.

Determine whether installation is project-owned or machine-owned from repository evidence and current vendor guidance. Explain the selected placement and any shared-machine version implications. Obtain any still-required installation approval before executing it; existing explicit authorization remains valid. Do not silently upgrade an incompatible runtime or replace a package manager.

Preserve a documented direct-start command. Repeated setup must not stack wrappers or create duplicate scripts. Keep task logic inside its owning package and preserve the existing workspace orchestrator. Non-interactive task startup must not depend on an unanswered machine setup prompt.

Machine trust, privileged proxy setup, hosts-file edits, and startup services require explicit authorization for those effects. LAN access and tunnels are separately selected capabilities. Check existing proxy state before changing shared settings, because other projects may use it.

## Verification and Recovery

Verify the named origin, TLS trust, page rendering, a same-origin application request, and hot reload where applicable. Verify the app's configured origin and an existing absolute-link or callback construction path; local reachability alone does not prove provider acceptance. Inspect provider callback restrictions when authentication is activated and report external registration work that remains.

Run two concurrent checkout instances and confirm distinct URLs and correct per-checkout application origins. Exercise existing worktrees or scoped temporary checkouts when feasible. If unavailable, report worktree verification as incomplete instead of claiming isolation from a naming example.

Verify direct startup without the proxy, including a correct direct application origin and callback behavior. It must not inherit a stale proxied origin. Record the direct URL and any explicit port/origin inputs required; do not promise automatic collision avoidance for direct startup.

Stop only processes created for verification and release their routes. Preserve shared proxy infrastructure used by other applications. Re-run setup to check idempotency through the resulting manifest/configuration diff. Document how to restore the previous startup path and remove project-owned integration; machine-wide cleanup is a separate operation because it may affect other projects.
