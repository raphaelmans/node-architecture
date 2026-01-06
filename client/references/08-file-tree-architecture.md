# File Tree Architecture

This guide covers the directory structure and organization patterns.

> **Important:** The `src/lib/**` directory structure is **reference only** and most likely to change based on your backend architecture, ORM choice, and API layer preferences. Focus on the patterns rather than exact file locations.

---

## High-Level Structure

```
src/
├── app/                 # Next.js App Router (routes)          - Stable
├── common/              # App-wide shared utilities            - Stable
├── components/          # Shared UI components                 - Stable
├── features/            # Feature modules                      - Stable
├── hooks/               # Global React hooks                   - Stable
├── lib/                 # Core logic & integrations            - Reference only
├── mastra/              # AI/Agent workflows (domain-specific) - Project-specific
└── scripts/             # CLI scripts                          - Project-specific
```

---

## App Directory (Next.js App Router)

```
src/app/
├── (api)/                       # API route group
│   └── api/
│       ├── trpc/[...trpc]/      # tRPC handler
│       │   └── route.ts
│       └── webhooks/            # Webhook endpoints
│           └── stripe/route.ts
│
├── (authenticated)/             # Protected routes (require auth)
│   ├── layout.tsx               # Auth check, sidebar
│   ├── dashboard/
│   │   └── page.tsx
│   ├── profile/
│   │   └── page.tsx
│   └── settings/
│       └── page.tsx
│
├── (guest)/                     # Public routes
│   ├── layout.tsx
│   ├── login/
│   │   └── page.tsx
│   └── signup/
│       └── page.tsx
│
├── layout.tsx                   # Root layout (providers)
├── page.tsx                     # Home page
└── globals.css                  # Global styles
```

### Route Groups

| Group             | Purpose         | Auth     |
| ----------------- | --------------- | -------- |
| `(api)`           | API endpoints   | Varies   |
| `(authenticated)` | Protected pages | Required |
| `(guest)`         | Public pages    | None     |

---

## Common Directory

```
src/common/
├── providers/              # React context providers
│   ├── trpc-provider.tsx   # tRPC + React Query
│   ├── theme-provider.tsx  # Theme context
│   └── index.tsx           # Provider composition
│
├── icons/                  # Custom icon components
│   └── logo.tsx
│
├── integrations/           # Third-party integrations
│   └── analytics.ts
│
├── app-routes.ts           # Route path constants
├── constants.ts            # Global constants
├── hooks.ts                # Shared custom hooks
├── types.ts                # Shared TypeScript types
└── utils.ts                # Utility functions
```

### app-routes.ts Pattern

```typescript
// src/common/app-routes.ts
const appRoutes = {
  home: '/',
  auth: {
    login: '/login',
    signup: '/signup',
    forgotPassword: '/forgot-password',
  },
  dashboard: '/dashboard',
  profile: {
    base: '/profile',
    edit: '/profile/edit',
  },
  settings: {
    base: '/settings',
    billing: '/settings/billing',
  },
} as const

export default appRoutes
```

---

## Components Directory

```
src/components/
├── ui/                    # shadcn/ui primitives
│   ├── button.tsx
│   ├── input.tsx
│   ├── form.tsx
│   ├── dialog.tsx
│   ├── select.tsx
│   ├── card.tsx
│   ├── skeleton.tsx
│   └── ...
│
└── custom-ui/             # Composed business components
    ├── data-table.tsx
    ├── page-header.tsx
    └── ...
```

### Component Naming

| Type              | Convention   | Example            |
| ----------------- | ------------ | ------------------ |
| UI Primitive      | lowercase    | `button.tsx`       |
| Custom UI         | kebab-case   | `data-table.tsx`   |
| Feature Component | prefix-kebab | `profile-form.tsx` |

---

## Features Directory

```
src/features/
├── auth/
│   ├── components/
│   │   ├── auth-login-form.tsx
│   │   ├── auth-register-form.tsx
│   │   └── auth-forgot-password-form.tsx
│   ├── hooks.ts
│   └── schemas.ts
│
├── profile/
│   ├── components/
│   │   ├── profile-form.tsx           # Business component
│   │   └── profile-form-fields.tsx    # Presentation components
│   ├── hooks.ts
│   └── schemas.ts
│
├── company/
│   ├── components/
│   │   ├── company-form.tsx
│   │   ├── company-form-fields.tsx
│   │   └── company-list.tsx
│   ├── hooks.ts
│   └── schemas.ts
│
└── <feature>/
    ├── components/
    │   ├── <feature>-form.tsx
    │   ├── <feature>-form-fields.tsx
    │   ├── <feature>-list.tsx
    │   └── <feature>-card.tsx
    ├── hooks.ts
    └── schemas.ts
```

