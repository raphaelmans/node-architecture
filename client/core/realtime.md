# Realtime Subscriptions (Agnostic)

> Framework- and provider-neutral contracts for event-driven client synchronization.

## Core Pattern

```text
Realtime transport -> feature realtime API -> lifecycle adapter -> cache strategy
```

The layers have separate responsibilities:

1. The transport owns connection mechanics and provider payloads.
2. The feature realtime API validates and maps provider payloads into domain events.
3. A framework lifecycle adapter subscribes, unsubscribes, and tracks reconnect gaps.
4. A cache strategy applies a safe patch or invalidates affected query scopes.

## Transport Port

Provider types remain behind a transport-neutral interface:

```typescript
export type RealtimeConnectionState =
  | "connecting"
  | "connected"
  | "disconnected"
  | "error";

export interface RealtimeSubscription {
  unsubscribe(): Promise<void> | void;
}

export interface RealtimeClient<TWireEvent, TFilter> {
  subscribe(input: {
    filter: TFilter;
    onEvent(event: TWireEvent): void;
    onStateChange?(state: RealtimeConnectionState): void;
  }): RealtimeSubscription;
}
```

The provider adapter validates enough of the outer payload to reject malformed messages safely. It must not expose vendor channel objects, database clients, or SDK error types to feature code.

## Feature Realtime API

The feature boundary validates the capability payload and maps it immediately into a domain event:

```typescript
export interface IReservationRealtimeApi {
  subscribe(input: {
    reservationId: string;
    onEvent(event: ReservationRealtimeEvent): void;
    onStateChange?(state: RealtimeConnectionState): void;
  }): RealtimeSubscription;
}

export const createReservationRealtimeApi = (
  deps: ReservationRealtimeApiDeps,
): IReservationRealtimeApi => new ReservationRealtimeApi(deps);
```

Construction follows the normal composition-root rules. The browser instance is application-scoped unless the adapter captures subscriber-specific request context. Tests inject fake transports and do not connect to a live provider.

Provider rows and envelopes are private wire types. They are validated and mapped before `onEvent` receives a domain event.

## Cache Strategies

The lifecycle adapter depends on a narrow cache port so the core event reducer does not import a UI framework:

```typescript
export interface RealtimeCache {
  patch<T>(key: QueryKey, update: (current: T | undefined) => T | undefined): void;
  invalidate(key: QueryKey): Promise<void> | void;
}
```

### Event-carried state transfer

When the event contains enough state:

1. Apply an immutable cache patch for immediate feedback.
2. Invalidate the affected query scope so active observers reconcile with server truth.

```typescript
function onReservationEvent(event: ReservationRealtimeEvent) {
  cache.patch(reservationKeys.detail(event.reservationId), (current) =>
    applyReservationEvent(current, event),
  );

  void cache.invalidate(reservationKeys.detail(event.reservationId));
}
```

The patch helper is pure and independently tested. Direct immutable transforms are fine for shallow data; Immer is optional when a nested patch is clearer with a draft.

### Invalidation only

When the event only signals that something changed, or patch semantics are risky, invalidate the smallest known scope:

```typescript
function onNotificationChanged() {
  void cache.invalidate(notificationKeys.unreadCount());
  void cache.invalidate(notificationKeys.list());
}
```

Do not fabricate partial entities from an event that does not carry a complete-enough contract.

## Reconnection and Gap Recovery

- The initial connection does not imply missed data and should not trigger a redundant resync.
- After a connected subscription becomes disconnected or errors, mark the scope as potentially stale.
- On the next successful connection, invalidate all affected scopes once to recover events missed during the gap.
- Provider retry/backoff policy stays in the transport adapter; cache resynchronization stays in the lifecycle/cache coordinator.
- If ordering matters, the domain event contract must carry a monotonic sequence/version and the reducer must ignore stale events.

## Operational Ownership

- Transport adapter: connection failures, retry exhaustion, sanitized channel/topic, and duration through `AppLogger`.
- Feature realtime API: invalid payload or domain mapping failure.
- Lifecycle/cache coordinator: meaningful reconnect/resync outcomes only.
- Product analytics: never receives transport failures; emit a product event only when a distinct user/business occurrence exists.

Each failure has one reporting owner.

## Rules

- Keep React hooks and provider SDK calls out of this core contract.
- Validate unknown wire events before mapping.
- Use domain events rather than database rows outside the provider/feature boundary.
- Patch only when the event contract is sufficient; otherwise invalidate.
- Reconcile patched data with server truth through invalidation.
- Coalesce or throttle reconciliation for high-frequency streams; do not trigger one network refetch per event when events can arrive in bursts.
- Make unsubscribe idempotent and safe during teardown.
- Put provider/server setup in a provider-specific guide.

## Related Docs

- `client/core/server-state-tanstack-query.md` — cache management patterns
- `client/core/query-keys.md` — query key conventions
- `client/core/composition-root.md` — factories and runtime lifetimes
- `client/frameworks/reactjs/realtime-react.md` — React subscription lifecycle
- `client/frameworks/reactjs/metaframeworks/nextjs/realtime-supabase.md` — Supabase adapter example
- `server/core/event-patterns.md` — server-side event log and outbox patterns
