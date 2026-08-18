# Environment Configuration (Next.js)

> Validate configuration once at the Next.js runtime boundary, then inject narrow values through composition roots and factories.

This guide recommends [`@t3-oss/env-nextjs`](https://env.t3.gg/docs/nextjs) as the Next.js adapter for typed environment configuration. It is a runtime concern, not a core architecture dependency: Express, Hono, workers, and other runtimes may implement the same boundary with a different validator.

## Architecture Boundary

```text
process.env
  -> validated Next.js env module
  -> composition root / controller factory
  -> narrow infrastructure configuration
  -> service or use case through an explicit port
```

Rules:

- Read `process.env` only inside the env module and test/runtime bootstrap code.
- Import the validated `env` object only from runtime adapters, composition roots, and infrastructure factories.
- Pass narrow configuration such as `{ connectionString }` or `{ apiKey }`; never inject the complete env object or `process.env`.
- Keep controllers, services, use cases, repositories, entities, and shared wire contracts independent of environment access.
- Treat client exposure as an explicit public API. Only variables declared under `client` and prefixed with `NEXT_PUBLIC_` may enter browser bundles.
- Never log configuration objects or secret values.

`@t3-oss/env-nextjs` is an implementation detail of this outer boundary. Inner layers depend on configuration values or focused ports, not the package.

## Install

```bash
pnpm add @t3-oss/env-nextjs zod
```

Confirm the installed package, Next.js, TypeScript, and Zod versions before copying version-sensitive syntax. The package is ESM-only and requires a TypeScript module resolution mode that understands package exports; `Bundler` is the normal Next.js choice.

## Default: One Validated Module

For most applications, keep one app-owned module:

```typescript
// src/env.ts

import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

const booleanFromString = z
  .enum(["true", "false"])
  .transform((value) => value === "true");

export const env = createEnv({
  server: {
    NODE_ENV: z
      .enum(["development", "test", "production"])
      .default("development"),
    DATABASE_URL: z.string().url(),
    LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),
    STRIPE_SECRET_KEY: z.string().min(1),
    ENABLE_ASYNC_JOBS: booleanFromString.default(false),
  },

  client: {
    NEXT_PUBLIC_APP_URL: z.string().url(),
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: z.string().min(1),
  },

  // Current Next.js releases only require explicit destructuring for values
  // that may be included in the browser bundle.
  experimental__runtimeEnv: {
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY:
      process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY,
  },

  emptyStringAsUndefined: true,
});
```

Why the explicit client map matters: Next.js statically replaces explicitly referenced public variables. A dynamic lookup such as `process.env[name]` is not a safe substitute.

For Next.js versions older than `13.4.4`, T3 Env requires `runtimeEnv` with every server and client variable listed explicitly. Do not mix examples across versions; follow the API supported by the installed dependencies.

Avoid JavaScript truthiness for boolean configuration. `Boolean("false")` is `true`; parse an explicit string enum or use the installed Zod version's equivalent string-boolean parser.

## Use Configuration at Composition

Prefer configuration-shaped factory arguments:

```typescript
// src/lib/shared/infra/db/make-database.ts

export interface DatabaseConfig {
  connectionString: string;
}

export function makeDatabase(config: DatabaseConfig): Database {
  return createPostgresDatabase(config.connectionString);
}
```

```typescript
// src/lib/shared/infra/runtime/database.ts

import { env } from "@/env";
import { makeDatabase } from "@/lib/shared/infra/db/make-database";

// Application-scoped, hot-reload/serverless-safe infrastructure composition.
export const database = makeDatabase({
  connectionString: env.DATABASE_URL,
});
```

```typescript
// src/lib/modules/user/factories/get-user.factory.ts

import { database } from "@/lib/shared/infra/runtime/database";

export function makeGetUserController(): GetUserController {
  const users = new DrizzleUserRepository(database);
  const service = new UserService(users);

  return new GetUserController(service);
}
```

The database adapter receives one required value at application-scoped composition. `UserService` and `GetUserController` never know that the value came from an environment variable or that T3 Env performed validation. Request-scoped resources such as cookies and sessions still belong in request-scoped factories; do not hide them in this application singleton.

## Optional Server/Client Split

A single module never exposes server values to browser code, but its server schema—including variable names—may be present in the client bundle. Split the boundary when secret names are themselves sensitive or when ownership is clearer that way:

```text
src/env/
├── server.ts   # server schema + server runtime values
└── client.ts   # NEXT_PUBLIC_ schema + explicit client runtime map
```

Rules for a split boundary:

- Client modules import only `env/client.ts`.
- Server composition roots import only `env/server.ts`.
- Do not create an isomorphic barrel that re-exports the server env module.
- Keep both modules app-owned; do not place them in `modules/*/shared/contracts/`.

## Validate During the Next.js Build

Import the env module from `next.config.ts` so missing or invalid configuration fails before deployment:

```typescript
// next.config.ts

import "./src/env";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {};

export default nextConfig;
```

If schemas are split, import both modules. When secrets intentionally exist only at container runtime, define and document that deployment contract instead of silently disabling all validation. Validate runtime-only configuration before accepting traffic or processing work.

### Standalone Output

When using `output: "standalone"`, transpile both T3 Env packages:

```typescript
// next.config.ts

import "./src/env";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@t3-oss/env-nextjs", "@t3-oss/env-core"],
};

export default nextConfig;
```

## Files and Deployment

```text
.env.local     local values; ignored by Git
.env.example   committed names and safe placeholders; never real secrets
platform env   production/staging values managed by the deployment platform
```

- Keep `.env.example` synchronized with required variables.
- Scope credentials per environment and grant the least privilege required.
- Rotate secrets without changing inner application APIs.
- Remember that `NEXT_PUBLIC_` values are compiled into browser assets and are not secrets.

## Tests

Import-time validation means a test may fail before assertions when its module graph imports `env`.

- Provide harmless fake values only in the Node/server test setup or test files that require them.
- Set values before dynamically importing an env-sensitive module.
- Do not place server-secret placeholders in global browser/jsdom setup; that can hide an accidental server import.
- Keep a real `next build` or equivalent import-boundary check in CI.
- Never load production credentials into unit tests.

```typescript
// src/test/setup-server-env.ts

process.env.DATABASE_URL ??=
  "postgresql://postgres:postgres@127.0.0.1:54322/postgres";
process.env.STRIPE_SECRET_KEY ??= "sk_test_not-a-secret";
process.env.NEXT_PUBLIC_APP_URL ??= "http://localhost:3000";
process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY ??= "pk_test_not-a-secret";
```

Direct `process.env` access is intentional in this bootstrap file because it prepares the boundary being tested.

## Review Checklist

- [ ] One validated Next.js env boundary owns ordinary `process.env` access.
- [ ] Server variables are under `server` and have no public prefix.
- [ ] Browser variables are under `client`, use `NEXT_PUBLIC_`, and appear in the explicit runtime map.
- [ ] Boolean, numeric, URL, enum, optional, and default semantics are validated deliberately.
- [ ] Runtime factories inject narrow configuration instead of the env object.
- [ ] Shared contracts and inner application layers do not import the env module.
- [ ] Build-time or runtime-start validation matches the deployment's secret availability.
- [ ] Standalone builds transpile the required T3 Env packages.
- [ ] `.env.example` contains safe placeholders and no credentials.
- [ ] Node test setup supplies only the minimum fake values needed for import-time validation.

## References

- [T3 Env: Next.js](https://env.t3.gg/docs/nextjs)
- [T3 Env: Customization](https://env.t3.gg/docs/customization)
- [Next.js: Environment Variables](https://nextjs.org/docs/app/guides/environment-variables)
