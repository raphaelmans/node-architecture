---
name: backend-webhook
description: Implements inbound and outbound webhook handling with signature verification, Zod validation, and idempotency. Use when integrating external services via webhooks, handling Stripe/Clerk/GitHub webhooks, or when the user mentions "webhook", "handle events", "Stripe integration", "external provider".
---

# Webhook Implementation

## Overview

Webhooks are handled in a centralized module with per-provider organization:

```
src/modules/webhooks/
├── <provider>/
│   ├── <provider>.route.ts       # POST /api/webhooks/<provider>
│   ├── <provider>.validator.ts   # Signature verification
│   ├── <provider>.schemas.ts     # Zod schemas per event
│   └── handlers/
│       ├── index.ts              # Handler registry
│       └── <event>.handler.ts    # Per-event handlers
├── shared/
│   ├── webhook.schemas.ts        # Response schema
│   ├── webhook.errors.ts         # Webhook errors
│   └── webhook.logger.ts         # Logger factory
└── outbound/                     # Outbound webhooks (if needed)
    ├── outbound.service.ts
    └── outbound.schemas.ts
```

## Inbound Webhook Flow

```
Route (Next.js API)
  → Verify signature (provider SDK)
  → Parse base event (Zod)
  → Route by event.type
  → Validate specific payload (Zod)
  → Call Use Case (NOT Service directly)
  → Return envelope response
```

## Adding a New Provider

### 1. Create Shared Components (if first provider)

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

```typescript
// modules/webhooks/shared/webhook.logger.ts
import { logger } from '@/shared/infra/logger';

export interface WebhookLogContext {
  provider: string;
  eventType: string;
  eventId: string;
  requestId: string;
}

export function createWebhookLogger(ctx: WebhookLogContext) {
  return logger.child({
    webhook: true,
    ...ctx,
  });
}
```

### 2. Create Provider Schemas

```typescript
// modules/webhooks/<provider>/<provider>.schemas.ts
import { z } from 'zod';

// Base event schema
export const <Provider>EventSchema = z.object({
  id: z.string(),
  type: z.string(),
  data: z.object({
    object: z.record(z.unknown()),
  }),
});

export type <Provider>Event = z.infer<typeof <Provider>EventSchema>;

// Specific event schemas
export const <Provider>InvoicePaidSchema = z.object({
  id: z.string(),
  type: z.literal('invoice.paid'),
  data: z.object({
    object: z.object({
      id: z.string(),
      customer: z.string(),
      amount_paid: z.number(),
      // ... specific fields
    }),
  }),
});
```

### 3. Create Signature Validator

```typescript
// modules/webhooks/<provider>/<provider>.validator.ts
import { env } from '@/env';
import { WebhookVerificationError } from '../shared/webhook.errors';
// Import provider SDK

export function verify<Provider>Signature(
  rawBody: string,
  signature: string | null,
): <Provider>Event {
  if (!signature) {
    throw new WebhookVerificationError('<provider>');
  }

  try {
    // Use provider SDK to verify
    return providerSdk.webhooks.constructEvent(
      rawBody,
      signature,
      env.<PROVIDER>_WEBHOOK_SECRET,
    );
  } catch (err) {
    throw new WebhookVerificationError('<provider>');
  }
}
```

### 4. Create Handler Interface and Handlers

```typescript
// modules/webhooks/<provider>/handlers/handler.interface.ts
import type { Logger } from '@/shared/infra/logger';

export interface WebhookHandlerResult {
  skipped: boolean;
  reason?: string;
}

export interface IWebhookHandler {
  handle(rawEvent: unknown, log: Logger): Promise<WebhookHandlerResult>;
}
```

```typescript
// modules/webhooks/<provider>/handlers/<event>.handler.ts
import type { Logger } from '@/shared/infra/logger';
import type { I<Action>UseCase } from '@/modules/<module>/use-cases/<action>.use-case';
import type { I<Entity>Repository } from '@/modules/<module>/repositories/<entity>.repository';
import { <Provider><Event>Schema } from '../<provider>.schemas';
import { WebhookPayloadError } from '../../shared/webhook.errors';
import type { IWebhookHandler, WebhookHandlerResult } from './handler.interface';

export class <Event>Handler implements IWebhookHandler {
  constructor(
    private <action>UseCase: I<Action>UseCase,
    private <entity>Repository: I<Entity>Repository,
  ) {}

  async handle(rawEvent: unknown, log: Logger): Promise<WebhookHandlerResult> {
    // Validate payload
    const result = <Provider><Event>Schema.safeParse(rawEvent);
    if (!result.success) {
      throw new WebhookPayloadError('<provider>', {
        eventType: '<event>',
        issues: result.error.issues,
      });
    }

    const event = result.data;
    const externalId = event.data.object.id;

    // Idempotency check via domain
    const existing = await this.<entity>Repository.findByExternalId(externalId);
    if (existing) {
      return { skipped: true, reason: 'Already processed' };
    }

    log.info({ externalId }, 'Processing event');

    // Delegate to use case
    await this.<action>UseCase.execute({
      externalId,
      // ... map other fields
    });

    return { skipped: false };
  }
}
```

