# 2026-08-24: Configuration Lifecycle Boundaries

## Summary

Separated configuration by consumer and lifecycle so browser builds, private build execution, server runtime, and optional browser runtime delivery validate only the values they actually consume. Executable schemas are authoritative; examples, dependency injection, and monorepo task policy derive from those deployable-owned contracts.

## Core Conventions

- Added `BrowserBuildConfig`, `PrivateBuildConfig`, `ServerRuntimeConfig`, and `BrowserRuntimeConfig` as distinct typed surfaces.
- Kept browser runtime configuration resource-backed and opt-in rather than treating it as a process environment.
- Required schemas to validate declared fields, permit unrelated ambient variables, and return only normalized application configuration.
- Made `.env.example` a checked human- or agent-authored projection rather than a source of truth.
- Scoped validation/failure to the lifecycle and work that consumes each configuration surface.
- Kept external variable names and complete configuration objects outside reusable packages and inward application layers.

## Framework Specializations

- Added standalone React guidance that preserves the installed build tool and activates browser runtime loading only when independent delivery is required.
- Reworked Next.js/T3 Env guidance around lifecycle-specific build/server/browser surfaces instead of universal build-time validation.
- Added NestJS configuration guidance that retains framework-native modules, dependency injection, lifecycle, and tests while supplying portable inward code with narrow normalized options.
- Required exact framework/module/configuration syntax to be resolved from installed versions and current official documentation.

## Monorepo and Turborepo

- Kept every executable environment schema with its deployable application; no root environment file or shared environment package is introduced.
- Separated task environment availability/cache identity from application schema validation.
- Required output-affecting values and loaded environment files to affect the owning task's cache identity while excluding runtime-only values from unrelated build hashes.
- Separated publication/deployment credentials and external side effects from cached artifact production so cache hits cannot suppress requested publication work.
- Preserved ambient variables for non-cacheable framework/tool execution without admitting unknown fields into application dependency injection.

## Portable Skills

Updated client, server, and monorepo references and source mappings with the durable configuration boundaries while keeping version-sensitive vendor APIs outside portable skill knowledge.

Follow-up review also kept mutable browser dependencies such as analytics consent outside `BrowserBuildConfig` and routed generic server configuration requests through the portable `foundations` slice before runtime specialization.
