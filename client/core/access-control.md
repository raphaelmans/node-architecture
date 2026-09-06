# Permission-Aware Client UX

Use when the UI presents role-sensitive actions, organization/branch switching, invitations, or membership management. Client checks improve UX; the server remains authoritative for data access and every operation. Apply the existing [client API flow](./client-api-architecture.md) and [state ownership](./state-management.md).

## Access Contract

Consume an application-owned, validated access result for the current identity, organization, and optional resource scope. Expose only what the feature needs: available actions or named permissions, relevant role labels, and safe scope identity. Do not pass provider session objects, database records, tokens, or a complete membership directory into a generic access context.

Separate loading, available access, and unavailable/error states. A ready result can explicitly deny an action; an absent result cannot grant it. Never treat missing or empty permissions as a request to restore role defaults. Avoid briefly rendering privileged controls before access resolves.

Use resource/action permissions, not numeric role ranks. Role labels may explain the UI but should not independently duplicate the server's authorization logic. Static client role definitions cannot stand in for dynamic organization roles or current resource/state checks.

## Scope and Freshness

The selected workspace/branch is navigation state, not an access credential. Include identity and all result-changing organization/scope values in query/cache identity. On scope change, do not present the old scope's permissions or data as the new scope while loading.

Keep access state with its server-state owner. Clear private access/data on logout or identity change, invalidate affected scope results after membership/role changes, and reconcile after revocation or permission-denied responses. Cancellation, late responses, optimistic updates, and persisted caches must not repopulate another user's or organization's state. A mutation retains its original scope even if navigation changes before it completes.

An authorization failure must stop the action and reconcile affected access state. An unavailable access service shows an appropriate retry/error state without granting access or falsely claiming the user lost membership.

## Interaction and Tests

Choose hide, disable with an accessible explanation, or a denied screen based on the interaction. These are presentation choices, not security controls. Keep invitation/member/role management in cohesive features and share only genuinely reusable access-display primitives.

Test loading without privileged flashes, denial, outage, revocation, logout/login as another user, switching organizations/branches while requests are in flight, and mutation completion after a switch. Ensure real server denial is handled even when the UI previously allowed the action.

Framework mappings: [React](../frameworks/reactjs/access-control.md) and [Next.js](../frameworks/reactjs/metaframeworks/nextjs/access-control.md). Server policy is owned by [capability authorization](../../server/core/authorization.md), not this client convention.
