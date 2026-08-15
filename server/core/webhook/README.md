# Webhook Architecture

> Architecture for handling inbound webhooks from external providers.

## Principles

- Centralized webhook module for all providers
- Signature verification before processing
- Zod validation for payload schemas
- Idempotency via domain logic (no dedicated webhook table)
- Standard API response envelope
- Comprehensive logging for debugging
- Provider handlers are specialized framework-neutral controllers and always delegate to one use case

## Testing Guides

| Document | Description |
| --- | --- |
| [Testing Index](./testing/README.md) | Testing strategy + index |
| [Test Doubles](./testing/testing-test-doubles.md) | Stub/mock/spy/fake/simulator definitions |
| [Vendor Simulator](./testing/testing-vendor-simulator.md) | Emulator patterns and scenarios |
| [Schema Validation](./testing/testing-schema-validation.md) | Zod + fixtures + payload drift |
| [Routing + Business Logic](./testing/testing-routing-and-business-logic.md) | Handler registry, mapping, idempotency |
| [Contract + Regression](./testing/testing-contract-and-regression.md) | Fixture suite + versioning vendor changes |
| [Testing Checklist](./testing/testing-checklist.md) | CTO/product-ready checklist |

## Folder Structure

```
src/
├─ app/api/webhooks/stripe/route.ts   # Next.js adapter; Express/Hono use routes/
└─ lib/modules/
   └─ webhooks/
      ├─ stripe/
      │  ├─ stripe.validator.ts       # Signature verification
      │  ├─ stripe.schemas.ts         # Zod schemas per event type
      │  └─ handlers/                 # Specialized inbound controllers
      │     ├─ index.ts               # Handler registry
      │     ├─ invoice-paid.handler.ts
      │     └─ subscription-updated.handler.ts
      │
      ├─ clerk/
      │  ├─ clerk.validator.ts
      │  ├─ clerk.schemas.ts
      │  └─ handlers/
      │     └─ user-created.handler.ts
      │
      └─ shared/
         ├─ webhook.schemas.ts        # Payload schema
         ├─ webhook.errors.ts         # Webhook-specific errors
         └─ webhook-log-fields.ts     # Structured log fields
```

## Request Flow

```
Webhook Route (HTTP endpoint)
  → Verify signature (provider SDK)
  → Parse base event (Zod)
  → Route by event.type
  → Framework-neutral provider handler/controller
      → Validate specific payload (Zod)
      → Map provider event to command
      → Call one Use Case
  → Return envelope response
```

## Response Structure

### Success Response

```typescript
{
  data: {
    received: true,
    eventId: string,
    processed: boolean,   // false for a duplicate or unsupported event type
  }
}
```

**Examples:**

```json
// Processed
{
  "data": {
    "received": true,
    "eventId": "evt_1234",
    "processed": true
  }
}

// Skipped (idempotency)
{
  "data": {
    "received": true,
    "eventId": "evt_1234",
    "processed": false
  }
}
```

### Error Response

```json
{
  "code": "WEBHOOK_VERIFICATION_FAILED",
  "message": "Webhook signature verification failed for stripe",
  "requestId": "req-abc-123"
}
```

## Shared Components

### Response Schema

```typescript
// src/lib/modules/webhooks/shared/webhook.schemas.ts

import { z } from 'zod';

export const WebhookResponseSchema = z.object({
  received: z.literal(true),
  eventId: z.string(),
  processed: z.boolean(),
});

export type WebhookResponse = z.infer<typeof WebhookResponseSchema>;
```

### Webhook Errors

```typescript
// modules/webhooks/shared/webhook.errors.ts

import { AuthenticationError, ValidationError } from '@/shared/kernel/errors';

export class WebhookVerificationError extends AuthenticationError {
  readonly code = 'WEBHOOK_VERIFICATION_FAILED';

  constructor(provider: string) {
    super(`Webhook signature verification failed for ${provider}`);
  }
}

export class WebhookPayloadError extends ValidationError {
  readonly code = 'WEBHOOK_PAYLOAD_INVALID';

  constructor(provider: string, details?: Record<string, unknown>) {
    super(`Invalid webhook payload from ${provider}`, details);
  }
}

```

Unknown provider event types are not application errors. Providers add event
types over time, so an unhandled type is acknowledged with HTTP 200,
`processed: false`, and a structured `webhook.skipped` record. Invalid
signatures and malformed supported payloads still fail.

### Webhook Log Fields

