# Webhook Architecture

> **Purpose**: This document defines the architecture for handling inbound webhooks from external providers.

---

## 1. Overview

**Principles:**

- Centralized webhook module for all providers
- Signature verification before processing
- Zod validation for payload schemas
- Idempotency via domain logic (no dedicated webhook table)
- Standard API response envelope
- Comprehensive logging for debugging

**Current Scope:** Inbound webhooks (receiving from external services)

---

## 2. Folder Structure

```
src/
├─ modules/
│  └─ webhooks/
│     ├─ stripe/
│     │  ├─ stripe.route.ts           # POST /api/webhooks/stripe
│     │  ├─ stripe.validator.ts       # Signature verification
│     │  ├─ stripe.schemas.ts         # Zod schemas per event type
│     │  └─ handlers/
│     │     ├─ index.ts               # Handler registry
│     │     ├─ invoice-paid.handler.ts
│     │     └─ subscription-updated.handler.ts
│     │
│     ├─ clerk/
│     │  ├─ clerk.route.ts
│     │  ├─ clerk.validator.ts
│     │  ├─ clerk.schemas.ts
│     │  └─ handlers/
│     │     └─ user-created.handler.ts
│     │
│     └─ shared/
│        ├─ webhook.schemas.ts        # Response schema
│        ├─ webhook.errors.ts         # Webhook-specific errors
│        └─ webhook.logger.ts         # Webhook logger factory
```

---

## 3. Request Flow

```
Webhook Route (Next.js API route)
  → Verify signature (provider SDK)
  → Parse base event (Zod)
  → Route by event.type
  → Validate specific payload (Zod)
  → Call Use Case
  → Return envelope response
```

---

## 4. Response Structure

Following the standard API response envelope.

### Success Response

```typescript
{
  data: {
    received: true,
    eventId: string,
    processed: boolean,   // false if skipped due to idempotency
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

Same as standard error response:

```json
{
  "code": "WEBHOOK_VERIFICATION_FAILED",
  "message": "Webhook signature verification failed for stripe",
  "requestId": "req-abc-123"
}
```

---

## 5. Shared Components

### 5.1 Response Schema

```typescript
// modules/webhooks/shared/webhook.schemas.ts

import { z } from 'zod';

export const WebhookResponseSchema = z.object({
  data: z.object({
    received: z.literal(true),
    eventId: z.string(),
    processed: z.boolean(),
  }),
});

export type WebhookResponse = z.infer<typeof WebhookResponseSchema>;
```

### 5.2 Webhook Errors

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

export class WebhookHandlerNotFoundError extends ValidationError {
  readonly code = 'WEBHOOK_HANDLER_NOT_FOUND';

  constructor(provider: string, eventType: string) {
    super(`No handler registered for ${provider} event: ${eventType}`);
  }
}
```

### 5.3 Webhook Logger

```typescript
// modules/webhooks/shared/webhook.logger.ts

import { logger } from '@/shared/infra/logger';

export interface WebhookLogContext {
  provider: string;       // 'stripe', 'clerk'
  eventType: string;      // 'invoice.paid'
  eventId: string;        // Provider's event ID
  requestId: string;      // Our request ID
}

/**
 * Creates a child logger with webhook context.
 */
export function createWebhookLogger(ctx: WebhookLogContext) {
  return logger.child({
    webhook: true,
    provider: ctx.provider,
    eventType: ctx.eventType,
    eventId: ctx.eventId,
    requestId: ctx.requestId,
  });
}
```

---

## 6. Logging Standards

### Log Events

| Event | Level | When |
|-------|-------|------|
| `webhook.received` | `info` | Signature verified, before processing |
| `webhook.processed` | `info` | Successfully processed |
| `webhook.skipped` | `info` | Skipped due to idempotency |
| `webhook.failed` | `error` | Processing failed |
| `webhook.verification_failed` | `warn` | Signature verification failed |
| `webhook.validation_failed` | `warn` | Payload validation failed |

### Log Data

| Field | Description |
|-------|-------------|
| `provider` | Provider name (stripe, clerk) |
| `eventType` | Event type (invoice.paid) |
| `eventId` | Provider's event ID |
| `requestId` | Our request ID |
| `duration` | Processing time in ms |
| `reason` | Skip reason (for idempotency) |

