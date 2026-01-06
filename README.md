# Node.js Architecture Documentation

> Reference architecture for full-stack Node.js applications with Next.js, tRPC, and TypeScript.

## Purpose

This repository contains **architectural patterns and conventions** for building production-ready applications. It serves as a reference for both human developers and LLMs.

> **Important:** This documentation describes patterns and conventions, not specific package versions. Always check `package.json` in your project for actual versions.

## Technology Stack

| Layer   | Technologies                                        |
| ------- | --------------------------------------------------- |
| Server  | Next.js, tRPC, Drizzle ORM, PostgreSQL, Zod, Pino   |
| Client  | Next.js, React, tRPC, TanStack Query, Zod, Tailwind |
| Auth    | Supabase Auth (or custom)                           |
| Storage | Supabase Storage (or custom)                        |

## Documentation Structure

```
node-architecture/
├── README.md                    # This file - entry point
│
├── server/                      # Backend architecture
│   ├── README.md                # Server overview + quick start
│   ├── core/                    # Core patterns
│   │   ├── overview.md          # Architecture summary
│   │   ├── conventions.md       # Layer responsibilities, DI
│   │   ├── error-handling.md    # Error classes, validation
│   │   ├── transaction.md       # Transaction patterns
│   │   ├── logging.md           # Pino configuration
│   │   ├── api-response.md      # Response envelope
│   │   └── id-generation.md     # UUID strategy
│   ├── trpc/                    # tRPC integration
│   │   ├── integration.md       # Router setup, Drizzle
│   │   └── authentication.md    # Auth middleware, RBAC
│   ├── webhook/                 # Webhook handling
│   │   └── architecture.md      # Inbound webhooks, idempotency
│   ├── supabase/                # Supabase integration
│   │   ├── README.md            # Quick reference
│   │   └── integration.md       # Auth, Storage, Database
│   ├── skills/                  # AI-assisted development
│   │   ├── backend-module/      # Creating new modules
│   │   ├── backend-feature/     # Adding features
│   │   ├── backend-auth/        # Auth implementation
│   │   └── backend-webhook/     # Webhook implementation
│   └── references/              # Original detailed docs
│
└── client/                      # Frontend architecture
    ├── README.md                # Client overview + quick start
    ├── core/                    # Core patterns
    │   ├── overview.md          # Architecture summary
    │   ├── conventions.md       # Layer responsibilities
    │   ├── data-fetching.md     # tRPC + TanStack Query
    │   ├── forms.md             # Zod + RHF + StandardForm
    │   ├── state-management.md  # URL state, Zustand
    │   ├── ui-patterns.md       # shadcn/ui, components
    │   ├── error-handling.md    # Toast, boundaries
    │   └── folder-structure.md  # Directory architecture
    └── references/              # Original detailed docs
```

## Project Folder Structure

This architecture expects the following project structure:

```
src/
├── app/                         # Next.js App Router
│   ├── (api)/api/               # API routes
│   │   ├── trpc/[...trpc]/      # tRPC handler
│   │   └── webhooks/            # Webhook endpoints
│   ├── (authenticated)/         # Protected routes
│   └── (guest)/                 # Public routes
│
├── lib/                         # Server code & integrations
│   ├── shared/                  # Shared kernel (server)
│   │   ├── kernel/              # Core types & contracts
│   │   │   ├── context.ts       # RequestContext
│   │   │   ├── transaction.ts   # TransactionManager
│   │   │   ├── errors.ts        # Base error classes
│   │   │   ├── pagination.ts    # Pagination types
│   │   │   └── dtos/            # Cross-module DTOs
│   │   │       └── common.ts    # ImageAssetSchema, etc.
│   │   └── infra/               # Infrastructure
│   │       ├── db/              # Drizzle client, schema
│   │       ├── trpc/            # tRPC setup, middleware
│   │       ├── supabase/        # Supabase client
│   │       └── logger/          # Pino configuration
│   │
│   ├── modules/                 # Backend domain modules
│   │   └── <module>/
│   │       ├── <module>.router.ts   # tRPC router
│   │       ├── dtos/            # Module-specific DTOs
│   │       ├── errors/          # Domain errors
│   │       ├── services/        # Business logic
│   │       ├── repositories/    # Data access
│   │       ├── use-cases/       # Multi-service orchestration
│   │       └── factories/       # Dependency creation
│   │
│   ├── trpc/                    # tRPC client setup
│   │   ├── client.ts            # Client export
│   │   └── query-client.ts      # QueryClient factory
│   │
│   └── env/                     # Environment config
│       └── index.ts             # @t3-oss/env-nextjs
│
├── features/                    # Frontend feature modules
│   └── <feature>/
│       ├── components/          # Feature components
│       ├── hooks.ts             # URL state, custom hooks
│       ├── schemas.ts           # Form schemas
│       └── stores/              # Zustand stores (optional)
│
├── components/                  # Shared UI components
│   ├── ui/                      # shadcn/ui primitives
│   ├── form/                    # StandardForm components
│   └── custom-ui/               # Composed components
│
├── common/                      # App-wide utilities
│   ├── providers/               # React providers
│   ├── app-routes.ts            # Route definitions
│   ├── constants.ts             # Global constants
│   └── hooks.ts                 # Shared hooks
│
└── hooks/                       # Global React hooks
```

## Quick Start

### For Server Development

1. Read [server/README.md](./server/README.md) for overview
2. Follow [server/core/conventions.md](./server/core/conventions.md) for layer patterns
3. Use [server/skills/](./server/skills/) for AI-assisted scaffolding

### For Client Development

1. Read [client/README.md](./client/README.md) for overview
2. Follow [client/core/conventions.md](./client/core/conventions.md) for component patterns
3. Use StandardForm components from [client/core/forms.md](./client/core/forms.md)

## Core Principles

| Principle                        | Description                                  |
| -------------------------------- | -------------------------------------------- |
| **Explicit over implicit**       | No magic, clear dependency flow              |
| **Feature-based organization**   | Co-locate related code by domain             |
| **Type-safe end-to-end**         | Zod schemas shared between client and server |
| **Layered architecture**         | Clear boundaries between layers              |
| **Composition over inheritance** | Small, focused units composed together       |

## Using This Documentation

### For LLMs

When implementing features:

1. Check `package.json` for actual package versions
2. Use this documentation for patterns and conventions
3. Follow the folder structure defined above
4. Reference `skills/` for step-by-step implementation guides

### For Humans

1. Start with the relevant README (server or client)
2. Deep-dive into `core/` docs for specific patterns
3. Check `references/` for detailed implementation examples