```typescript
// modules/webhooks/shared/webhook-log-fields.ts

import { APP_ATTRIBUTES } from '@/shared/infra/observability/attributes';

export interface WebhookLogContext {
  provider: string;
  eventType: string;
  eventId: string;
}

export function webhookLogFields(ctx: WebhookLogContext) {
  return {
    [APP_ATTRIBUTES.webhookProvider]: ctx.provider,
    [APP_ATTRIBUTES.webhookEventType]: ctx.eventType,
    [APP_ATTRIBUTES.webhookEventId]: ctx.eventId,
  };
}
```

This helper builds custom fields only. The injected/contextual `AppLogger` supplies request and trace correlation.

## Logging Standards

### Log Events

| Event | Level | When |
|-------|-------|------|
| `webhook.received` | `info` | Signature verified, before processing |
| `webhook.processed` | `info` | Successfully processed |
| `webhook.skipped` | `info` | Duplicate or unsupported event type |
| `webhook.failed` | `error` | Processing failed |
| `webhook.verification_failed` | `warn` | Signature verification failed |
| `webhook.validation_failed` | `warn` | Payload validation failed |

### Log Data

| Field | Description |
|-------|-------------|
| `com.example.api.webhook.provider` | Provider name (Stripe, Clerk) |
| `com.example.api.webhook.event.type` | Provider event type (`invoice.paid`) |
| `com.example.api.webhook.event.id` | Provider event ID |
| `com.example.api.request.id` | Request ID; added by contextual `AppLogger` |
| `com.example.api.duration_ms` | Processing time in milliseconds |
| `com.example.api.skip.reason` | Skip reason (for idempotency) |

Use the `APP_ATTRIBUTES` constants rather than repeating these strings. Operational event names go in `otel.event.name`; trace correlation uses `trace_id`, `span_id`, and `trace_flags`. See [Observability](../observability.md).

## Provider Implementation: Stripe

### Zod Schemas

```typescript
// modules/webhooks/stripe/stripe.schemas.ts

import { z } from 'zod';

export const StripeEventSchema = z.object({
  id: z.string(),
  type: z.string(),
  data: z.object({
    object: z.record(z.unknown()),
  }),
});

export type StripeEvent = z.infer<typeof StripeEventSchema>;

export const StripeInvoicePaidSchema = z.object({
  id: z.string(),
  type: z.literal('invoice.paid'),
  data: z.object({
    object: z.object({
      id: z.string(),
      customer: z.string(),
      amount_paid: z.number(),
      currency: z.string(),
      status: z.string(),
      subscription: z.string().nullable(),
    }),
  }),
});

export type StripeInvoicePaidEvent = z.infer<typeof StripeInvoicePaidSchema>;
```

### Signature Validator

```typescript
// modules/webhooks/stripe/stripe.validator.ts

import Stripe from 'stripe';
import { env } from '@/env';
import { WebhookVerificationError } from '../shared/webhook.errors';

const stripe = new Stripe(env.STRIPE_SECRET_KEY);

export function verifyStripeSignature(
  rawBody: string,
  signature: string | null,
): Stripe.Event {
  if (!signature) {
    throw new WebhookVerificationError('stripe');
  }

  try {
    return stripe.webhooks.constructEvent(
      rawBody,
      signature,
      env.STRIPE_WEBHOOK_SECRET,
    );
  } catch (err) {
    throw new WebhookVerificationError('stripe');
  }
}
```

### Handler Interface

```typescript
// modules/webhooks/stripe/handlers/handler.interface.ts

export interface WebhookHandlerResult {
  skipped: boolean;
  reason?: string;
}

export interface IWebhookHandler {
  handle(rawEvent: unknown): Promise<WebhookHandlerResult>;
}
```

### Handler Implementation

Webhook handlers are specialized framework-neutral controllers: they map one provider event to one use case and contain no persistence or transport code.

```typescript
// modules/webhooks/stripe/handlers/invoice-paid.handler.ts

import type { IProcessPaymentUseCase } from '@/modules/payment/use-cases/process-payment.use-case.interface';
import { StripeInvoicePaidSchema } from '../stripe.schemas';
import { WebhookPayloadError } from '../../shared/webhook.errors';
import type { IWebhookHandler, WebhookHandlerResult } from './handler.interface';

export class InvoicePaidHandler implements IWebhookHandler {
  constructor(
    private processPaymentUseCase: IProcessPaymentUseCase,
  ) {}

  async handle(rawEvent: unknown): Promise<WebhookHandlerResult> {
    // Validate payload
    const result = StripeInvoicePaidSchema.safeParse(rawEvent);
    if (!result.success) {
      throw new WebhookPayloadError('stripe', {
        eventType: 'invoice.paid',
        issues: result.error.issues,
      });
    }

    const event = result.data;
    const invoiceId = event.data.object.id;

    // The use case owns idempotency, transaction, and operational logging.
    const outcome = await this.processPaymentUseCase.execute({
      stripeInvoiceId: invoiceId,
      amount: event.data.object.amount_paid,
      currency: event.data.object.currency,
      customerId: event.data.object.customer,
    });

    return outcome;
  }
}
```

