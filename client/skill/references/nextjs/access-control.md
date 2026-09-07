# Next.js Access-Control Convention

Load for protected SSR/RSC data, access hydration, organization/branch navigation, or permission-aware Next.js features. Read [nextjs](../nextjs.md) and [React access control](../react/access-control.md); this leaf extends React rather than replacing it. Add [routing](routing.md) only when paths or route policies are involved.

## Apply

- Pages/layouts own typed route context, access composition, and safe redirects. Route groups, interception, and hidden layout content are not authoritative guards.
- Authorize protected reads before data reaches HTML, the RSC payload, client props, or hydration. A parent layout cannot protect independent descendant reads or direct endpoint calls, and it may be reused during navigation.
- Application-owned route handlers and Server Actions are public entrypoints: authenticate independently and invoke the protected server application operation. Coordinate with installed `$server` for capability authorization when available; do not bypass it with direct repository calls.
- Keep cookies, headers, SDK sessions, and private configuration at request/server composition. Map a plain actor into the server's controller/service/use-case boundary. Server prefetch may reuse that authorized boundary without an HTTP loopback.
- Pass only safe, scoped application access results to Client Components. Hiding a client component cannot protect data already serialized to it.
- Never put request-dependent clients/access results in process-global singletons. Request-local reuse stays within its lifetime; shared caching requires explicit identity/scope partitioning and revocation behavior.
- Match prefetched access/data to client query identity and scope. Follow the React leaf for scope switching, stale results, logout, revocation, and in-flight mutations. A navigation selection is not membership evidence.

## Verify and Sources

When Better Auth is selected, coordinate its native handler/session/cookie integration with installed `$server` and `runtimes/better-auth` when available. Native auth routes preserve the provider protocol rather than business envelopes. Test cookie propagation for auth-mutating Server Actions; do not require an existing session for login or treat an in-process auth call as automatic browser cookie propagation.

Test direct handler/action invocation, unauthorized descendants, navigation with reused layouts, simultaneous users, and serialized RSC/hydration output—not just redirect behavior or hidden buttons. Verify new-scope loading and post-revocation access.

- [Next.js authentication](https://nextjs.org/docs/app/guides/authentication)
- [Next.js data security](https://nextjs.org/docs/app/guides/data-security)

Resolve current request APIs, authentication integration, caching, and file conventions from the installed Next.js version. Neither this leaf nor the React leaf requires Better Auth installation.