### Feature Structure Rules

1. **components/** - All React components for the feature
2. **hooks.ts** - Custom hooks (URL state, feature logic)
3. **schemas.ts** - Zod schemas for forms

### Component Naming Convention

```
<feature>-<type>.tsx

Examples:
- profile-form.tsx        # Main form (business)
- profile-form-fields.tsx # Field components (presentation)
- profile-list.tsx        # List view
- profile-card.tsx        # Card component
- profile-skeleton.tsx    # Loading skeleton
```

---

## Lib Directory

> **Reference Only:** This structure is specific to the current project's backend architecture (Drizzle + Supabase + tRPC). Adapt based on your ORM, database, and API layer choices. The key concepts (DTOs, schemas, external integrations) are transferable.

```
src/lib/                                   # REFERENCE ONLY - likely to change
├── core/                          # Business logic
│   ├── dtos/                      # Data Transfer Objects
│   │   ├── profile-dtos.ts
│   │   ├── company-dtos.ts
│   │   └── index.ts
│   │
│   ├── schemas/                   # Database entity schemas
│   │   ├── profile.ts
│   │   ├── company.ts
│   │   └── index.ts
│   │
│   ├── controllers/               # API controllers
│   │   └── index.ts
│   │
│   ├── services/                  # Business services
│   │   └── index.ts
│   │
│   ├── handlers/                  # Request handlers
│   │   └── index.ts
│   │
│   ├── common-schemas.ts          # Shared schema primitives
│   └── constants.ts               # Business constants
│
├── extern/                        # External integrations
│   ├── db/                        # Database
│   │   ├── schemas.ts             # Drizzle schemas
│   │   ├── supabase/              # Supabase client
│   │   └── scripts/               # DB scripts
│   │
│   └── <service>/                 # Other services
│       └── client.ts
│
├── trpc/                          # tRPC setup
│   ├── init.ts                    # Server initialization
│   ├── client.ts                  # Client export
│   ├── query-client.ts            # QueryClient factory
│   ├── transformers.ts            # Custom transformers
│   └── routers/                   # tRPC routers
│       ├── profile.ts
│       └── index.ts
│
├── env/                           # Environment config
│   ├── client.ts                  # Client env vars
│   └── server.ts                  # Server env vars
│
├── config/                        # App configuration
│   └── site.ts
│
├── adapters/                      # Data adapters
│   └── index.ts
│
└── utils.ts                       # Server utilities
```

---

## Hooks Directory

```
src/hooks/
├── use-mobile.tsx        # Mobile detection
└── use-toast.ts          # Toast notifications
```

Global hooks that are used across multiple features. Feature-specific hooks go in `features/<feature>/hooks.ts`.

---

## Import Patterns

### Absolute Imports

```typescript
// tsconfig.json paths
{
  "paths": {
    "@/*": ["./src/*"]
  }
}

// Usage
import { Button } from '@/components/ui/button'
import { trpc } from '@/lib/trpc/client'
import { profileFormSchema } from '@/features/profile/schemas'
import appRoutes from '@/common/app-routes'
```

### Import Order

```typescript
// 1. React/Next
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

// 2. External libraries
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

// 3. Internal - components
import { Button } from '@/components/ui/button'
import { Form } from '@/components/ui/form'

// 4. Internal - lib/common
import { trpc } from '@/lib/trpc/client'
import { cn } from '@/lib/utils'
import appRoutes from '@/common/app-routes'

// 5. Internal - feature
import { ProfileFirstNameField } from './profile-form-fields'
import { profileFormSchema, type ProfileFormHandler } from '../schemas'
```

---

## File Naming Conventions

| Type       | Convention | Example            |
| ---------- | ---------- | ------------------ |
| Components | kebab-case | `profile-form.tsx` |
| Hooks      | kebab-case | `use-toast.ts`     |
| Schemas    | kebab-case | `profile-dtos.ts`  |
| Utils      | kebab-case | `query-client.ts`  |
| Types      | kebab-case | `types.ts`         |
| Constants  | kebab-case | `constants.ts`     |

---

## Decision Guide

| Question                      | Location                         |
| ----------------------------- | -------------------------------- |
| Is it a page/route?           | `app/`                           |
| Is it a shared UI component?  | `components/ui/`                 |
| Is it feature-specific UI?    | `features/<feature>/components/` |
| Is it a form schema?          | `features/<feature>/schemas.ts`  |
| Is it an API contract (DTO)?  | `lib/core/dtos/`                 |
| Is it shared across features? | `common/`                        |
| Is it server-side logic?      | `lib/core/`                      |
| Is it external integration?   | `lib/extern/`                    |
