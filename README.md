# Node.js Architecture Documentation

> Reference architecture for full-stack applications with a core-first client/server documentation model.

## Purpose

This repository contains **architectural patterns and conventions** for building production-ready applications. It serves as a reference for both human developers and LLMs.

> **Important:** This documentation describes patterns and conventions, not specific package versions. Always check `package.json` in your project for actual versions.

## Contributing

For contribution standards (including adding new client frameworks like Vue/Svelte or new server runtimes/languages like Go), see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Technology Stack

| Layer   | Technologies                                        |
| ------- | --------------------------------------------------- |
| Server  | Next.js, tRPC, Drizzle ORM, PostgreSQL, Zod, Pino   |
| Client  | Next.js/React, TanStack Query, Zod, Tailwind, adapter-based API layer |
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
│   │   ├── id-generation.md     # UUID strategy
│   │   └── webhook/             # Agnostic webhook architecture + testing
│   ├── runtime/                 # Runtime-specific docs
│   │   └── nodejs/
│   │       ├── libraries/
│   │       │   ├── trpc/        # tRPC integration + auth
│   │       │   └── supabase/    # Supabase integration docs
│   │       └── metaframeworks/
│   │           ├── nextjs/      # Next.js route handlers
│   │           ├── express/     # Placeholder
│   │           └── nestjs/      # Placeholder
│   └── drafts/                  # Original detailed docs (legacy, non-canonical)
│
├── skills/                      # Shared AI-assisted development skills
│   ├── server/
│   │   ├── backend-module/
│   │   ├── backend-feature/
│   │   ├── backend-auth/
│   │   └── backend-webhook/
│   └── client/
│
└── client/                      # Frontend architecture
    ├── README.md                # Client overview + quick start
    ├── core/                    # Core patterns
    │   ├── onboarding.md        # New project + contributor startup checklist
    │   ├── overview.md          # Core index
    │   ├── architecture.md      # Agnostic principles
    │   ├── conventions.md       # Layer responsibilities
    │   ├── client-api-architecture.md # clientApi -> featureApi -> query adapter
    │   ├── validation-zod.md    # Zod boundary rules
    │   ├── server-state-tanstack-query.md # TanStack Query patterns
    │   ├── domain-logic.md      # Shared vs client-only domain transformations
    │   ├── query-keys.md        # Query key conventions (Query Key Factory)
    │   ├── logging.md           # Client logging conventions (debug)
    │   ├── state-management.md  # Conceptual state decision guide
    │   ├── error-handling.md    # Error taxonomy and rules
    │   └── folder-structure.md  # Directory architecture
    ├── frameworks/              # Framework-specific docs
    │   └── reactjs/             # React-specific docs
    │       └── metaframeworks/nextjs/ # Next.js-specific docs
    └── drafts/                  # Original detailed docs (drafts)
```

## Project Folder Structure

This architecture expects a core-aligned project structure.
Treat this as a contract-oriented reference, not an exact required tree.

```
src/
├── <routes>/                    # Metaframework-owned routes (Next.js: app/)
├── features/                    # Client feature modules (business unit)
│   └── <feature>/
│       ├── components/          # view + fields (business/presentation split)
│       ├── api.ts               # featureApi
│       ├── hooks.ts             # query adapter
│       ├── schemas.ts           # zod schemas + derived types
│       ├── domain.ts            # deterministic domain rules (optional)
│       └── helpers.ts           # pure transforms (optional)
├── components/                  # Shared UI components
├── common/                      # Cross-feature contracts/utilities
│   ├── query-keys/              # Query key contracts
│   ├── errors/                  # AppError contract + adapters
│   ├── toast/                   # Toast facade + adapters
│   └── logging/                 # Logger facade + adapters
└── lib/                         # Server code and server/client shared module logic
    └── modules/<module>/shared/ # Shared domain transforms and contracts
```

## Quick Start

### For Server Development

1. Read [server/README.md](./server/README.md) for overview
2. Follow [server/core/conventions.md](./server/core/conventions.md) for layer patterns
3. Use [skills/server/](./skills/server/) for AI-assisted scaffolding

### For Client Development

1. Read [client/README.md](./client/README.md) for overview
2. Start with [client/core/onboarding.md](./client/core/onboarding.md)
3. Follow [client/core/conventions.md](./client/core/conventions.md) and [client/core/client-api-architecture.md](./client/core/client-api-architecture.md)
4. Apply framework details from [client/frameworks/reactjs/README.md](./client/frameworks/reactjs/README.md) and [client/frameworks/reactjs/metaframeworks/nextjs/README.md](./client/frameworks/reactjs/metaframeworks/nextjs/README.md)

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
3. Check `drafts/` for detailed legacy examples (non-canonical)
