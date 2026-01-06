# Folder Structure

> Directory architecture and organization patterns.

## High-Level Structure

```
src/
├── app/                 # Next.js App Router (routes)
├── common/              # App-wide shared utilities
├── components/          # Shared UI components
├── features/            # Feature modules
├── hooks/               # Global React hooks
└── lib/                 # Core logic & integrations
```

## Detailed Structure

```
src/
├── app/                                    # Next.js App Router
│   ├── (api)/                              # API route group
│   │   └── api/
│   │       ├── trpc/[...trpc]/
│   │       │   └── route.ts                # tRPC handler
│   │       └── webhooks/
│   │           └── stripe/route.ts
│   │
│   ├── (authenticated)/                    # Protected routes
│   │   ├── layout.tsx                      # Auth check, sidebar
│   │   ├── dashboard/
│   │   │   ├── page.tsx
│   │   │   ├── loading.tsx
│   │   │   └── error.tsx
│   │   ├── profile/
│   │   │   └── page.tsx
│   │   └── settings/
│   │       └── page.tsx
│   │
│   ├── (guest)/                            # Public routes
│   │   ├── layout.tsx
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── signup/
│   │       └── page.tsx
│   │
│   ├── layout.tsx                          # Root layout (providers)
│   ├── page.tsx                            # Home page
│   ├── error.tsx                           # Global error boundary
│   └── globals.css                         # Global styles
│
├── common/                                 # App-wide shared code
│   ├── providers/                          # React context providers
│   │   ├── trpc-provider.tsx
│   │   ├── theme-provider.tsx
│   │   └── index.tsx
│   ├── app-routes.ts                       # Route path definitions
│   ├── constants.ts                        # Global constants
│   ├── hooks.ts                            # Shared custom hooks
│   ├── types.ts                            # Shared TypeScript types
│   └── utils.ts                            # Utility functions
│
├── components/                             # Shared UI components
│   ├── ui/                                 # shadcn/ui primitives
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── form.tsx
│   │   ├── dialog.tsx
│   │   ├── card.tsx
│   │   ├── skeleton.tsx
│   │   ├── toast.tsx
│   │   └── ...
│   ├── form/                               # StandardForm components
│   │   ├── StandardFormProvider.tsx
│   │   ├── StandardFormError.tsx
│   │   ├── fields/
│   │   │   ├── StandardFormInput.tsx
│   │   │   ├── StandardFormSelect.tsx
│   │   │   ├── StandardFormTextarea.tsx
│   │   │   └── StandardFormField.tsx
│   │   ├── context.tsx
│   │   ├── types.ts
│   │   └── index.ts
│   ├── custom-ui/                          # Composed business components
│   │   ├── data-table.tsx
│   │   ├── page-header.tsx
│   │   └── ...
│   └── common/                             # Other shared components
│       └── StandardSearch.tsx
│
├── features/                               # Feature modules
│   ├── auth/
│   │   ├── components/
│   │   │   ├── auth-login-form.tsx
│   │   │   └── auth-register-form.tsx
│   │   ├── hooks.ts
│   │   └── schemas.ts
│   │
│   ├── profile/
│   │   ├── components/
│   │   │   ├── profile-form.tsx            # Business component
│   │   │   └── profile-form-fields.tsx     # Presentation components
│   │   ├── hooks.ts                        # URL state, custom hooks
│   │   └── schemas.ts                      # Zod schemas
│   │
│   └── <feature>/
│       ├── components/
│       │   ├── <feature>-form.tsx
│       │   ├── <feature>-form-fields.tsx
│       │   ├── <feature>-list.tsx
│       │   └── <feature>-card.tsx
│       ├── stores/                         # Zustand stores (if needed)
│       │   └── <name>-store.ts
│       ├── hooks.ts
│       └── schemas.ts
│
├── hooks/                                  # Global React hooks
│   ├── use-mobile.tsx
│   └── use-toast.ts
│
└── lib/                                    # Server code & integrations
    ├── shared/                             # Shared kernel (server)
    │   ├── kernel/                         # Core types & contracts
    │   │   ├── context.ts                  # RequestContext
    │   │   ├── transaction.ts              # TransactionManager
    │   │   ├── errors.ts                   # Base error classes
    │   │   ├── pagination.ts               # Pagination types
    │   │   └── dtos/                       # Cross-module DTOs
    │   │       └── common.ts               # ImageAssetSchema, etc.
    │   └── infra/                          # Infrastructure
    │       ├── db/                         # Drizzle client, schema
    │       ├── trpc/                       # tRPC setup, middleware
    │       └── logger/                     # Pino configuration
    │
    ├── modules/                            # Backend domain modules
    │   └── <module>/
    │       ├── <module>.router.ts          # tRPC router
    │       ├── dtos/                       # Module-specific DTOs
    │       ├── services/                   # Business logic
    │       └── repositories/               # Data access
    │
    ├── trpc/                               # tRPC client setup
    │   ├── client.ts                       # Client export
    │   ├── query-client.ts                 # QueryClient factory
    │   └── transformers.ts                 # Custom transformers
    │
    ├── env/                                # Environment config
    │   └── index.ts                        # @t3-oss/env-nextjs
    │
    └── utils.ts                            # Utility functions
```

