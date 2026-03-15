# Test Runner Standard: Vitest (Core)

> Framework/library-agnostic test runner configuration. Behavioral testing policy lives in `client/core/testing.md` and `server/core/testing-service-layer.md`.

## Scope

This guide covers the **test runner setup** that applies to any project using Vitest, regardless of framework. It defines:

- config baseline
- script conventions
- setup file patterns
- TypeScript integration
- file discovery rules

Framework-specific additions (React plugin, `server-only` shims, env bootstrapping) belong in framework docs. See Related Docs at the bottom.

## MUST Rules

- Vitest MUST be the unit test runner for both client and server code.
- Every project MUST have `test:unit` and `test:unit:watch` scripts.
- Test files MUST live under `src/__tests__/` following the mirror layout from `client/core/testing.md`.
- A setup file MUST exist at `src/test/vitest.setup.ts` for cross-suite configuration.
- New and modified modules MUST have corresponding tests before merge.

## Scripts

```json
{
  "scripts": {
    "test:unit": "vitest run",
    "test:unit:watch": "vitest"
  }
}
```

Optional feature-scoped scripts are allowed:

```json
{
  "scripts": {
    "test:unit:chat": "vitest run src/__tests__/features/chat"
  }
}
```

## Dev Dependencies

Minimum for any project:

- `vitest`
- `vite-tsconfig-paths`

Framework-specific additions (e.g., `@vitejs/plugin-react`, `jsdom`, `@testing-library/react`) are documented in the relevant framework guide.

Exact versions belong in the consumer repo's `package.json`, not this guide.

## TypeScript Integration

Add Vitest types so test files type-check without per-file imports:

```json
{
  "compilerOptions": {
    "types": ["vitest/globals"]
  }
}
```

Framework-specific type additions (e.g., `vitest/jsdom`) belong in framework docs.

## Config Baseline

Recommended shape for `vitest.config.mts`:

```typescript
import tsconfigPaths from "vite-tsconfig-paths";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [tsconfigPaths()],
  test: {
    globals: true,
    setupFiles: ["./src/test/vitest.setup.ts"],
    include: ["src/__tests__/**/*.test.ts", "src/__tests__/**/*.test.tsx"],
    restoreMocks: true,
    clearMocks: true,
  },
});
```

Key points:

- `tsconfigPaths()` resolves path aliases (e.g., `@/*`) in tests.
- `globals: true` enables `describe`, `it`, `expect` without imports.
- `include` is restricted to `src/__tests__/` to enforce the canonical mirror layout.
- `restoreMocks` and `clearMocks` prevent mock leakage between tests.

Framework-specific plugins (React, jsdom environment, alias overrides) are added in framework docs.

## Setup File

`src/test/vitest.setup.ts` is the cross-suite entry point:

```typescript
import { afterEach } from "vitest";

// Add framework-specific cleanup here (e.g., Testing Library cleanup)

afterEach(() => {
  // shared teardown
});
```

Use this file for:

- test-only environment variable defaults (harmless, non-secret values)
- shared mock/polyfill setup
- framework-specific cleanup hooks (manual cleanup is optional when relying on Vitest globals + Testing Library auto-cleanup)

Do not:

- point tests at production secrets or real infrastructure
- add test-specific business logic here

## File Layout

```text
vitest.config.mts
src/
  test/
    vitest.setup.ts
    shims/              # framework-specific shims (optional)
  __tests__/
    features/
    common/
    lib/
    ...
```

Test files follow the core mirror rule:

- `src/<path>/<file>.ts` → `src/__tests__/<path>/<file>.test.ts`

See `client/core/testing.md` for the full mirror layout and naming conventions.

## First Verification Step

Before adding large test suites, add one mirrored smoke test and run:

```bash
pnpm test:unit
```

Recommended smoke-test targets:

- a pure helper or domain function
- a small cross-cutting utility

This verifies:

- config loads
- aliases resolve
- setup file runs
- test discovery matches the documented layout

## What Stays Out of This Guide

These belong in behavioral testing docs, not runner configuration:

- AAA pattern
- test double definitions
- layer ownership and test matrix
- `__tests__` mirror policy as the canonical rule
- TDD red-green-refactor workflow

See:

- `client/core/testing.md`
- `server/core/testing-service-layer.md`

## Related Docs

- `client/core/testing.md` — behavioral testing standard (client)
- `server/core/testing-service-layer.md` — behavioral testing standard (server)
- `client/frameworks/reactjs/metaframeworks/nextjs/testing-vitest.md` — Next.js-specific runner additions (React plugin, `server-only` shim, jsdom, env bootstrapping)
