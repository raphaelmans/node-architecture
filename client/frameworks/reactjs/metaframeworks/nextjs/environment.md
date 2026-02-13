# Environment Variables

> Type-safe environment variable management using `@t3-oss/env-nextjs`.

## Overview

Environment variables are managed with `@t3-oss/env-nextjs`, which provides:

- **Type-safe** access to environment variables
- **Runtime validation** with Zod
- **Build-time errors** for missing variables
- **Separation** of server/client variables

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
    ALLOW_PROMOTION_CODES: z.coerce.boolean().default(false),
  },

  // Client-side variables (exposed via NEXT_PUBLIC_ prefix)
  client: {
    NEXT_PUBLIC_APP_URL: z.string().url(),
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: z.string(),
    NEXT_PUBLIC_MIXPANEL_TOKEN: z.string().optional(),
  },

  // Required for client variables in App Router
  experimental__runtimeEnv: {
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY:
      process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY,
    NEXT_PUBLIC_MIXPANEL_TOKEN: process.env.NEXT_PUBLIC_MIXPANEL_TOKEN,
  },
});
```

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
FEATURE_FLAG: z.coerce.boolean().default(false),

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
| Always use `env`            | Never access `process.env` directly  |
| Validate URLs with `.url()` | Catch invalid URLs at build time     |
| Coerce booleans             | Env vars are always strings          |
| Provide defaults            | For optional config                  |
| Keep secrets server-side    | Never use `NEXT_PUBLIC_` for secrets |

## Error Handling

Missing or invalid variables throw at build/start time:

```
Invalid environment variables:
  DATABASE_URL: Required
  STRIPE_SECRET_KEY: Invalid url
```

This prevents deploying with missing configuration.

## Checklist

- [ ] `lib/env/index.ts` created with `createEnv`
- [ ] Server variables defined without prefix
- [ ] Client variables use `NEXT_PUBLIC_` prefix
- [ ] `experimental__runtimeEnv` includes all client variables
- [ ] `.env.local` git-ignored
- [ ] `.env.example` committed with placeholder values
- [ ] All code uses `env` instead of `process.env`