## Route Groups

| Group             | Purpose         | Auth Required |
| ----------------- | --------------- | ------------- |
| `(api)`           | API endpoints   | Varies        |
| `(authenticated)` | Protected pages | Yes           |
| `(guest)`         | Public pages    | No            |

## Feature Module Structure

Each feature follows this pattern:

```
src/features/<feature>/
├── components/
│   ├── <feature>-form.tsx           # Business component (data fetching)
│   ├── <feature>-form-fields.tsx    # Presentation components
│   ├── <feature>-list.tsx           # List view
│   ├── <feature>-card.tsx           # Card component
│   └── <feature>-skeleton.tsx       # Loading skeleton
├── stores/                          # Zustand stores (optional)
│   └── <name>-store.ts
├── hooks.ts                         # URL state, feature hooks
└── schemas.ts                       # Zod form schemas
```

## Naming Conventions

### Files

| Type              | Convention             | Example             |
| ----------------- | ---------------------- | ------------------- |
| Page              | `page.tsx`             | `page.tsx`          |
| Layout            | `layout.tsx`           | `layout.tsx`        |
| Loading           | `loading.tsx`          | `loading.tsx`       |
| Error             | `error.tsx`            | `error.tsx`         |
| Feature component | `<feature>-<type>.tsx` | `profile-form.tsx`  |
| UI primitive      | `<component>.tsx`      | `button.tsx`        |
| Hook              | `use-<name>.ts`        | `use-toast.ts`      |
| Store             | `<name>-store.ts`      | `customer-store.ts` |
| Schema            | `schemas.ts`           | `schemas.ts`        |
| DTO               | `<entity>-dtos.ts`     | `profile-dtos.ts`   |

### Components

| Type               | Convention              | Example                 |
| ------------------ | ----------------------- | ----------------------- |
| Page component     | `<Name>Page`            | `ProfilePage`           |
| Feature component  | `<Feature><Type>`       | `ProfileForm`           |
| Presentation field | `<Feature><Field>Field` | `ProfileFirstNameField` |
| UI primitive       | `<Name>`                | `Button`                |

## Import Aliases

```typescript
// tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

```typescript
// Usage
import { Button } from "@/components/ui/button";
import { trpc } from "@/lib/trpc/client";
import { profileFormSchema } from "@/features/profile/schemas";
import appRoutes from "@/common/app-routes";
```

## Import Order

```typescript
// 1. React/Next.js
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

// 2. External libraries
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

// 3. Internal - components
import { Button } from "@/components/ui/button";
import { StandardFormProvider } from "@/components/form";

// 4. Internal - common/lib
import { trpc } from "@/lib/trpc/client";
import appRoutes from "@/common/app-routes";

// 5. Internal - feature (relative)
import { ProfileFirstNameField } from "./profile-form-fields";
import { profileFormSchema, type ProfileFormHandler } from "../schemas";
```

## Decision Guide

| Question                        | Location                         |
| ------------------------------- | -------------------------------- |
| Is it a page/route?             | `app/(group)/<route>/page.tsx`   |
| Is it a layout?                 | `app/(group)/layout.tsx`         |
| Is it a UI primitive?           | `components/ui/`                 |
| Is it a StandardForm component? | `components/form/`               |
| Is it a composed component?     | `components/custom-ui/`          |
| Is it feature-specific?         | `features/<feature>/components/` |
| Is it a form schema?            | `features/<feature>/schemas.ts`  |
| Is it a URL state hook?         | `features/<feature>/hooks.ts`    |
| Is it a Zustand store?          | `features/<feature>/stores/`     |
| Is it shared across features?   | `common/`                        |
| Is it a cross-module DTO?       | `lib/shared/kernel/dtos/`        |
| Is it a module-specific DTO?    | `lib/modules/<module>/dtos/`     |
| Is it a global hook?            | `hooks/`                         |

## Colocation Rules

1. **Feature-specific code** → `features/<feature>/`
2. **Shared UI** → `components/`
3. **App-wide utilities** → `common/`
4. **Cross-module DTOs** → `lib/shared/kernel/dtos/`
5. **Module-specific server code** → `lib/modules/<module>/`
6. **Third-party integrations** → `lib/`

## Checklist for New Features

- [ ] Create `src/features/<feature>/` folder
- [ ] Add `schemas.ts` with Zod schemas
- [ ] Add `hooks.ts` for URL state (if needed)
- [ ] Create components in `components/` folder
- [ ] Add routes to `app-routes.ts`
- [ ] Create page in `app/(authenticated)/<feature>/page.tsx`