---

## 7. Provider Implementation: Stripe

### 7.1 Zod Schemas

```typescript
// modules/webhooks/stripe/stripe.schemas.ts

import { z } from 'zod';

/**
 * Base Stripe event schema for initial parsing and routing.
 */
export const StripeEventSchema = z.object({
  id: z.string(),
  type: z.string(),
  data: z.object({
    object: z.record(z.unknown()),
  }),
});

export type StripeEvent = z.infer<typeof StripeEventSchema>;

/**
 * invoice.paid event schema.
 */
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

/**
 * customer.subscription.updated event schema.
 */
export const StripeSubscriptionUpdatedSchema = z.object({
  id: z.string(),
  type: z.literal('customer.subscription.updated'),
  data: z.object({
    object: z.object({
      id: z.string(),
      customer: z.string(),
      status: z.enum(['active', 'canceled', 'incomplete', 'past_due', 'trialing', 'unpaid']),
      current_period_start: z.number(),
      current_period_end: z.number(),
    }),
  }),
});

export type StripeSubscriptionUpdatedEvent = z.infer<typeof StripeSubscriptionUpdatedSchema>;
```

### 7.2 Signature Validator

```typescript
// modules/webhooks/stripe/stripe.validator.ts

import Stripe from 'stripe';
import { env } from '@/env';
import { WebhookVerificationError } from '../shared/webhook.errors';

const stripe = new Stripe(env.STRIPE_SECRET_KEY);

/**
 * Verifies Stripe webhook signature and returns parsed event.
 */
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

### 7.3 Handler Interface

```typescript
// modules/webhooks/stripe/handlers/handler.interface.ts

import type { Logger } from '@/shared/infra/logger';

export interface WebhookHandlerResult {
  skipped: boolean;
  reason?: string;
}

export interface IWebhookHandler {
  handle(rawEvent: unknown, log: Logger): Promise<WebhookHandlerResult>;
}
```

### 7.4 Handler Implementation

```typescript
// modules/webhooks/stripe/handlers/invoice-paid.handler.ts

import type { Logger } from '@/shared/infra/logger';
import type { IProcessPaymentUseCase } from '@/modules/payment/use-cases/process-payment.use-case.interface';
import type { IPaymentRepository } from '@/modules/payment/repositories/payment.repository.interface';
import { StripeInvoicePaidSchema } from '../stripe.schemas';
import { WebhookPayloadError } from '../../shared/webhook.errors';
import type { IWebhookHandler, WebhookHandlerResult } from './handler.interface';

export class InvoicePaidHandler implements IWebhookHandler {
  constructor(
    private processPaymentUseCase: IProcessPaymentUseCase,
    private paymentRepository: IPaymentRepository,
  ) {}

  async handle(rawEvent: unknown, log: Logger): Promise<WebhookHandlerResult> {
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

    // Idempotency check via domain
    const existing = await this.paymentRepository.findByStripeInvoiceId(invoiceId);
    if (existing) {
      return { skipped: true, reason: 'Payment already processed' };
    }

    log.info(
      {
        invoiceId,
        amount: event.data.object.amount_paid,
        currency: event.data.object.currency,
      },
      'Processing payment',
    );

    // Delegate to use case
    await this.processPaymentUseCase.execute({
      stripeInvoiceId: invoiceId,
      amount: event.data.object.amount_paid,
      currency: event.data.object.currency,
      customerId: event.data.object.customer,
    });

    return { skipped: false };
  }
}
```

### 7.5 Handler Registry

```typescript
// modules/webhooks/stripe/handlers/index.ts

import type { IWebhookHandler } from './handler.interface';
import { InvoicePaidHandler } from './invoice-paid.handler';
import { SubscriptionUpdatedHandler } from './subscription-updated.handler';
import { makeProcessPaymentUseCase } from '@/modules/payment/factories/payment.factory';
import { makeUpdateSubscriptionUseCase } from '@/modules/subscription/factories/subscription.factory';
import { makePaymentRepository } from '@/modules/payment/factories/payment.factory';

type StripeEventType = 'invoice.paid' | 'customer.subscription.updated';

