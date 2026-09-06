# React Access-Control Convention

Apply [permission-aware client UX](../../core/access-control.md) first. This mapping applies to standalone React and to Client Components inside Next.js; it does not require an authentication or authorization library.

## Composition

- Keep access reads and membership/role mutations behind the feature API interface, implementation, and factory. SDK calls and provider errors stay in transport/integration adapters.
- Load access through feature-owned query hooks. A feature coordinator handles loading/error/scope changes and supplies a focused access snapshot to children, optionally through context when several descendants consume it.
- An access provider distributes already resolved state; it does not fetch bootstrap entities, construct SDK clients, or expose a runtime container. A pure permission predicate may be shared with the server when it is provider-independent, but its client result is never authoritative.
- Keep guards such as a permission gate render-only. They consume an app-facing permission result and presentation props; they do not infer authorization from a role name or fetch resources themselves.

Use the repository's established hook naming and state/query integration rather than introducing parallel auth-state infrastructure. Do not install Better Auth or a policy engine merely to render a gate. If Better Auth is present, adapt its supported permission behavior behind the feature boundary and obtain server-backed results for dynamic roles and resource-specific rules.

## Scope Lifecycle

Keep query keys and invalidation in hooks/sync modules, not TSX. Partition results by identity, organization, and branch/resource scope. Disable cross-scope previous-data placeholders for private access and data; late requests must remain associated with their original scope. Clean up relevant subscriptions on identity/scope change and reconcile after membership changes.

Use a loading or unavailable state until the new scope has a valid result. Controls may be hidden or disabled with an accessible reason. A stale allow result never justifies suppressing a server denial, and a UI context must not expose another organization's cached state during a switch.

## Verification and Sources

Test pure predicates with permission fixtures, query/API boundaries with mapped results, and gates with loading/denied/allowed/unavailable states. Exercise rapid scope switching, in-flight mutations, logout, revocation, and subscription cleanup with the actual query integration.

- [React context](https://react.dev/learn/passing-data-deeply-with-context)
- [TanStack Query keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)
- [Better Auth Organization](https://better-auth.com/docs/plugins/organization), only for the selected integration

Official installed-version docs own hook/context and query-library syntax. This guide owns component, API, and state boundaries.
