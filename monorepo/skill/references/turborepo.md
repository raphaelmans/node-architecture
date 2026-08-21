# Turborepo Slice

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

For a greenfield workspace without package-manager evidence, propose pnpm first only after confirming current compatibility and obtaining approval. Never convert an existing package manager silently.

Do not embed or rely on frozen schemas, fields, flags, CLI catalogs, experimental status, provider instructions, or version-specific workarounds. If current official behavior cannot satisfy a core invariant, block the affected configuration and request direction.

