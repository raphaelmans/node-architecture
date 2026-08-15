# Supabase Realtime Adapter (Next.js)

> Provider-specific implementation of the contracts in `client/core/realtime.md`.

## Adapter Boundary

Keep Supabase construction in the client composition root and inject the narrow client dependency into a realtime adapter. The adapter owns channel names, PostgREST filters, provider status mapping, and removal of the channel.

```typescript
export function createReservationRealtimeClient(deps: {
  supabase: SupabaseClient;
  logger: AppLogger;
}): RealtimeClient<ReservationEventRow, ReservationEventFilter> {
  return new SupabaseReservationRealtimeClient(deps);
}
```

Inside the adapter:

- subscribe to the configured schema/table/event set;
- treat the received row as `unknown` and validate it with a provider-private schema;
- map Supabase statuses into the core `RealtimeConnectionState` union;
- return an idempotent `unsubscribe()` that removes the channel; and
- emit connection diagnostics once through the injected `AppLogger`.

The feature realtime API maps the validated row into a domain event. React hooks never receive a Postgres row or Supabase channel.

## Event Scope

`INSERT`-only subscriptions are appropriate only when the server intentionally exposes an append-only event log. Entity tables that rely on `UPDATE` or `DELETE` require a different event contract and cache reducer. Document that decision per feature rather than treating INSERT-only behavior as a global client rule.

## Server-Side Setup

Publication, replica identity, grants, and row-level-security policies are server/database responsibilities and must be delivered through reviewed migrations.

Typical Supabase concerns include:

1. adding the intended table to the realtime publication;
2. selecting the required replica identity for the subscribed event/filter behavior;
3. granting only the minimum required privileges; and
4. defining RLS policies that authorize each subscriber's rows.

Do not apply one-time production SQL from client setup scripts. Keep the exact migration and security review in the server/database project.

## Testing

- Unit-test the adapter with a fake Supabase channel/client.
- Test malformed provider payload rejection and provider-to-core status mapping.
- Test that unsubscribe removes the channel once.
- Keep live Supabase integration tests in the owning integration-test suite, not the client unit loop.