const handlers: Record<StripeEventType, () => IWebhookHandler> = {
  'invoice.paid': () => new InvoicePaidHandler(
    makeProcessPaymentUseCase(),
    makePaymentRepository(),
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

### 7.6 Route Handler

```typescript
// modules/webhooks/stripe/stripe.route.ts
// Location: app/api/webhooks/stripe/route.ts

import { NextResponse } from 'next/server';
import { logger } from '@/shared/infra/logger';
import { wrapResponse } from '@/shared/utils/response';
import { verifyStripeSignature } from './stripe.validator';
import { StripeEventSchema } from './stripe.schemas';
import { getStripeHandler, isHandledEventType } from './handlers';
import { createWebhookLogger } from '../shared/webhook.logger';
import {
  WebhookVerificationError,
  WebhookPayloadError,
  WebhookHandlerNotFoundError,
} from '../shared/webhook.errors';

export async function POST(req: Request) {
  const requestId = crypto.randomUUID();
  let log = logger.child({ requestId, provider: 'stripe' });

  try {
    // 1. Get raw body and signature
    const rawBody = await req.text();
    const signature = req.headers.get('stripe-signature');

    // 2. Verify signature
    const stripeEvent = verifyStripeSignature(rawBody, signature);

    // 3. Parse base event with Zod
    const parseResult = StripeEventSchema.safeParse(stripeEvent);
    if (!parseResult.success) {
      throw new WebhookPayloadError('stripe', {
        issues: parseResult.error.issues,
      });
    }

    const event = parseResult.data;

    // 4. Create webhook-specific logger
    log = createWebhookLogger({
      provider: 'stripe',
      eventType: event.type,
      eventId: event.id,
      requestId,
    });

    log.info({ event: 'webhook.received' }, 'Webhook received');

    // 5. Check if we handle this event type
    if (!isHandledEventType(event.type)) {
      log.info({ event: 'webhook.skipped', reason: 'Unhandled event type' }, 'Webhook skipped');
      return NextResponse.json(
        wrapResponse({
          received: true,
          eventId: event.id,
          processed: false,
        }),
        { status: 200 },
      );
    }

    // 6. Get and execute handler
    const handler = getStripeHandler(event.type);
    if (!handler) {
      throw new WebhookHandlerNotFoundError('stripe', event.type);
    }

    const start = Date.now();
    const result = await handler.handle(stripeEvent, log);
    const duration = Date.now() - start;

    // 7. Log outcome
    if (result.skipped) {
      log.info(
        { event: 'webhook.skipped', reason: result.reason, duration },
        'Webhook skipped',
      );
    } else {
      log.info(
        { event: 'webhook.processed', duration },
        'Webhook processed',
      );
    }

    // 8. Return success response
    return NextResponse.json(
      wrapResponse({
        received: true,
        eventId: event.id,
        processed: !result.skipped,
      }),
      { status: 200 },
    );

  } catch (error) {
    // Handle known errors
    if (error instanceof WebhookVerificationError) {
      log.warn(
        { event: 'webhook.verification_failed', err: error },
        'Webhook signature verification failed',
      );
      return NextResponse.json(
        {
          code: error.code,
          message: error.message,
          requestId,
        },
        { status: 401 },
      );
    }

    if (error instanceof WebhookPayloadError) {
      log.warn(
        { event: 'webhook.validation_failed', err: error, details: error.details },
        'Webhook validation failed',
      );
      return NextResponse.json(
        {
          code: error.code,
          message: error.message,
          requestId,
          details: error.details,
        },
        { status: 400 },
      );
    }

    // Unknown error
    log.error(
      { event: 'webhook.failed', err: error },
      'Webhook processing failed',
    );
    return NextResponse.json(
      {
        code: 'INTERNAL_ERROR',
        message: 'An unexpected error occurred',
        requestId,
      },
      { status: 500 },
    );
  }
}
```

---

## 8. Provider Implementation: Clerk

### 8.1 Zod Schemas

```typescript
// modules/webhooks/clerk/clerk.schemas.ts

import { z } from 'zod';

/**
 * Base Clerk event schema.
 */
export const ClerkEventSchema = z.object({
  type: z.string(),
  data: z.record(z.unknown()),
  object: z.literal('event'),
});

export type ClerkEvent = z.infer<typeof ClerkEventSchema>;

/**
 * user.created event schema.
 */
export const ClerkUserCreatedSchema = z.object({
  type: z.literal('user.created'),
  data: z.object({
    id: z.string(),
    email_addresses: z.array(z.object({
      id: z.string(),
      email_address: z.string(),
    })),
    first_name: z.string().nullable(),
    last_name: z.string().nullable(),
    created_at: z.number(),
  }),
  object: z.literal('event'),
});

export type ClerkUserCreatedEvent = z.infer<typeof ClerkUserCreatedSchema>;
```

### 8.2 Signature Validator

```typescript
// modules/webhooks/clerk/clerk.validator.ts

import { Webhook } from 'svix';
import { env } from '@/env';
import { WebhookVerificationError } from '../shared/webhook.errors';

/**
 * Verifies Clerk webhook signature using Svix.
 */
export function verifyClerkSignature(
  rawBody: string,
  headers: Headers,
): unknown {
  const svixId = headers.get('svix-id');
  const svixTimestamp = headers.get('svix-timestamp');
  const svixSignature = headers.get('svix-signature');

  if (!svixId || !svixTimestamp || !svixSignature) {
    throw new WebhookVerificationError('clerk');
  }

  const wh = new Webhook(env.CLERK_WEBHOOK_SECRET);

  try {
    return wh.verify(rawBody, {
      'svix-id': svixId,
      'svix-timestamp': svixTimestamp,
      'svix-signature': svixSignature,
    });
  } catch (err) {
    throw new WebhookVerificationError('clerk');
  }
}
```

---

## 9. Idempotency

Idempotency is handled via **domain logic**, not a dedicated webhook events table.

### Pattern

Each handler checks if the action has already been performed:

```typescript
// Check by provider's unique ID
const existing = await this.paymentRepository.findByStripeInvoiceId(invoiceId);
if (existing) {
  return { skipped: true, reason: 'Payment already processed' };
}

// Check by provider's user ID
const existing = await this.userRepository.findByClerkId(clerkUserId);
if (existing) {
  return { skipped: true, reason: 'User already exists' };
}
```

### Benefits

- No extra table to maintain
- Idempotency logic lives close to domain
- Natural checks using existing queries

---

## 10. Adding a New Provider

1. Create provider folder: `modules/webhooks/<provider>/`

2. Create schemas: `<provider>.schemas.ts`
   - Base event schema
   - Per-event-type schemas

3. Create validator: `<provider>.validator.ts`
   - Signature verification using provider's SDK

4. Create handlers: `handlers/*.handler.ts`
   - Implement `IWebhookHandler` interface
   - Validate with Zod
   - Check idempotency
   - Call use case

5. Create handler registry: `handlers/index.ts`
   - Map event types to handlers

6. Create route: `<provider>.route.ts`
   - Follow the standard flow

7. Register route in Next.js: `app/api/webhooks/<provider>/route.ts`

---

## 11. Future Considerations

For future reference when scaling:

- [ ] **Async processing** - Queue webhook events for background processing
- [ ] **Retry handling** - Store failed events for retry
- [ ] **Dead letter queue** - Handle permanently failed events
- [ ] **Webhook events table** - If audit trail needed, store raw events
- [ ] **Rate limiting** - Protect against webhook floods
- [ ] **Outbound webhooks** - Send events to external systems

---

## 12. Checklist

- [ ] Webhook module created at `modules/webhooks/`
- [ ] Shared components: `webhook.schemas.ts`, `webhook.errors.ts`, `webhook.logger.ts`
- [ ] Per-provider: schemas, validator, handlers, route
- [ ] Handler registry maps event types to handlers
- [ ] Handlers implement `IWebhookHandler` interface
- [ ] Handlers validate payloads with Zod
- [ ] Handlers check idempotency via domain queries
- [ ] Handlers delegate to Use Cases (not Services directly)
- [ ] Routes verify signatures before processing
- [ ] Routes return standard envelope response
- [ ] Routes handle errors with proper status codes
- [ ] All webhook events logged with consistent context
