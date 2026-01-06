# Dev Tools Configuration

This guide covers development tools setup for debugging and performance analysis.

---

## React Query DevTools

### Installation

Already included with `@tanstack/react-query`:

```json
{
  "@tanstack/react-query-devtools": "^5.62.16"
}
```

### Setup

```typescript
// src/common/providers/trpc-provider.tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

export function TRPCProvider({ children }: { children: React.ReactNode }) {
  return (
    <trpc.Provider client={trpcClient} queryClient={queryClient}>
      <QueryClientProvider client={queryClient}>
        {children}
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </trpc.Provider>
  )
}
```

### Features

- View all queries and mutations
- Inspect query state (loading, error, data)
- Manually invalidate/refetch queries
- Time travel through query history
- View cache contents

### Usage Tips

| Action         | Purpose                    |
| -------------- | -------------------------- |
| Click query    | View details, data, timing |
| Refetch button | Manually trigger refetch   |
| Invalidate     | Mark query as stale        |
| Remove         | Clear from cache           |
| Query filters  | Find specific queries      |

---

## React Scan (Render Performance)

### Installation

```bash
pnpm add react-scan --save-dev
```

### Setup

```typescript
// src/app/layout.tsx or _app.tsx
if (process.env.NODE_ENV === 'development') {
  import('react-scan').then(({ scan }) => {
    scan({
      enabled: true,
      log: true, // Console logging
    })
  })
}
```

### Alternative: Script Tag

```typescript
// src/app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html>
      <head>
        {process.env.NODE_ENV === 'development' && (
          <script
            src="https://unpkg.com/react-scan/dist/auto.global.js"
            async
          />
        )}
      </head>
      <body>{children}</body>
    </html>
  )
}
```

### Features

- Highlights re-rendering components
- Shows render count
- Identifies unnecessary renders
- Performance metrics

---

## React Grab (Future)

Placeholder for react-grab integration when added:

```typescript
// Future setup location
// src/common/providers/dev-tools-provider.tsx

export function DevToolsProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      // react-grab setup here
    }
  }, [])

  return <>{children}</>
}
```

---

## ESLint + Prettier

### ESLint Configuration

```json
// .eslintrc.json
{
  "extends": ["next/core-web-vitals", "prettier"],
  "plugins": ["@typescript-eslint", "import"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "warn",
    "import/order": [
      "error",
      {
        "groups": ["builtin", "external", "internal", "parent", "sibling", "index"],
        "newlines-between": "never"
      }
    ]
  }
}
```

### Prettier Configuration

```json
// .prettierrc
{
  "semi": false,
  "singleQuote": true,
  "jsxSingleQuote": true,
  "trailingComma": "es5",
  "tabWidth": 2,
  "printWidth": 100,
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

---

## Husky + lint-staged

### Setup

```json
// package.json
{
  "scripts": {
    "prepare": "husky"
  }
}
```

```bash
# .husky/pre-commit
pnpm lint-staged
```

```javascript
// .lintstagedrc.js
module.exports = {
  '*.{js,jsx,ts,tsx}': ['eslint --fix', 'prettier --write'],
  '*.{json,md}': ['prettier --write'],
}
```

---

## TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

---

## Environment Variables

```typescript
// src/lib/env/client.ts
import { createEnv } from '@t3-oss/env-nextjs'
import { z } from 'zod'

export const env = createEnv({
  client: {
    NEXT_PUBLIC_APP_URL: z.string().url(),
  },
  runtimeEnv: {
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  },
})
```

---

## Recommended VS Code Extensions

```json
// .vscode/extensions.json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "prisma.prisma",
    "ms-vscode.vscode-typescript-next"
  ]
}
```

---

## Dev Tools Checklist

- [ ] React Query DevTools (dev only)
- [ ] React Scan or similar render tool
- [ ] ESLint with TypeScript rules
- [ ] Prettier with Tailwind plugin
- [ ] Husky pre-commit hooks
- [ ] lint-staged for staged files
- [ ] TypeScript strict mode
- [ ] VS Code extensions configured
