# Realtime Subscriptions (Agnostic)

> Client-side realtime subscription architecture for event-driven cache updates.

## Core Pattern

Realtime subscriptions follow a four-layer chain:

```
Realtime Client (transport) → Feature Realtime API (domain mapping) → React Hook (subscription lifecycle) → Cache Strategy (patch/invalidate)
```

### 1) Realtime Client (`common/clients/<entity>-realtime-client/`)

Each realtime-enabled entity has a dedicated client in `common/clients/`:

```text
src/common/clients/
  availability-realtime-client/
  reservation-realtime-client/
  notification-realtime-client/
  chat-realtime-client/
```

Every client follows the same structural blueprint:

- A typed row type matching the DB table columns
- A connection-status type: `"SUBSCRIBED" | "TIMED_OUT" | "CLOSED" | "CHANNEL_ERROR"`
- A runtime type guard (`isXxxRow`) to validate the payload before forwarding
- A channel name generator using `Date.now() + random()` to avoid collisions
- A filter builder generating PostgREST filter strings (`column=eq.value`)
- A class implementing an interface, with a singleton exported via `getXxxClient()`
- Subscription returns `{ channelName, unsubscribe }` where `unsubscribe()` calls `supabase.removeChannel(channel)`

Clients subscribe to `postgres_changes` with `event: "INSERT"` and `schema: "public"`. This is an append-only event log contract — no UPDATE or DELETE events.

### 2) Feature Realtime API (`features/<feature>/realtime-api.ts`)

Maps raw DB rows to domain events, following the same `I<Feature>Api` pattern as `api.ts`:

```typescript
// src/features/reservation/realtime-api.ts
export interface IReservationRealtimeApi {
  subscribePlayer(params: SubscribeParams): Subscription;
  subscribeOwner(params: SubscribeParams): Subscription;
}

export class ReservationRealtimeApi implements IReservationRealtimeApi {
  // Maps raw DB rows → ReservationRealtimeDomainEvent
  // Validates from_status, to_status, triggered_by_role against enums
  // Constructs sequenceCursor for ordering
}
```

Has a corresponding `realtime-api.runtime.ts` for test mocking.

### 3) React Hook (subscription lifecycle)

Features expose `useMod<Feature>RealtimeSync` hooks that manage the subscription lifecycle in `useEffect`:

```typescript
useEffect(() => {
  const sub = realtimeApi.subscribe({
    filter: { entityId },
    onEvent: handleEvent,
    onStatusChange: handleStatus,
  });
  return () => sub.unsubscribe();
}, [entityId]);
```

### 4) Cache Strategy

Two cache strategies are used depending on event payload richness:

## Event-Carried State Transfer + Eventual Consistency

This is the primary realtime cache pattern. It's a hybrid of two strategies:

1. **Event arrives with payload** → patch the cache immediately (user sees the change now)
2. **Trigger a background refetch** → server confirms the truth
3. **Refetch result replaces the optimistic patch** silently

```typescript
function handleEvent(event: RealtimeEvent) {
  // Step 1: Patch the cache with event data (Immer)
  queryClient.setQueryData(queryKey, (old) =>
    old
      ? produce(old, (draft) => {
          const slot = draft.slots.find((s) => s.id === event.slotId);
          if (slot) slot.status = event.newStatus;
        })
      : old,
  );

  // Step 2: Mark stale and refetch active observers for truth reconciliation
  queryClient.invalidateQueries({ queryKey, refetchType: "none" });
  queryClient.refetchQueries({ queryKey, type: "active" });
}
```

**Why this works:**

- The event carries enough data to patch the cache immediately → the user sees changes in real-time
- The background refetch reconciles any drift between the optimistic patch and the actual server state
- If the refetch returns different data, it silently replaces the patch — no flash, no error

**When to use:** When the realtime event payload contains sufficient data to produce a meaningful cache patch (e.g., availability slot status changes).

## Invalidation-Only Strategy

For simpler cases where patching isn't worth the complexity:

```typescript
function handleEvent() {
  queryClient.invalidateQueries({ queryKey: notificationKeys.unreadCount });
  queryClient.invalidateQueries({ queryKey: notificationKeys.list });
}
```

**When to use:** When the event signals "something changed" but the payload doesn't carry enough data to patch, or when the query is cheap to refetch.

## Reconnection / Resync

Realtime clients must handle disconnections gracefully:

```typescript
const [hasSeenInitialSubscribe, setHasSeenInitialSubscribe] = useState(false);
const [shouldResyncOnSubscribe, setShouldResyncOnSubscribe] = useState(false);

function handleStatus(status: ConnectionStatus) {
  if (status === "SUBSCRIBED") {
    if (!hasSeenInitialSubscribe) {
      setHasSeenInitialSubscribe(true);
      return; // suppress unnecessary invalidation on first connect
    }
    if (shouldResyncOnSubscribe) {
      // Reconnected after a gap — invalidate everything to catch missed events
      queryClient.invalidateQueries({ queryKey: scopeKey });
      setShouldResyncOnSubscribe(false);
    }
  }

  if (["TIMED_OUT", "CLOSED", "CHANNEL_ERROR"].includes(status) && hasSeenInitialSubscribe) {
    setShouldResyncOnSubscribe(true);
  }
}
```

Rules:

- Suppress invalidation on initial subscribe (no events were missed)
- On reconnect after error, invalidate all affected queries to catch the gap
- Each client implements its own resync policy based on payload complexity

## Server-Side Setup (Supabase Realtime)

Realtime broadcasting uses PostgreSQL WAL (Write-Ahead Log) via Supabase Realtime publications:

1. Add the table to the publication: `ALTER PUBLICATION supabase_realtime ADD TABLE public.<table_name>`
2. Set `REPLICA IDENTITY FULL` on tables with filter columns (required for PostgREST filter validation)
3. Grant `SELECT` to `authenticated` and `anon` roles (Supabase validates `has_column_privilege` before allowing subscriptions)

These are set up via migration SQL files or one-time scripts.

## Rules

- Each realtime-enabled entity gets its own client in `common/clients/`
- Clients subscribe to INSERT events only (append-only event log)
- Use event-carried state transfer when the payload is rich enough to patch
- Always follow a patch with a background refetch for truth reconciliation
- Handle reconnection by invalidating affected queries
- Use Immer for cache patches to preserve immutability guarantees

## Related Docs

- `client/core/server-state-tanstack-query.md` — cache management patterns
- `client/core/query-keys.md` — query key conventions
- `client/core/client-api-architecture.md` — `realtime-api.ts` file placement
- `server/core/event-patterns.md` — server-side event log and outbox patterns