### Handler Registry

```typescript
// modules/webhooks/stripe/handlers/index.ts

import type { IWebhookHandler } from './handler.interface';
import { InvoicePaidHandler } from './invoice-paid.handler';
import { SubscriptionUpdatedHandler } from './subscription-updated.handler';
import { makeProcessPaymentUseCase } from '@/modules/payment/factories/payment.factory';
import { makeUpdateSubscriptionUseCase } from '@/modules/subscription/factories/subscription.factory';

type StripeEventType = 'invoice.paid' | 'customer.subscription.updated';

const handlers: Record<StripeEventType, () => IWebhookHandler> = {
  'invoice.paid': () => new InvoicePaidHandler(
    makeProcessPaymentUseCase(),
  ),
  'customer.subscription.updated': () => new SubscriptionUpdatedHandler(
    makeUpdateSubscriptionUseCase(),
  ),
};

export function getStripeHandler(eventType: string): IWebhookHandler | null {
  const factory = handlers[eventType as StripeEventType];
  return factory ? factory() : null;
}

export function isHandledEventType(eventType: string): boolean {
  return eventType in handlers;
}
```

### Route Handler

```typescript
// app/api/webhooks/stripe/route.ts

import { NextResponse } from 'next/server';
import { appLogger } from '@/shared/infra/logger';
import { handleError } from '@/shared/infra/http/error-handler';
import {
  APP_ATTRIBUTES,
  withRequestObservability,
} from '@/shared/infra/observability';
import { wrapResponse } from '@/shared/utils/response';
import { WebhookResponseSchema } from '@/modules/webhooks/shared/webhook.schemas';
import { verifyStripeSignature } from '@/modules/webhooks/stripe/stripe.validator';
import { StripeEventSchema } from '@/modules/webhooks/stripe/stripe.schemas';
import { getStripeHandler, isHandledEventType } from '@/modules/webhooks/stripe/handlers';
import {
  WebhookVerificationError,
  WebhookPayloadError,
} from '@/modules/webhooks/shared/webhook.errors';

export async function POST(req: Request) {
  return withRequestObservability(req, async ({ requestId }) => {
    let webhookFields: Record<string, unknown> = {
      [APP_ATTRIBUTES.webhookProvider]: 'stripe',
    };

    try {
      const rawBody = await req.text();
      const signature = req.headers.get('stripe-signature');

      const stripeEvent = verifyStripeSignature(rawBody, signature);
      const parseResult = StripeEventSchema.safeParse(stripeEvent);

      if (!parseResult.success) {
        throw new WebhookPayloadError('stripe', {
          issues: parseResult.error.issues,
        });
      }

      const event = parseResult.data;

      webhookFields = {
        ...webhookFields,
        [APP_ATTRIBUTES.webhookEventType]: event.type,
        [APP_ATTRIBUTES.webhookEventId]: event.id,
      };

      appLogger.info(
        { ...webhookFields, 'otel.event.name': 'webhook.received' },
        'Webhook received',
      );

      if (!isHandledEventType(event.type)) {
        appLogger.info(
          {
            ...webhookFields,
            'otel.event.name': 'webhook.skipped',
            [APP_ATTRIBUTES.skipReason]: 'unhandled_event_type',
          },
          'Webhook skipped',
        );
        const response = WebhookResponseSchema.parse({
          received: true,
          eventId: event.id,
          processed: false,
        });
        return NextResponse.json(wrapResponse(response), { status: 200 });
      }

      const handler = getStripeHandler(event.type);
      if (!handler) {
        // Defensive fallback if the registry changes between the type check
        // and resolution. It follows the same unknown-event policy.
        const response = WebhookResponseSchema.parse({
          received: true,
          eventId: event.id,
          processed: false,
        });
        return NextResponse.json(wrapResponse(response), { status: 200 });
      }

      const start = Date.now();
      const result = await handler.handle(stripeEvent);
      const duration = Date.now() - start;

      if (result.skipped) {
        appLogger.info(
          {
            ...webhookFields,
            'otel.event.name': 'webhook.skipped',
            [APP_ATTRIBUTES.skipReason]: result.reason,
            [APP_ATTRIBUTES.durationMs]: duration,
          },
          'Webhook skipped',
        );
      } else {
        appLogger.info(
          {
            ...webhookFields,
            'otel.event.name': 'webhook.processed',
            [APP_ATTRIBUTES.durationMs]: duration,
          },
          'Webhook processed',
        );
      }

      const response = WebhookResponseSchema.parse({
        received: true,
        eventId: event.id,
        processed: !result.skipped,
      });
      return NextResponse.json(wrapResponse(response), { status: 200 });

    } catch (error) {
      const failureEvent = error instanceof WebhookVerificationError
        ? 'webhook.verification_failed'
        : error instanceof WebhookPayloadError
          ? 'webhook.validation_failed'
          : 'webhook.failed';
      const { status, body } = handleError(error, requestId, {
        ...webhookFields,
        'otel.event.name': failureEvent,
      });
      return NextResponse.json(body, { status });
    }
  });
}
```