### 5. Create Handler Registry

```typescript
// modules/webhooks/<provider>/handlers/index.ts
import type { IWebhookHandler } from './handler.interface';
import { <Event>Handler } from './<event>.handler';
import { make<Action>UseCase } from '@/modules/<module>/factories';
import { make<Entity>Repository } from '@/modules/<module>/factories';

type <Provider>EventType = '<event.type>' | '<other.event>';

const handlers: Record<<Provider>EventType, () => IWebhookHandler> = {
  '<event.type>': () => new <Event>Handler(
    make<Action>UseCase(),
    make<Entity>Repository(),
  ),
};

export function get<Provider>Handler(eventType: string): IWebhookHandler | null {
  const factory = handlers[eventType as <Provider>EventType];
  return factory ? factory() : null;
}

export function isHandledEventType(eventType: string): boolean {
  return eventType in handlers;
}
```

### 6. Create Route Handler

```typescript
// app/api/webhooks/<provider>/route.ts
import { NextResponse } from 'next/server';
import { logger } from '@/shared/infra/logger';
import { wrapResponse } from '@/shared/utils/response';
import { verify<Provider>Signature } from '@/modules/webhooks/<provider>/<provider>.validator';
import { <Provider>EventSchema } from '@/modules/webhooks/<provider>/<provider>.schemas';
import { get<Provider>Handler, isHandledEventType } from '@/modules/webhooks/<provider>/handlers';
import { createWebhookLogger } from '@/modules/webhooks/shared/webhook.logger';
import {
  WebhookVerificationError,
  WebhookPayloadError,
} from '@/modules/webhooks/shared/webhook.errors';

export async function POST(req: Request) {
  const requestId = crypto.randomUUID();
  let log = logger.child({ requestId, provider: '<provider>' });

  try {
    const rawBody = await req.text();
    const signature = req.headers.get('<provider>-signature');

    // Verify signature
    const providerEvent = verify<Provider>Signature(rawBody, signature);

    // Parse base event
    const parseResult = <Provider>EventSchema.safeParse(providerEvent);
    if (!parseResult.success) {
      throw new WebhookPayloadError('<provider>', {
        issues: parseResult.error.issues,
      });
    }

    const event = parseResult.data;

    log = createWebhookLogger({
      provider: '<provider>',
      eventType: event.type,
      eventId: event.id,
      requestId,
    });

    log.info({ event: 'webhook.received' }, 'Webhook received');

    // Skip unhandled events
    if (!isHandledEventType(event.type)) {
      log.info({ event: 'webhook.skipped', reason: 'Unhandled event type' }, 'Webhook skipped');
      return NextResponse.json(
        wrapResponse({ received: true, eventId: event.id, processed: false }),
        { status: 200 },
      );
    }

    // Get and execute handler
    const handler = get<Provider>Handler(event.type);
    if (!handler) {
      return NextResponse.json(
        wrapResponse({ received: true, eventId: event.id, processed: false }),
        { status: 200 },
      );
    }

    const start = Date.now();
    const result = await handler.handle(providerEvent, log);
    const duration = Date.now() - start;

    if (result.skipped) {
      log.info({ event: 'webhook.skipped', reason: result.reason, duration }, 'Webhook skipped');
    } else {
      log.info({ event: 'webhook.processed', duration }, 'Webhook processed');
    }

    return NextResponse.json(
      wrapResponse({
        received: true,
        eventId: event.id,
        processed: !result.skipped,
      }),
      { status: 200 },
    );

  } catch (error) {
    if (error instanceof WebhookVerificationError) {
      log.warn({ event: 'webhook.verification_failed', err: error }, 'Verification failed');
      return NextResponse.json(
        { code: error.code, message: error.message, requestId },
        { status: 401 },
      );
    }

    if (error instanceof WebhookPayloadError) {
      log.warn({ event: 'webhook.validation_failed', err: error }, 'Validation failed');
      return NextResponse.json(
        { code: error.code, message: error.message, requestId, details: error.details },
        { status: 400 },
      );
    }

    log.error({ event: 'webhook.failed', err: error }, 'Webhook processing failed');
    return NextResponse.json(
      { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred', requestId },
      { status: 500 },
    );
  }
}
```

