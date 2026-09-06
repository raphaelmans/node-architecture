# Turborepo Slice

For named local origins and concurrent worktrees, coordinate with installed `$development` when available. Retain package-owned startup and existing root orchestration. Check task environment availability at the actual origin-injection boundary; do not add development-proxy variables to application schemas.

Use this slice only when Turborepo is detected or requested. It is a thin execution router, not a configuration reference.

## Resolve Before Acting

Detect:

- Turborepo and package-manager versions;
- lockfile and workspace declarations;
- root/package configuration and scripts;
- package graph, exports, and internal dependencies;
- task outputs, environment inputs, development tasks, CI, and cache state.

Retrieve the official Turborepo documentation applicable to that evidence. Use official release notes or source when versioned docs do not resolve behavior.

## Map Durable Outcomes

Select the current official mechanism that preserves:

- deployable apps as graph endpoints;
- internal packages consumed through manifests and exports;
- package-local task logic with root coordination;
- dependency builds before dependents;
- parallel but cache-correct checks;
- real outputs for file-producing tasks;
- explicit persistent development tasks;
- app/task-owned environment inputs;
- affected CI selection;
- optional remote caching with external credentials;
- package and onion boundary verification.

For environment mapping, keep application schemas and task policy separate. Use the current official mechanism so output-affecting browser/private values and loaded environment files affect the owning task's cache identity; exclude runtime-only values from unrelated build hashes. Treat publication/deployment as a separate non-cacheable task, or equivalent side-effect execution, whose credentials are available without hashing the cached build and whose requested work still runs after a build cache hit. Non-cacheable development/execution tasks may admit ambient framework/tool variables without adding them to app schemas. Framework inference or loose/pass-through behavior never substitutes for executable validation or makes an unhashed output-affecting input safe.

For a greenfield workspace without package-manager evidence, propose pnpm first only after confirming current compatibility and obtaining approval. Never convert an existing package manager silently.

Do not embed or rely on frozen schemas, fields, flags, CLI catalogs, experimental status, provider instructions, or version-specific workarounds. If current official behavior cannot satisfy a core invariant, block the affected configuration and request direction.

## Official Implementation References

- [Turborepo documentation](https://turborepo.com/docs)
- [pnpm workspaces](https://pnpm.io/workspaces)

Turborepo is the task orchestration and cache specialization, while pnpm is the greenfield package-manager reference. Preserve the desired task-graph, ownership, and reproducibility outcomes and their selection criteria; derive exact schemas and commands from the installed versions and current official documentation.
