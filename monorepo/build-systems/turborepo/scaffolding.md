# Turborepo Scaffolding

Apply this checklist after the [core scaffolding contract](../../core/scaffolding.md). The detected version and its official documentation determine exact commands and fields.

## Foundation Mapping

Resolve the current official mechanism for:

- package-manager workspace discovery and grouping without ambiguous nested packages;
- a private workspace root with minimal repository tooling;
- root coordination of package-local tasks;
- package graph construction from declared internal dependencies and the lockfile;
- package-specific task behavior close to the affected package;
- correct outputs, environment inputs, persistent development tasks, and cache invalidation;
- affected-package selection in CI;
- optional remote caching and boundary checks.

Do not scaffold a root environment file, application dependencies at the root, manual cross-package build chains, undeclared internal imports, provider credentials, or speculative packages.

## Slice Mapping

For every activated package:

1. Add a unique namespaced package identity and intentional exports.
2. Add internal dependencies to each consumer's manifest using the detected package manager's current supported workspace form.
3. Put executable task logic in the package that owns it.
4. Resolve compilation from actual consumers and declare generated outputs when present.
5. Keep environment files and validation with deployable owners; inject narrow configuration inward.
6. Add package-specific task configuration only for real differences.
7. Verify that dependency and task graphs reflect the intended onion/package direction.

## Environment Mapping

Keep the [core environment contract](../../core/environment.md) authoritative and use current version-matched Turborepo documentation to select the exact mechanism.

- Browser-build and private-build variables that can change generated output participate in the owning build task's cache identity.
- Server-runtime values do not invalidate a build that does not consume them.
- Environment files affect only tasks that actually load them; do not promote app-local files to root-wide inputs.
- Non-cacheable development/execution tasks may admit ambient framework or tooling variables without adding them to application schemas.
- Strict filtering, loose pass-through, and framework inference are task-runner concerns. They never replace app-owned validation or justify an unhashed input to a cacheable build.
- Inspect the resolved task environment and cache summary with the installed tool when verifying the mapping.

## Version-Sensitive Topics

Always retrieve current official sources before deciding:

- configuration schema and field names;
- workspace or language support;
- task dependency and cache-invalidation patterns;
- development/watch orchestration;
- environment modes and framework inference;
- affected filtering and CI comparison bases;
- boundary/tag behavior and experimental status;
- remote-cache providers and authentication;
- pruning or deployment behavior.

Report the installed/selected versions and links used. If current official behavior cannot preserve a core invariant, stop the affected scaffold and request direction rather than embedding an outdated workaround.
