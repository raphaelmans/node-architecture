# Testing with Vitest — Next.js Additions

> Next.js-specific runner additions layered on top of the core Vitest standard.
> Core runner setup: `client/core/testing-vitest.md`.
> Behavioral testing policy: `client/core/testing.md` and `server/core/testing-service-layer.md`.

## Scope

This guide covers **only the Next.js-specific additions** to the core Vitest runner. Read `client/core/testing-vitest.md` first for the baseline config, scripts, and setup conventions.

Next.js projects commonly need these additions:

- `server-only` shims during unit tests
- React plugin for JSX/TSX transforms
- `jsdom` environment for client component coverage
- setup-time env bootstrapping for import-time env validation (`@t3-oss/env-nextjs`)

## Additional Dev Dependencies

On top of the core dependencies (`vitest`, `vite-tsconfig-paths`), Next.js + React projects add:

- `jsdom`
- `@vitejs/plugin-react`
- `@testing-library/react`
- `@testing-library/dom`

Exact versions belong in the consumer repo's `package.json`, not this guide.

### Additional TypeScript Types

Add jsdom types alongside the core `vitest/globals`:

```json
{
  "compilerOptions": {
    "types": ["vitest/globals", "vitest/jsdom"]
  }
}
```

## Additional File Layout

Next.js projects extend the core layout with a `server-only` shim:

```text
src/
  test/
    shims/
      server-only.ts    # Next.js-specific shim
    setup-server-env.ts # imported only by server/env-sensitive tests
```

## Config Additions

Extend the core config from `client/core/testing-vitest.md` with Next.js + React specifics:

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
    environment: "node",
    globals: true,
    setupFiles: ["./src/test/vitest.setup.ts"],
    include: ["src/__tests__/**/*.test.ts", "src/__tests__/**/*.test.tsx"],
    restoreMocks: true,
    clearMocks: true,
  },
});
```

Next.js-specific additions on top of the core baseline:

- `react()` plugin so JSX/TSX matches app transforms.
- `environment: "node"` as the safe default for server modules and pure units.
- `server-only` alias so Next.js server-only markers do not break unit imports.

Opt individual component/hook test files into a DOM environment:

```typescript
// @vitest-environment jsdom

import { render } from "@testing-library/react";
```

For a large suite, use separate named Vitest projects for Node and jsdom instead of a global jsdom environment. This prevents server-oriented tests from accidentally depending on browser globals.

## Setup File Additions

Extend the core setup file (`src/test/vitest.setup.ts`) with Next.js specifics:

```typescript
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  if (typeof document !== "undefined") cleanup();
});
```

Next.js-specific additions:

- Testing Library cleanup (`@testing-library/react`) when not relying on auto-cleanup via Vitest globals
- DOM cleanup guarded so Node-environment tests remain valid

## Env Validation in Tests

Many Next.js repos validate env at import time with packages like `@t3-oss/env-nextjs`.
If a module graph touches env during import, unit tests will fail before assertions unless
safe defaults exist.

Rule:

- provide harmless fallback env values only to the Node/server test project or files whose import graph validates them
- keep them clearly fake and non-secret
- use only the minimum variables required to import modules deterministically

```typescript
// src/test/setup-server-env.ts
process.env.DATABASE_URL ??=
  "postgresql://postgres:postgres@127.0.0.1:54322/postgres";
process.env.NEXT_PUBLIC_APP_URL ??= "http://localhost:3000";
```

Import that setup before dynamically importing an env-sensitive server module, or register it only in a named Node test project. Do not put server-secret placeholders in the global jsdom/client setup; doing so can conceal an accidental server import in client code.

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

This is a runner compatibility detail, not a signal that server-only code is safe to execute in the browser. Keep an independent Next.js build or import-boundary check in CI so the shim cannot conceal a server-only import that leaked into a client entry point.

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

- Runner baseline config, scripts, setup conventions → `client/core/testing-vitest.md`
- AAA pattern, test doubles, mirror layout → `client/core/testing.md`
- Layer ownership, service-layer test matrix → `server/core/testing-service-layer.md`
