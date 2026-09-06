# Local Development Foundations

Own local startup, stable origins, machine prerequisites, and concurrent checkout isolation. Preserve deployable-owned application configuration and package-owned task logic. Client and server roles inside one deployable do not require separate processes. Apply the same outcomes in single-project and monorepo topologies.

## Setup

Inspect manifests, lockfiles, runtime/tool versions, scripts, environment schemas/examples, worktrees, current proxy state, and task orchestration. Reuse compatible setup. An explicit setup request includes necessary dependency installation and package/configuration edits within its authorization; preserve package-manager and version policy. Explain machine versus project installation placement based on current official guidance and repository evidence. Obtain outstanding authorization for machine trust, privileged setup, hosts edits, or services before those effects; network sharing is separately selected.

Reuse the existing application-origin variable. Development tooling supplies the resolved checkout origin before app startup and browser configuration materialization. Application source and environment schemas must not acquire proxy-specific reads or dependencies. Keep overrides local to the child process, preserve secrets and production values, and avoid a shared root environment file.

Use the tool's resolved identity rather than reproducing hostname construction. Concurrent checkouts need distinct origins; detect collisions without taking over unrelated routes. Preserve relative browser requests within one app. Separate apps retain their own explicit service-origin configuration, resolved before consumer startup and verified against the same checkout. A server without a self-origin consumer needs no new origin variable. Backing services may remain shared despite distinct URLs.

Preserve direct startup and existing workspace orchestration. Avoid duplicate wrappers, recursive scripts, and machine prompts hidden inside non-interactive tasks. Do not silently upgrade runtimes or replace package managers. Review shared proxy users before changing machine-wide settings.

## Verify and Hand Off

- Verify trusted local HTTPS, page rendering, an app request, and hot reload when applicable.
- Confirm the existing application-origin value and an activated absolute-link/callback path agree with the browser URL. Check provider registrations and cookie scope when relevant.
- Run two checkout instances concurrently and verify each app's configured origin and response identity. Report missing evidence if this cannot be exercised.
- Verify direct startup without proxy dependencies or a stale proxy origin, including its own origin-dependent behavior.
- Repeat setup to check idempotency through the resulting diff; preserve existing scripts and settings.
- Stop only verification-owned processes/routes. Document restoration of project startup; shared-machine cleanup is separate.

Report changed files, selected versions, official sources, actual verification, and unresolved external setup. Installation alone does not establish success.