`handleError` is the same central HTTP error adapter used by other framework
routes. Webhook routes do not maintain a second status/message mapping.

## Idempotency

Idempotency is enforced by **domain logic plus a database uniqueness
constraint**. A dedicated webhook-events table is optional, but an atomic
database guard is required.

### Pattern

The handler maps the event and calls one use case. The use case attempts one
atomic domain write using the provider's stable ID:

```typescript
const outcome = await this.transactionManager.run(async (tx) => {
  const payment = await this.paymentService.createFromStripeInvoiceIfAbsent(
    command,
    { tx },
  );

  if (!payment) {
    return { skipped: true, reason: 'payment_already_processed' } as const;
  }

  // Required side effects are persisted as outbox intent in the same tx.
  await this.receiptOutbox.enqueue({ paymentId: payment.id }, { tx });
  return { skipped: false } as const;
});

return outcome;
```

The repository implements this with a unique constraint such as
`UNIQUE (stripe_invoice_id)` and `INSERT ... ON CONFLICT DO NOTHING RETURNING`.
Do not implement idempotency as `find` followed by `insert`; concurrent
deliveries can both pass the read.

### Benefits

- No extra webhook table is required when the domain table owns a natural key
- Idempotency logic lives close to domain
- Concurrent deliveries are serialized by a database constraint

## Adding a New Provider

1. Create provider folder: `src/lib/modules/webhooks/<provider>/`

2. Create schemas: `<provider>.schemas.ts`
   - Base event schema
   - Per-event-type schemas

3. Create validator: `<provider>.validator.ts`
   - Signature verification using provider's SDK

4. Create handlers: `handlers/*.handler.ts`
   - Implement `IWebhookHandler` interface
   - Validate with Zod
   - Call use case

5. Create handler registry: `handlers/index.ts`
   - Map event types to handlers

6. Create the framework adapter in its entrypoint folder and follow the
   standard flow. Example: `app/api/webhooks/<provider>/route.ts` for Next.js,
   or `routes/webhooks.<provider>.ts` for Express/Hono.

## Future Considerations

- [ ] **Async processing** - Queue webhook events for background processing
- [ ] **Retry handling** - Store failed events for retry
- [ ] **Dead letter queue** - Handle permanently failed events
- [ ] **Webhook events table** - If audit trail needed, store raw events
- [ ] **Rate limiting** - Protect against webhook floods
- [ ] **Outbound webhooks** - Send events to external systems

## Checklist

- [ ] Webhook module created at `src/lib/modules/webhooks/`
- [ ] Shared components: `webhook.schemas.ts`, `webhook.errors.ts`, `webhook-log-fields.ts`
- [ ] Per-provider module: schemas, validator, handlers
- [ ] Framework route exists only in the selected adapter entrypoint folder
- [ ] Handler registry maps event types to handlers
- [ ] Handlers implement `IWebhookHandler` interface
- [ ] Handlers validate payloads with Zod
- [ ] Handlers import no framework, repository, database, or provider SDK types
- [ ] Use cases/services own idempotency and repositories enforce it atomically
- [ ] Provider IDs have explicit database unique constraints
- [ ] Handlers delegate to Use Cases (not Services directly)
- [ ] Routes verify signatures before processing
- [ ] Routes return standard envelope response
- [ ] Routes handle errors with proper status codes
- [ ] All webhook events logged with consistent context
