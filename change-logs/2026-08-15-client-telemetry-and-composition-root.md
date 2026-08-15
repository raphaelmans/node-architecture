# 2026-08-15: Client Telemetry, Composition Root, and Field Guide

## Summary

Standardized client operational logging, product analytics, and dependency-heavy infrastructure construction across the framework-agnostic core and React/Next.js layers. Added a standalone interactive client field guide with a concrete create-user vertical slice.

## Documentation Surface

Added:

- `client/core/composition-root.md`
- `client/core/product-analytics.md`
- `assets/client-architecture-guide.html`

Aligned the surrounding client core, React, Next.js, Ky, tRPC, diagrams, onboarding, testing, and downstream consumer artifacts with the same ownership and lifecycle rules.

## Core Decisions

- `AppLogger` and `ProductAnalytics` are separate application ports; no combined telemetry service.
- Operational records follow an OpenTelemetry-shaped contract with typed primitive attributes, stable event names, severity, correlation, and adapter-owned context.
- `debug` is the local browser sink and namespace selector, not the application logging contract.
- Sentry is an optional filtered production sink for unhandled exceptions and selected operational records.
- Product analytics uses a typed event registry, consent/identity lifecycle, non-blocking delivery, and vendor adapters.
- Transport failures are logged once by `clientApi`; `featureApi` owns contract/mapping diagnostics; error boundaries own unhandled exceptions.
- Successful mutation/workflow owners emit typed product events after meaningful success.
- Telemetry fields do not enter business DTOs or ordinary method parameters.

## Factories and Lifetimes

- Added named factories for dependency-heavy client infrastructure: `createAppLogger`, `createProductAnalytics`, `createClientApi`, and `create<Feature>Api`.
- Added one client composition root that owns provider construction, dependency order, and lifecycle.
- Browser infrastructure is application-scoped.
- SSR infrastructure is request-scoped only when it captures request/user context.
- Consumers receive specific ports, never the complete runtime container.
- Feature modules no longer own hidden singleton construction; runtime indirection modules expose composition-root-owned accessors.
- React components, Zod schemas, pure helpers, and simple hooks do not get unnecessary factories.

## Framework Alignment

- React mutation/workflow hooks own success analytics when the action is reusable.
- Business components own only route/UI-specific occurrences.
- Next.js Ky and tRPC guidance constructs transports in the composition root and owns correlation/logging at transport adapters.
- QueryClient defaults and components do not duplicate lower-boundary operational reports.

## Testing

- Tests call the same factories with logger sinks, analytics adapters, transports, spies, fakes, or no-op implementations.
- Added explicit adapter tests for enrichment, redaction, sampling, consent, identity, and non-fatal delivery failure.
- Added lifetime tests for application-scoped browser composition and isolated request-scoped SSR composition.

## Interactive Artifact

- Added `assets/client-architecture-guide.html` as the standalone interactive companion to the client documentation.
- Added eight focused sections covering the system, client layers, data flows, TanStack Query server state, telemetry, runtime composition, testing, and folder structure.
- Added interactive query-read, create-mutation, optimistic-write, and contract-failure flow explorers.
- Aligned query-key examples with the documented direct-tRPC, wrapped-tRPC, and non-tRPC strategies.
- Added an expandable, near-compilable create-user vertical slice connecting:

  1. `UserCreateForm`
  2. `useCreateUser`
  3. `UserApi` and `createUserApi`
  4. Ky-backed `createClientApi`
  5. the browser composition root

- The slice shows success-only `user_created` analytics, detail-cache seeding, list invalidation, feature-owned schema diagnostics, transport-owned logging, and application-scoped dependency construction.
- Telemetry occurrence context stays outside `CreateUserInput` and other business DTOs.
- Added the guide to the root, client, and downstream consumer indexes.

## Validation

- Passed `git diff --check`.
- Parsed the standalone HTML and verified unique IDs, control targets, and local documentation links.
- Checked embedded JavaScript syntax with Node.js.
- Exercised section navigation, flow selection, disclosure toggling, and keyboard expansion in Chromium.
- Visually reviewed desktop and mobile layouts.
- Confirmed no document-level horizontal overflow at 1440px and 390px widths.
- Confirmed no browser console or runtime errors during the walkthrough checks.

## Notes

- Documentation-only change.
- Existing client API and query-adapter flow remains canonical; telemetry does not introduce a controller layer.
