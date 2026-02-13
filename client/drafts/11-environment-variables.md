# Environment Variables

This guide covers type-safe environment variable management using `@t3-oss/env-nextjs`.

---

## Dependencies

```json
{
  "@t3-oss/env-nextjs": "^0.11.1",
  "zod": "^3.25.8"
}
```

---

## Overview

`@t3-oss/env-nextjs` provides:

- **Type-safe** environment variables
- **Runtime validation** with Zod
- **Build-time errors** for missing variables
- **Separation** of server/client variables

---

## Setup

```typescript
// src/lib/env/index.ts
import { z } from 'zod'
import { createEnv } from '@t3-oss/env-nextjs'

export const env = createEnv({
  // Server-side variables (never exposed to client)
  server: {
    DATABASE_URL: z.string(),
    STRIPE_SECRET_KEY: z.string(),
    STRIPE_WEBHOOK_SECRET: z.string(),

    // Optional with defaults
    LANGFUSE_BASE_URL: z.string().url().optional(),
    ALLOW_PROMOTION_CODES: z.coerce.boolean().default(false),

    // With default values
    STRIPE_TRIAL_CHARGE_PRICE_ID: z.string().default('price_xxx'),
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
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY,
    NEXT_PUBLIC_MIXPANEL_TOKEN: process.env.NEXT_PUBLIC_MIXPANEL_TOKEN,
  },
})
```

---

## Usage

```typescript
// Server-side (API routes, server components, tRPC)
import { env } from '@/lib/env'

const stripe = new Stripe(env.STRIPE_SECRET_KEY)
const dbUrl = env.DATABASE_URL

// Client-side (client components)
import { env } from '@/lib/env'

const appUrl = env.NEXT_PUBLIC_APP_URL
const stripeKey = env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
```

---

## Conventions

### Naming

| Type   | Prefix         | Example                             |
| ------ | -------------- | ----------------------------------- |
| Server | None           | `DATABASE_URL`, `STRIPE_SECRET_KEY` |
| Client | `NEXT_PUBLIC_` | `NEXT_PUBLIC_APP_URL`               |

### Categories

Group related variables:

```typescript
server: {
  // Database
  DATABASE_URL: z.string(),

  // Authentication
  SUPABASE_URL: z.string(),
  SUPABASE_ANON_KEY: z.string(),
  SUPABASE_SERVICE_ROLE_KEY: z.string(),

  // Payments
  STRIPE_SECRET_KEY: z.string(),
  STRIPE_WEBHOOK_SECRET: z.string(),

  // External APIs
  MUX_ACCESS_TOKEN_ID: z.string(),
  MUX_SECRET_KEY: z.string(),
  RESEND_API_KEY: z.string(),

  // AI/ML
  XAI_API_KEY: z.string(),
  GOOGLE_GENERATIVE_AI_API_KEY: z.string(),

  // Observability
  LANGFUSE_PUBLIC_KEY: z.string(),
  LANGFUSE_SECRET_KEY: z.string(),
},
```

### Validation Patterns

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

// Regex validation
WEBHOOK_SECRET: z.string().startsWith('whsec_'),
```

---

## File Structure

```
src/lib/env/
└── index.ts          # Single env configuration file

# Alternative for complex setups:
src/lib/env/
├── index.ts          # Re-exports
├── server.ts         # Server variables
└── client.ts         # Client variables
```

---

## .env Files

```bash
# .env.local (git-ignored, local development)
DATABASE_URL="postgresql://..."
STRIPE_SECRET_KEY="sk_test_..."
NEXT_PUBLIC_APP_URL="http://localhost:3000"

# .env.example (committed, template)
DATABASE_URL="postgresql://user:pass@host:5432/db"
STRIPE_SECRET_KEY="sk_test_xxx"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

---

## Best Practices

1. **Always use `env`** - Never access `process.env` directly

   ```typescript
   // Good
   import { env } from '@/lib/env'
   const key = env.API_KEY

   // Bad
   const key = process.env.API_KEY
   ```

2. **Validate URLs** - Use `.url()` for URL variables

   ```typescript
   BASE_URL: z.string().url(),
   ```

3. **Coerce booleans** - Environment variables are always strings

   ```typescript
   ENABLE_FEATURE: z.coerce.boolean().default(false),
   ```

4. **Provide defaults** for optional config

   ```typescript
   PORT: z.coerce.number().default(3000),
   ```

5. **Keep secrets server-side** - Never use `NEXT_PUBLIC_` for secrets

---

## Error Handling

Missing or invalid variables will throw at build/start time:

```
❌ Invalid environment variables:
  DATABASE_URL: Required
  STRIPE_SECRET_KEY: Invalid url
```

This prevents deploying with missing configuration.

---

## Integration with Scripts

For scripts outside Next.js (e.g., database seeds):

```typescript
// src/scripts/seed.ts
import 'dotenv/config' // Load .env first
import { env } from '@/lib/env'

// Now env is available
console.log(env.DATABASE_URL)
```

Or use `dotenvx` (as in package.json):

```bash
dotenvx run --env-file=.env.local -- tsx src/scripts/seed.ts
```
