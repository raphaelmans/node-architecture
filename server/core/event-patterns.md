# Event-Driven Patterns

> Server-side patterns for domain events, side effects, and async delivery.

The architecture uses practical event-driven patterns without a formal event bus. These patterns are production-complete and tested.

## Domain Event Log

For entities where state changes need to be broadcast to clients in real-time, use an **append-only event table**:

```
domain operation → write event row (inside transaction) → PostgreSQL WAL → Supabase Realtime → client
```

### Pattern: Availability Change Events

The `availability_change_event` table is a pure event log — never updated, only inserted:

```typescript
// availability_change_event schema
{
  id: uuid,
  courtId: uuid,
  placeId: uuid,
  sourceKind: "RESERVATION" | "COURT_BLOCK",
  sourceEvent: "reservation.created" | "reservation.expired" | "reservation.cancelled" | ...,
  slotStatus: "AVAILABLE" | "BOOKED",
  unavailableReason: "RESERVATION" | "MAINTENANCE" | "WALK_IN" | null,
  occurredAt: timestamp,
}
```

### Event Service Interface

A domain event service encapsulates emission:

```typescript
export interface IAvailabilityChangeEventService {
  emitReservationBooked(params: EmitParams): Promise<void>;
  emitReservationReleased(params: EmitParams): Promise<void>;
  emitCourtBlockBooked(params: EmitParams): Promise<void>;
  emitCourtBlockReleased(params: EmitParams): Promise<void>;
}
```

Named methods are thin adapters over `emitMany(events)` which calls the repository's `createMany`.

### Emission Rules

- Event writes happen **inside the DB transaction** — if the transaction rolls back, no event is written and no realtime broadcast happens
- All services that modify the entity's state must emit events: create, cancel, expire, confirm, reject
- Event names use `<entity>.<past_tense_action>` format

### When to Use

Use a domain event log when:

- Clients need real-time visibility into state changes
- Multiple independent consumers need to react to the same state change
- An audit trail of state transitions is valuable

## Notification Delivery Pipeline (Outbox Pattern)

For reliable async delivery of notifications across multiple channels:

```
service method → enqueue jobs (inside tx) → after() kick → QStash → dispatch worker → deliver
```

### Step 1: Enqueue (inside transaction)

```typescript
// Inside ReservationService, within the DB transaction
await this.notificationDeliveryService.enqueueOwnerReservationCreated(payload, ctx);
```

`enqueueXxx` builds `NotificationDeliveryJob[]` records for each enabled channel (EMAIL, SMS, WEB_PUSH, MOBILE_PUSH) and each recipient. Jobs are inserted with an idempotency key: `{event_type}:{entity_id}:{role}:{user_id}:{channel}`.

It also writes an `user_notification` record directly for the in-app inbox (no job needed).

### Step 2: Dispatch Trigger (after response)

```typescript
// Best-effort post-response signal after commit
after(() => {
  dispatchTriggerQueue.publishDispatchKick({ reason: "enqueue", jobCount });
});
```

Next.js `after()` is a best-effort post-response hook that decouples QStash publish from response latency. Treat it as a trigger signal, not a durable queue: if publish fails or times out, jobs remain in `PENDING` status and the cron fallback must drain them.

### Step 3: Queue Worker

The QStash endpoint (`/api/internal/queue/dispatch-notification-delivery`) verifies the HMAC signature, then processes batches:

- `claimBatch({ limit: 25 })` — transactional `SELECT FOR UPDATE SKIP LOCKED` for atomic job claiming
- Up to `DISPATCH_CONCURRENCY = 5` jobs in parallel via `pLimit`
- If a full batch is processed (backlog likely), self-re-queues for draining

### Step 4: Delivery + Error Handling

| Outcome | Action |
| --- | --- |
| Success | Set status `"SENT"`, store `providerMessageId` |
| WebPush 404/410 | Revoke subscription, set `"SKIPPED"`, reason `"SUBSCRIPTION_GONE"` |
| ExpoPush `DeviceNotRegistered` | Revoke mobile token, set `"SKIPPED"` |
| Transient failure | Exponential backoff `[1, 5, 15, 60, 360]` minutes, max 5 attempts |

### Cron Fallback

`GET /api/cron/dispatch-notification-delivery` runs the same handler on a schedule, catching any jobs where the QStash kick was never published.

## Side-Effect Procedures (`ops/`)

For best-effort post-commit side effects that don't need transactional guarantees:

```
service method (post-commit) → ops/<procedure>.ts → external provider
```

### Pattern

```typescript
// modules/chat/ops/post-player-created-message.ts
export async function postPlayerCreatedMessage(params: Params): Promise<void> {
  const thread = await ensureReservationThread(params);
  await chatProvider.sendSystemMessage(thread.channelId, messageText);
}
```

### Calling Convention

Services call ops as best-effort, catching and logging failures:

```typescript
// Inside ReservationService, AFTER transaction commits
try {
  await postPlayerCreatedMessage({ reservationId, ... });
} catch (error) {
  logger.warn({ error }, "Failed to post player created chat message");
}
```

### When to Use `ops/` vs Outbox

| Use `ops/` | Use outbox (notification pipeline) |
| --- | --- |
| Best-effort, no retry needed | Must guarantee delivery |
| Single external call | Multi-channel fan-out |
| Failure is acceptable (chat message) | Failure triggers retry + backoff |
| Synchronous within request lifecycle | Async, decoupled from request |

## Command/Query Separation

The architecture uses a practical command/query separation at multiple levels:

### Router Level

tRPC consistently separates `.query` (reads) from `.mutation` (writes). Reads delegate directly to services; complex writes may use use cases.

### Service Level

Modules with distinct user roles split into separate service classes:

- `ReservationService` — player perspective (create, cancel, mark payment)
- `ReservationOwnerService` — owner perspective (confirm, reject, reschedule)

They share repositories but have entirely different DTOs, error types, and business rules.

### Client API Level

`IFeatureApi` interfaces use explicit naming:

- `mutReservationCreateForCourt` — commands (mutations)
- `queryReservationGetById` — queries

This makes the command/query boundary explicit in the type system.

### What's NOT Implemented

- Separate read models / materialized projections
- Formal event bus or pub/sub system
- Systematic use-case extraction (most writes are service methods)

These remain genuinely deferred.

## Related Docs

- `client/core/realtime.md` — client-side realtime subscription architecture
- `server/core/conventions.md` — module `ops/`, `queues/`, `providers/` sub-folders
- `server/core/async-jobs-outbox.md` — conceptual outbox pattern
- `client/core/server-state-tanstack-query.md` — cache management patterns
