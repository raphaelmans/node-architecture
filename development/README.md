# Development

Canonical guidance for architecture reference index initialization and local development. Initialization discovers installed skills and repository packages; local startup guidance covers Next.js applications, Express/Hono servers, and other Node.js HTTP servers. Single-project and monorepo placement preserve the same contracts.

- [Architecture Initialization](core/initialization.md) owns `/development init`, repository discovery, the navigation-only `ARCHITECTURE.md` index and its lightweight entry point.
- [Local Development Contract](core/local-development.md) owns stable origins, startup, worktree isolation, and verification.
- [Portless Integration](tools/portless/README.md) owns shared tool setup and workspace integration.
- [Next.js](frameworks/nextjs/README.md) maps framework startup and browser configuration.
- [Node.js Servers](runtimes/nodejs/README.md) maps Express, Hono, and other Node.js server startup.
- [Development Skill](skill/SKILL.md) distributes curated guidance as `$development`.

Development owns architecture index initialization and local process/origin setup. Initialization selects applicable installed guidance without taking over its conventions: client and server own application configuration and behavior; monorepo owns workspace manifests, dependency edges, and shared task coordination. Production delivery is outside this surface.
