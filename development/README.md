# Local Development

Canonical guidance for starting and reaching Next.js applications, Express/Hono servers, and other Node.js HTTP servers during local development. Single-project and monorepo placement preserve the same contract.

- [Local Development Contract](core/local-development.md) owns stable origins, startup, worktree isolation, and verification.
- [Portless Integration](tools/portless/README.md) owns shared tool setup and workspace integration.
- [Next.js](frameworks/nextjs/README.md) maps framework startup and browser configuration.
- [Node.js Servers](runtimes/nodejs/README.md) maps Express, Hono, and other Node.js server startup.
- [Development Skill](skill/SKILL.md) distributes curated guidance as `$development`.

Development owns local process and origin setup. Client and server own application configuration and behavior. Monorepo owns workspace manifests, dependency edges, and shared task coordination. Production delivery is outside this surface.
