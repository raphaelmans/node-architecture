# Environment Variables

The boolean examples target Zod 4. Projects pinned to Zod 3 should use an explicit string enum/transform rather than JavaScript truthiness-based boolean coercion.

> Type-safe environment variable management using `@t3-oss/env-nextjs`.

Reference: [T3 Env Next.js documentation](https://env.t3.gg/docs/nextjs).

## Overview

Environment variables are managed with `@t3-oss/env-nextjs`, which provides:

- **Type-safe** access to environment variables
- **Runtime validation** with Zod
- **Build-time errors** for missing variables
- **Separation** of server/client variables

## Compatibility Baseline

`@t3-oss/env-nextjs` is ESM-only and requires TypeScript 5 or newer. Use a TypeScript module resolution mode that understands package `exports`; `Bundler` is the recommended default for Next.js applications.

The examples in this guide use Zod because shared runtime validation is the repository standard. The package also accepts other validators implementing Standard Schema, but do not mix validation libraries within one application without a concrete migration or integration requirement.

## Setup

```typescript
// lib/env/index.ts

import { z } from "zod";
import { createEnv } from "@t3-oss/env-nextjs";

export const env = createEnv({
  // Server-side variables (never exposed to client)
  server: {
    DATABASE_URL: z.string(),
    STRIPE_SECRET_KEY: z.string(),
    STRIPE_WEBHOOK_SECRET: z.string(),

    // Optional with defaults
    LANGFUSE_BASE_URL: z.string().url().optional(),
    ALLOW_PROMOTION_CODES: z.stringbool().default(false),
  },

  // Client-side variables (exposed via NEXT_PUBLIC_ prefix)
  client: {
    NEXT_PUBLIC_APP_URL: z.string().url(),
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: z.string(),
    NEXT_PUBLIC_MIXPANEL_TOKEN: z.string().optional(),
  },

  // Next.js >= 13.4.4: enumerate client variables only.
  // Server variables are read from process.env by the package.
  experimental__runtimeEnv: {
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY:
      process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY,
    NEXT_PUBLIC_MIXPANEL_TOKEN: process.env.NEXT_PUBLIC_MIXPANEL_TOKEN,
  },
});
```

## Runtime Environment Wiring by Next.js Version

Next.js only includes environment variables in a browser bundle when the access can be statically analyzed. This is why client variables must be written out explicitly instead of passing an opaque environment object.

| Next.js version | Configuration | Required values |
| --- | --- | --- |
| `>= 13.4.4` | `experimental__runtimeEnv` | Explicitly enumerate every client variable |
| `< 13.4.4` | `runtimeEnv` | Explicitly enumerate every server and client variable |

For older Next.js applications:

```typescript
export const env = createEnv({
  server: {
    DATABASE_URL: z.string(),
  },
  client: {
    NEXT_PUBLIC_APP_URL: z.string().url(),
  },
  runtimeEnv: {
    DATABASE_URL: process.env.DATABASE_URL,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  },
});
```

Missing `runtimeEnv` entries should remain type errors. Do not bypass strict runtime wiring with dynamic property access.

## Usage

```typescript
import { env } from "@/lib/env";

// Server-side (API routes, server components, tRPC)
const stripe = new Stripe(env.STRIPE_SECRET_KEY);
const dbUrl = env.DATABASE_URL;

// Client-side (client components)
const appUrl = env.NEXT_PUBLIC_APP_URL;
```

## Naming Conventions

| Type   | Prefix         | Example                             |
| ------ | -------------- | ----------------------------------- |
| Server | None           | `DATABASE_URL`, `STRIPE_SECRET_KEY` |
| Client | `NEXT_PUBLIC_` | `NEXT_PUBLIC_APP_URL`               |

## Validation Patterns

```typescript
// Required string
API_KEY: z.string(),

// Required URL
BASE_URL: z.string().url(),

// Optional
OPTIONAL_KEY: z.string().optional(),

// Optional with default
FEATURE_FLAG: z.stringbool().default(false),

// Numeric
PORT: z.coerce.number().default(3000),

// Enum
NODE_ENV: z.enum(['development', 'production', 'test']),
```

## File Structure

```
lib/env/
└── index.ts          # Single env configuration file
```

Keep one module by default because it provides the best autocomplete and import ergonomics. A unified module does not expose server values to the browser, but its server schema—and therefore server variable names—may be present in the client bundle.

If the names themselves are sensitive, split the schemas:

```text
lib/env/
├── client.ts         # client schema + explicit NEXT_PUBLIC_* runtimeEnv
└── server.ts         # server schema + server-only import boundary
```

Client Components may import only `client.ts`. Route handlers, Server Components, server actions, and other server-only modules may import `server.ts`. Do not create a barrel that imports the server schema into client-reachable code.

Wire split schemas independently:

```typescript
// lib/env/client.ts
export const clientEnv = createEnv({
  client: {
    NEXT_PUBLIC_APP_URL: z.string().url(),
  },
  runtimeEnv: {
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  },
});

// lib/env/server.ts — Next.js >= 13.4.4
export const serverEnv = createEnv({
  server: {
    DATABASE_URL: z.string(),
  },
  experimental__runtimeEnv: process.env,
});
```

Do not substitute an empty object for the server runtime environment. On older Next.js versions, replace the server module's `experimental__runtimeEnv` with strict `runtimeEnv` entries for every declared server variable.

## Validate During the Build

Import the environment module from the Next.js configuration so invalid or missing variables fail before the application build proceeds. Import every split schema when using separate client and server modules.

For Next.js 16 and newer, import the TypeScript module directly:

```typescript
// next.config.ts
import "./src/lib/env/index";

import type { NextConfig } from "next";

const nextConfig: NextConfig = {};

export default nextConfig;
```

For pre-16 projects whose configuration remains CommonJS, load the TypeScript module with `jiti`:

```javascript
// next.config.js
const { createJiti } = require("jiti");

const jiti = createJiti(__filename);

/** @type {import("next").NextConfig} */
const nextConfig = {};

module.exports = async () => {
  await jiti.import("./src/lib/env/index.ts");
  return nextConfig;
};
```

`next.config.js` is CommonJS, so use `require` and `module.exports`. Next.js supports an async configuration function from version 12.1 onward, which lets this example use Jiti's asynchronous import API and complete validation before returning the configuration. If the project already uses ESM configuration, use `next.config.mjs` with `import`, top-level `await`, and `export default` instead. Do not copy the ESM form into `next.config.js`. For an older Next.js version without async config support, resolve a compatible strategy from that version's official documentation or block the config change.

This explicit import is the mechanism that guarantees build-time validation. Runtime imports still protect application startup and execution paths. Verify config-module and Jiti behavior against the installed versions before editing; see the official [Next.js configuration documentation](https://nextjs.org/docs/app/api-reference/config/next-config-js) and [Jiti usage documentation](https://github.com/unjs/jiti#programmatic).

## Standalone Output

When `output: "standalone"` is enabled, transpile the T3 Env packages so the standalone artifact includes compatible output:

```typescript
// next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@t3-oss/env-nextjs", "@t3-oss/env-core"],
};

export default nextConfig;
```

## .env Files

```bash
# .env.local (git-ignored, local development)
DATABASE_URL="postgresql://..."
STRIPE_SECRET_KEY="sk_test_..."
NEXT_PUBLIC_APP_URL="http://localhost:3000"

# .env.example (committed, template for team)
DATABASE_URL="postgresql://user:pass@host:5432/db"
STRIPE_SECRET_KEY="sk_test_xxx"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

## Best Practices

| Practice                    | Reason                               |
| --------------------------- | ------------------------------------ |
| Application code uses `env` | Keep direct `process.env` access inside the env module and test/runtime setup boundaries |
| Validate URLs with `.url()` | Catch invalid URLs at build time     |
| Parse boolean strings explicitly | `"false"` must become `false`, not JavaScript-truthy `true` |
| Provide defaults            | For optional config                  |
| Keep secrets server-side    | Never use `NEXT_PUBLIC_` for secrets |
| Validate from Next.js config | Fail the build before application modules are evaluated |
| Keep runtime keys explicit | Preserve Next.js static bundling and T3 Env type checks |

## Error Handling

Missing or invalid variables throw at build/start time:

```
Invalid environment variables:
  DATABASE_URL: Required
  STRIPE_SECRET_KEY: Required
```

This prevents deploying with missing configuration.

## Checklist

- [ ] `lib/env/index.ts` created with `createEnv`
- [ ] Server variables defined without prefix
- [ ] Client variables use `NEXT_PUBLIC_` prefix
- [ ] Runtime wiring matches the installed Next.js version
- [ ] `experimental__runtimeEnv` includes all client variables on Next.js `>= 13.4.4`
- [ ] `runtimeEnv` includes all server and client variables on older Next.js versions
- [ ] Next.js config imports the environment module for build-time validation
- [ ] Standalone builds transpile `@t3-oss/env-nextjs` and `@t3-oss/env-core`
- [ ] Sensitive variable names use separate client and server schema modules
- [ ] Split server schemas use `process.env` on modern Next.js, not an empty runtime object
- [ ] `.env.local` git-ignored
- [ ] `.env.example` committed with placeholder values
- [ ] Application code uses `env`; only env/bootstrap boundaries access `process.env`
