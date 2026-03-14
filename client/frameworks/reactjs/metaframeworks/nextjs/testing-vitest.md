# Testing with Vitest

> Concrete Next.js + React test-runner wiring for `Vitest` unit tests. Canonical testing behavior still lives in `client/core/testing.md` and `server/core/testing-service-layer.md`.

## Scope

Use this guide when a Next.js App Router repo wants the standard test layout and behavior from core docs, plus a concrete runner setup for:

- client component tests
- pure domain/helper tests
- hook/query adapter tests
- service-layer unit tests that import Next.js-aware modules

Keep these distinctions clear:

- behavioral testing policy stays in core docs
- framework runner/tooling setup belongs here

This is metaframework-specific because Next.js projects commonly need:

- `server-only` shims during unit tests
- `jsdom` for client component coverage
- setup-time env bootstrapping for import-time env validation

## Recommended Baseline

### Scripts

Add unit test scripts at the package root:

```json
{
  "scripts": {
    "test:unit": "vitest run",
    "test:unit:watch": "vitest"
  }
}
```

### Dev dependencies

Typical Next.js + React + Vitest unit-test stack:

- `vitest`
- `jsdom`
- `@vitejs/plugin-react`
- `vite-tsconfig-paths`
- `@testing-library/react`
- `@testing-library/dom`

Exact versions belong in the consumer repo's `package.json`, not this guide.

### TypeScript

Add Vitest types so test files type-check without per-file global imports:

```json
{
  "compilerOptions": {
    "types": ["vitest/globals", "vitest/jsdom"]
  }
}
```

## Recommended File Layout

```text
vitest.config.mts
src/
  test/
    vitest.setup.ts
    shims/
      server-only.ts
  __tests__/
    ...
```

Test files still follow the core mirror rule:

- `src/<path>/<file>.ts` -> `src/__tests__/<path>/<file>.test.ts`

See:

- `client/core/testing.md`
- `server/core/testing-service-layer.md`

## Vitest Config

Recommended shape for `vitest.config.mts`:

```typescript
import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";
import { defineConfig } from "vitest/config";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  resolve: {
    alias: {
      "server-only": path.resolve(rootDir, "src/test/shims/server-only.ts"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/vitest.setup.ts"],
    include: ["src/__tests__/**/*.test.ts", "src/__tests__/**/*.test.tsx"],
    restoreMocks: true,
    clearMocks: true,
  },
});
```

Key points:

- Use `tsconfigPaths()` so `@/*` aliases resolve in tests.
- Use the React plugin so JSX/TSX matches app transforms.
- Restrict `include` to `src/__tests__/` to preserve the canonical mirror layout.
- Use `jsdom` as the default environment for mixed client + hook coverage.
- Alias `server-only` to a local shim so Next.js server-only markers do not break unit imports.

## Shared Setup File

Use `src/test/vitest.setup.ts` for cross-suite setup:

```typescript
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

process.env.DATABASE_URL ??=
  "postgresql://postgres:postgres@127.0.0.1:54322/postgres";
process.env.SUPABASE_URL ??= "https://example.supabase.co";
process.env.SUPABASE_SECRET_KEY ??= "test-supabase-secret-key";
process.env.NEXT_PUBLIC_SUPABASE_URL ??= "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ??=
  "test-supabase-publishable-key";
process.env.NEXT_PUBLIC_APP_URL ??= "http://localhost:3000";

afterEach(() => {
  cleanup();
});
```

Use this file for:

- Testing Library cleanup
- deterministic test-only env defaults
- future shared mocks/polyfills

## Env Validation in Tests

Many Next.js repos validate env at import time with packages like `@t3-oss/env-nextjs`.
If a module graph touches env during import, unit tests will fail before assertions unless
safe defaults exist.

Rule:

- provide harmless fallback env values in `vitest.setup.ts`
- keep them clearly fake and non-secret
- use only the minimum variables required to import modules deterministically

Do not:

- point tests at production secrets
- depend on real infrastructure in the unit-test loop

## `server-only` Shim

When the repo imports Next.js server-only markers:

```typescript
import "server-only";
```

add a local shim:

```typescript
// src/test/shims/server-only.ts
export {};
```

This is a runner compatibility detail, not a signal that server-only code is safe to execute in the browser.

## First Verification Step

Before adding large test suites, add one mirrored smoke test under `src/__tests__/` and run:

```bash
pnpm test:unit
```

Recommended smoke-test targets:

- a pure helper or domain function
- a small cross-cutting utility
- a redirect/route helper

This verifies:

- config loads
- aliases resolve
- setup file runs
- test discovery matches the documented layout

## What Stays Out of This Guide

Do not move these rules here:

- AAA pattern
- test double definitions
- layer ownership
- `__tests__` mirror policy as the canonical rule
- service-layer test matrix

Those belong in:

- `client/core/testing.md`
- `server/core/testing-service-layer.md`
