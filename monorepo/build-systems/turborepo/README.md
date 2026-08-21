# Turborepo Specialization

Turborepo is the first supported implementation of the monorepo contracts. This guide intentionally does not duplicate its configuration reference.

## Authority Boundary

This repository owns:

- application versus internal-package ownership;
- package activation and dependency direction;
- package-local task ownership and shared task vocabulary;
- environment ownership, scaffolding atomicity, and verification outcomes.

The official Turborepo documentation owns current configuration fields, schemas, CLI behavior, cache mechanisms, workspace support, boundary features, development orchestration, and CI integration.

Start with the [official Turborepo documentation](https://turborepo.com/docs), then select material applicable to the detected or selected version. Use official release notes or source when the versioned documentation does not resolve a behavior.

## Required Resolution

Before configuring Turborepo:

1. Detect the installed version, package manager and version, lockfile, workspace declarations, root and package configurations, package scripts, outputs, environment inputs, CI, and cache state.
2. Retrieve official guidance matching that evidence.
3. Map [core package boundaries](../../core/package-boundaries.md) and the [scaffolding contract](../../core/scaffolding.md) to the current supported mechanisms.
4. Show any dependency installation, initialization, migration, remote-cache connection, or CI-provider change for approval.
5. Verify the resulting package and task graphs with the installed tool.

For a greenfield workspace with no package-manager evidence, this repository recommends proposing pnpm first. Confirm current compatibility, show the exact version and install/initialization consequences, and obtain approval; never convert an existing package manager silently.

## Durable Outcomes

Regardless of version-specific syntax:

- deployables remain package-graph endpoints;
- shared code is consumed through declared internal packages and exports;
- package tasks contain task logic and the root coordinates them;
- dependency builds precede dependents;
- parallel checks invalidate when dependency sources change;
- file-producing tasks cache their real outputs;
- development servers are explicit persistent tasks and never bypass the dependency graph;
- environment inputs are declared by the packages/tasks they affect;
- remote caching is optional and credentials remain external;
- package and onion boundaries are both verified.

See [Turborepo Scaffolding](./scaffolding.md) for the execution checklist.
