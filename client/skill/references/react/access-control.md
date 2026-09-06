# React Access-Control Convention

Load for permission gates, organization/branch switching, or membership/role-sensitive UX in standalone React or Next.js Client Components. Read [react](../react.md) and add [data-flow](../data-flow.md) when implementing access queries or mutations.

## Apply

- Consume a validated application access result scoped to identity, organization, and optional resource scope. Expose only needed actions/permissions and safe labels, not SDK sessions, tokens, database rows, or a whole membership directory.
- Keep access reads/mutations behind feature API interfaces, implementations, and factories. Query hooks own fetching and keys; the feature coordinator owns loading/error/scope UX.
- A focused context may distribute already resolved state to descendants. Providers do not fetch bootstrap entities or construct SDKs. Gates render from app-facing decisions and never infer authority from numeric ranks or administrative labels.
- Separate loading, ready (allowed or denied), and unavailable states. Missing/empty grants never enable controls or restore role defaults. Avoid privileged-content flashes.
- Partition query/cache identity by user and every result-changing organization/scope value. Never use old-scope access/data as a new-scope placeholder. Keep late responses and mutation results associated with their original scope.
- Clear private state on logout/identity change, invalidate affected access after grant changes, and clean up subscriptions during scope changes. Reconcile after server denial without disguising outages as lost membership.
- Choose hide, accessible disabled explanations, or a denied screen intentionally. Client gates are UX only; the server rechecks every operation and authorizes all returned data.
- Do not install a policy engine or Better Auth just to render gates. If selected, adapt its supported behavior behind feature boundaries; static role checks cannot represent dynamic roles or current resource-state authorization.

Keep permission/cache mechanics in feature hooks or sync modules, not TSX. Shared pure predicates may support UI consistency but cannot replace current server authorization.

## Verify and Sources

Test permission fixtures, API result/error mapping, loading/allowed/denied/unavailable rendering, no privileged flash, revocation, logout/login, rapid scope changes, late requests, and mutations completing after navigation.

- [React context](https://react.dev/learn/passing-data-deeply-with-context)
- [TanStack Query keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)
- [Better Auth Organization](https://better-auth.com/docs/plugins/organization), only for the selected integration

Use matching official docs for concrete hooks and SDK behavior. Add [Next.js access control](../nextjs/access-control.md) only for its request/rendering boundaries.
