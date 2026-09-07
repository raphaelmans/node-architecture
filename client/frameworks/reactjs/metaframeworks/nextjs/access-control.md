# Next.js Access-Control Convention

Apply [React access control](../../access-control.md) for Client Components and the [client access contract](../../../../core/access-control.md) for state and UX. This leaf adds server-rendering and request boundaries; it does not replace the React leaf.

## Server and Client Responsibilities

Pages and layouts resolve typed route context, coordinate safe redirects, and compose features. Use the [routing convention](./routing-convention.md) when constructing paths or policies. Route groups, interception, and hidden layout content are not authoritative access checks.

Authorize every protected server read before its data enters rendered HTML, the RSC payload, client props, or hydration state. A layout check is insufficient for descendant reads, direct endpoint access, or navigation that reuses a layout. Application-owned route handlers and Server Actions are public entrypoints and must independently authenticate and reach the protected application operation.

When Better Auth is selected, follow [its integration convention](../../../../../server/runtime/nodejs/libraries/better-auth/README.md) for native auth handler mounting, session verification, and cookie propagation from auth-mutating Server Actions. These provider-managed routes retain their native protocol; they are not wrapped in business response envelopes. Do not make login require an existing session or assume an in-process auth call updates browser cookies automatically.

Keep Next.js cookies, headers, and session SDKs at request composition. Map identity into a plain actor and use the server's controller/service/use-case boundaries. Server prefetch can call the authorized application boundary directly; do not add an HTTP loopback merely to reuse checks, and do not bypass policy through direct repository access.

Pass only a safe application access result to Client Components. Keep server-only adapters and private configuration unreachable from browser imports. A client permission gate cannot retroactively protect data that was already serialized.

## Request and Cache Isolation

Never store user/session/scope-dependent clients or access results in process-global singletons. Reuse request-local work only within its valid lifetime. If a shared cache is explicitly needed, define identity/scope partitioning and revocation behavior before enabling it; do not inherit a framework's cache default as authorization policy.

Bind server-prefetched access and private data to the same identity and scope used by the client query keys. On organization/branch change, follow the React leaf's cancellation, stale-data, invalidation, and subscription rules. Client navigation cannot establish membership.

## Verification and Official Sources

Test direct route-handler/action calls, unauthorized nested pages, layout reuse during navigation, parallel requests from different users, and RSC/hydration payloads for unauthorized data. Verify scope switching and post-revocation behavior, not only redirects or hidden buttons.

- [Next.js authentication](https://nextjs.org/docs/app/guides/authentication)
- [Next.js data security](https://nextjs.org/docs/app/guides/data-security)
- [Server capability authorization](../../../../../server/core/authorization.md)

Resolve framework-specific authentication integration, request APIs, caching behavior, and file conventions from the target Next.js version's official docs. Better Auth is a documented optional integration, not a dependency of this leaf.
