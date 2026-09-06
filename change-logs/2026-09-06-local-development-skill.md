# Local development guidance and skill

- Added canonical local-development contracts, shared Portless integration, and thin Next.js and Node.js server mappings for Express, Hono, and other HTTP servers, distributed as `$development`.
- Defined installation, package-script updates, current official source resolution, concurrent worktrees, and direct startup verification.
- Kept application code unaware of Portless by supplying the existing app-origin variable from development tooling before startup.
- Connected client, server, and workspace ownership and documented consumer installation and source-drift maintenance.
- Added actual listener verification, optional API self-origins, and same-checkout frontend/API targets for concurrent application sets.
