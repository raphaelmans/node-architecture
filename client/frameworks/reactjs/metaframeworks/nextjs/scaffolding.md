# Next.js Client Scaffolding

This guide extends [React scaffolding](../../scaffolding.md) for an existing Next.js repository. Core safety, evidence, atomicity, and boundary rules remain authoritative.

In a monorepo, the Next.js application remains the owner of routes, client/server composition, and app environment validation. Consume activated internal packages through public exports; resolve cross-package changes and build-system behavior through the monorepo contract and current version-matched official sources.

## Preflight

Detect before planning:

- installed Next.js, React, Node.js, and TypeScript versions;
- App Router, Pages Router, or a deliberate hybrid;
- source root and route groups;
- `next.config.js`, `next.config.mjs`, or supported TypeScript configuration;
- package module type and path aliases;
- Server/Client Component boundaries, server actions, route handlers, and SSR request scope;
- existing environment validation, transport, tRPC/HTTP adapters, cache policy, and test/build setup.

Retrieve version-applicable official Next.js documentation for configuration formats, router APIs, rendering lifecycle, caching, environment behavior, and production build requirements. Current documentation must be checked rather than inferred from examples in this repository.

## Boundary Mapping

- Route files and route groups belong to Next.js.
- Client Components contain only browser-reachable dependencies and explicitly declared public environment values.
- Server Components, route handlers, and server actions may use server-only adapters through a server composition root.
- Request-scoped dependencies are created only when they capture cookies, headers, sessions, or other request-bound values.
- Shared contracts remain browser-safe and do not import Next.js or server infrastructure.
- Feature APIs and query adapters retain the client-core call chain; route handlers retain the server-core call chain.

Use the repository's established App Router or Pages Router placement. Canonical mode follows the version-applicable Next.js folder guidance in [Folder Structure](./folder-structure.md), not a universal path from core.

## Configuration and Environment

Preserve the repository's existing supported config format. Do not place ESM syntax or top-level `await` in a CommonJS `next.config.js`. Use:

- `next.config.js` with `require`/`module.exports` for CommonJS;
- `next.config.mjs` with `import`/`export default` for ESM;
- a TypeScript config only when the installed Next.js version supports it.

For environment validation, follow [Environment Variables](./environment.md). Detect the installed Next.js and T3 Env versions, choose their version-applicable runtime wiring, and verify build-time validation through a production build.

## Verification

Run focused client boundary tests, typecheck, and the actual Next.js production build. Treat Server/Client import violations, invalid config module syntax, environment validation failures, and standalone-output packaging errors as scaffold failures. Report the official sources and applicable versions used for every version-sensitive decision.
