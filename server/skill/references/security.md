# Security Slice

Use this slice for authentication, sessions, authorization, cookies, trusted origins and redirects, Supabase keys and RLS, secret handling, rate-limit identity, and Next.js security configuration.

## Authentication and Authorization

Authentication establishes an actor. Authorization decides whether that actor may perform the requested action.

- Transport middleware may enforce a coarse authenticated-session or role gate.
- Services enforce reusable domain permissions and resource ownership.
- Use cases enforce workflow-level policy spanning multiple domains.
- Repositories never own authorization policy.

Convert transport/session data to a plain `Actor` before calling a controller. Do not pass framework context or provider user objects inward.

## Session Boundary

Use a module-owned `SessionResolver` port in shared transport context. Return `null` only for genuine anonymous or expired sessions. Translate provider and database outages to typed gateway/unavailable errors; never silently downgrade them to anonymous access.

Use HTTP-only, secure production cookies with an intentional SameSite policy. Rotate/create sessions at authentication, support revocation, and keep password hashing or token verification behind focused infrastructure.

## Supabase Keys and RLS

- Use the publishable key for browser and request-scoped user/session clients.
- Use the secret key only in narrowly named server-only privileged factories.
- Never expose a secret/service-role key to the client; it bypasses RLS.
- Treat legacy `anon` and `service_role` values as migration compatibility, not the default for new code.
- Enable and test RLS for browser/user-scoped access. Do not assume a publishable key protects data without policy.

Keep privileged clients out of ordinary factories so code review can identify bypass-RLS paths immediately.

Declare secret keys only in the validated server environment schema. Declare browser-safe provider values explicitly under the public client schema and require the framework's public prefix. Runtime factories import validated values and pass only the key needed by each provider adapter; neither application code nor generic context objects receive the env module.

## Redirects and Request Trust

Build OAuth, PKCE, and other security-sensitive redirects from a validated application origin. Accept only validated relative next paths and reject protocol-relative paths. Resolve the sanitized path with the URL parser and compare the final origin so backslash normalization cannot bypass prefix checks. OAuth exchange failures must be logged through the central error policy and redirected to a safe same-origin error destination. Do not derive trusted hosts from forwarded headers unless a configured trusted-proxy boundary has validated them.

Accept incoming request IDs or client IPs only through a documented trusted ingress policy. Otherwise generate the request ID and use the authenticated actor or server-observed address for rate-limit identity.

## Provider Error Safety

Branch on stable provider error codes, never localized message text. Translate provider errors at the adapter into typed application errors, preserve the original error as an internal cause, and expose only safe public messages.

## Next.js and HTTP Baseline

- Configure CSP deliberately; prefer nonces/hashes over broad unsafe directives.
- Set HSTS only in environments that are permanently HTTPS.
- Add MIME sniffing, frame, referrer, and permissions policies appropriate to the application.
- Validate rewrite/redirect destinations and environment-gate development-only routes.
- Restrict image and asset origins.
- Validate FormData size, count, type, and filename/path boundaries before provider calls.

## Review Checklist

- Authentication failures and provider outages remain distinguishable.
- Authorization is enforced at the reusable domain/workflow boundary.
- Actor data is plain and provider-independent inside application code.
- Cookie, origin, redirect, and proxy trust policies are explicit.
- Publishable and privileged Supabase clients are separate.
- RLS and privileged bypass paths are tested.
- Secrets, credentials, cookies, and raw tokens cannot reach logs or public errors.
- Secret/public environment exposure is validated centrally and configuration is injected narrowly.
- Security headers and upload limits match the deployed runtime.

## Derivation Sources

Derived from core errors/rate limits, tRPC authentication, Supabase auth/integration, and Next.js security/FormData guidance. Exact paths and fingerprints are maintained outside the portable skill package.