## Idempotency Pattern

Handle idempotency via domain logic, NOT a dedicated webhook table:

```typescript
// In handler
const existing = await this.paymentRepository.findByStripeInvoiceId(invoiceId);
if (existing) {
  return { skipped: true, reason: 'Payment already processed' };
}

// In handler for user events
const existing = await this.userRepository.findByClerkId(clerkUserId);
if (existing) {
  return { skipped: true, reason: 'User already exists' };
}
```

## Outbound Webhooks

For sending webhooks to external systems:

```typescript
// modules/webhooks/outbound/outbound.service.ts
import { logger } from '@/shared/infra/logger';

export interface OutboundWebhookPayload {
  event: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface IOutboundWebhookService {
  send(url: string, payload: OutboundWebhookPayload, secret: string): Promise<void>;
}

export class OutboundWebhookService implements IOutboundWebhookService {
  async send(url: string, payload: OutboundWebhookPayload, secret: string): Promise<void> {
    const body = JSON.stringify(payload);
    const signature = await this.sign(body, secret);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': signature,
        'X-Webhook-Timestamp': payload.timestamp,
      },
      body,
    });

    if (!response.ok) {
      logger.warn(
        {
          event: 'outbound_webhook.failed',
          url,
          status: response.status,
          eventType: payload.event,
        },
        'Outbound webhook failed',
      );
      throw new OutboundWebhookError(url, response.status);
    }

    logger.info(
      { event: 'outbound_webhook.sent', url, eventType: payload.event },
      'Outbound webhook sent',
    );
  }

  private async sign(body: string, secret: string): Promise<string> {
    const encoder = new TextEncoder();
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(secret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign'],
    );
    const signature = await crypto.subtle.sign('HMAC', key, encoder.encode(body));
    return Buffer.from(signature).toString('hex');
  }
}
```

### Webhook Subscriptions Schema

```typescript
// shared/infra/db/schema.ts
export const webhookSubscriptions = pgTable('webhook_subscriptions', {
  id: uuid('id').primaryKey().defaultRandom(),
  workspaceId: uuid('workspace_id').notNull().references(() => workspaces.id),
  url: text('url').notNull(),
  secret: text('secret').notNull(),
  events: text('events').array().notNull(), // ['entity.created', 'entity.updated']
  isActive: boolean('is_active').default(true).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});
```

### Dispatching Outbound Webhooks

```typescript
// In a use case or service, after business logic
async execute(input: CreateEntityDTO): Promise<Entity> {
  const entity = await this.transactionManager.run(async (tx) => {
    return this.entityService.create(input, { tx });
  });

  // After transaction commits, dispatch webhooks
  await this.dispatchWebhooks('entity.created', entity);

  return entity;
}

private async dispatchWebhooks(event: string, data: unknown): Promise<void> {
  const subscriptions = await this.webhookSubscriptionRepository.findByEvent(
    event,
    data.workspaceId,
  );

  const payload: OutboundWebhookPayload = {
    event,
    data,
    timestamp: new Date().toISOString(),
  };

  // Fire and forget (or queue for retry)
  await Promise.allSettled(
    subscriptions.map((sub) =>
      this.outboundWebhookService.send(sub.url, payload, sub.secret),
    ),
  );
}
```

## Checklist

### Inbound Webhooks
- [ ] Shared components in `modules/webhooks/shared/`
- [ ] Provider schemas with Zod validation
- [ ] Signature validator using provider SDK
- [ ] Handler interface implemented
- [ ] Handler registry maps event types
- [ ] Handlers delegate to Use Cases (not Services)
- [ ] Idempotency checked via domain queries
- [ ] Route verifies signature first
- [ ] Route returns standard envelope response
- [ ] All events logged with consistent context

### Outbound Webhooks
- [ ] Webhook subscriptions table created
- [ ] Outbound service with HMAC signing
- [ ] Subscription management endpoints
- [ ] Webhooks dispatched after transaction commits
- [ ] Failed webhooks logged for monitoring

See [references/provider-examples.md](references/provider-examples.md) for Stripe and Clerk examples.
