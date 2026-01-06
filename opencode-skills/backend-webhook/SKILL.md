---
name: backend-webhook
description: Implement inbound webhooks with signature verification, Zod validation, and idempotency for Stripe, Clerk, and other providers in Next.js projects
---

# Webhook Implementation

Use this skill when handling webhooks from external services (Stripe, Clerk, GitHub, etc.).

## Architecture

```
src/modules/webhooks/
├── <provider>/
│   ├── <provider>.route.ts       # POST /api/webhooks/<provider>
│   ├── <provider>.validator.ts   # Signature verification
│   ├── <provider>.schemas.ts     # Zod schemas per event
│   └── handlers/
│       ├── index.ts              # Handler registry
│       └── <event>.handler.ts    # Per-event handlers
└── shared/
    ├── webhook.schemas.ts        # Response schema
    ├── webhook.errors.ts         # Webhook errors
    └── webhook.logger.ts         # Logger factory
```

## Webhook Flow

```
Route → Verify Signature → Parse Event → Route by Type → Validate Payload → Call Use Case → Return Response
```

## Adding a New Provider

### 1. Shared Components (first time only)

```typescript
// modules/webhooks/shared/webhook.errors.ts
import { AuthenticationError, ValidationError } from '@/shared/kernel/errors'

export class WebhookVerificationError extends AuthenticationError {
  readonly code = 'WEBHOOK_VERIFICATION_FAILED'
  constructor(provider: string) {
    super(`Webhook signature verification failed for ${provider}`)
  }
}

export class WebhookPayloadError extends ValidationError {
  readonly code = 'WEBHOOK_PAYLOAD_INVALID'
  constructor(provider: string, details?: Record<string, unknown>) {
    super(`Invalid webhook payload from ${provider}`, details)
  }
}
```

```typescript
// modules/webhooks/shared/webhook.logger.ts
import { logger } from '@/shared/infra/logger'

export function createWebhookLogger(ctx: {
  provider: string
  eventType: string
  eventId: string
  requestId: string
}) {
  return logger.child({ webhook: true, ...ctx })
}
```

### 2. Provider Schemas

```typescript
// modules/webhooks/<provider>/<provider>.schemas.ts
import { z } from 'zod'

// Base event schema
export const ProviderEventSchema = z.object({
  id: z.string(),
  type: z.string(),
  data: z.object({ object: z.record(z.unknown()) }),
})

// Specific event schema
export const ProviderInvoicePaidSchema = z.object({
  id: z.string(),
  type: z.literal('invoice.paid'),
  data: z.object({
    object: z.object({
      id: z.string(),
      customer: z.string(),
      amount_paid: z.number(),
    }),
  }),
})
```

### 3. Signature Validator

```typescript
// modules/webhooks/<provider>/<provider>.validator.ts
import { env } from '@/env'
import { WebhookVerificationError } from '../shared/webhook.errors'

export function verifyProviderSignature(
  rawBody: string,
  signature: string | null
): ProviderEvent {
  if (!signature) {
    throw new WebhookVerificationError('provider')
  }

  try {
    // Use provider SDK to verify
    return providerSdk.webhooks.constructEvent(
      rawBody,
      signature,
      env.PROVIDER_WEBHOOK_SECRET
    )
  } catch {
    throw new WebhookVerificationError('provider')
  }
}
```

### 4. Handler

```typescript
// modules/webhooks/<provider>/handlers/<event>.handler.ts
import type { Logger } from '@/shared/infra/logger'
import { ProviderInvoicePaidSchema } from '../<provider>.schemas'
import { WebhookPayloadError } from '../../shared/webhook.errors'

export interface WebhookHandlerResult {
  skipped: boolean
  reason?: string
}

export interface IWebhookHandler {
  handle(rawEvent: unknown, log: Logger): Promise<WebhookHandlerResult>
}

export class InvoicePaidHandler implements IWebhookHandler {
  constructor(
    private processPaymentUseCase: IProcessPaymentUseCase,
    private paymentRepository: IPaymentRepository
  ) {}

  async handle(rawEvent: unknown, log: Logger): Promise<WebhookHandlerResult> {
    // Validate
    const result = ProviderInvoicePaidSchema.safeParse(rawEvent)
    if (!result.success) {
      throw new WebhookPayloadError('provider', {
        eventType: 'invoice.paid',
        issues: result.error.issues,
      })
    }

    const event = result.data
    const invoiceId = event.data.object.id

    // Idempotency check
    const existing = await this.paymentRepository.findByExternalId(invoiceId)
    if (existing) {
      return { skipped: true, reason: 'Already processed' }
    }

    log.info({ invoiceId }, 'Processing payment')

    // Delegate to use case
    await this.processPaymentUseCase.execute({
      externalId: invoiceId,
      amount: event.data.object.amount_paid,
      customerId: event.data.object.customer,
    })

    return { skipped: false }
  }
}
```

### 5. Handler Registry

```typescript
// modules/webhooks/<provider>/handlers/index.ts
import { InvoicePaidHandler } from './invoice-paid.handler'
import { makeProcessPaymentUseCase, makePaymentRepository } from '@/modules/payment/factories'

type EventType = 'invoice.paid' | 'customer.subscription.updated'

const handlers: Record<EventType, () => IWebhookHandler> = {
  'invoice.paid': () =>
    new InvoicePaidHandler(makeProcessPaymentUseCase(), makePaymentRepository()),
}

export function getHandler(eventType: string): IWebhookHandler | null {
  const factory = handlers[eventType as EventType]
  return factory ? factory() : null
}

export function isHandledEventType(eventType: string): boolean {
  return eventType in handlers
}
```

### 6. Route Handler

```typescript
// app/api/webhooks/<provider>/route.ts
import { NextResponse } from 'next/server'
import { logger } from '@/shared/infra/logger'
import { wrapResponse } from '@/shared/utils/response'
import { verifyProviderSignature } from '@/modules/webhooks/<provider>/<provider>.validator'
import { ProviderEventSchema } from '@/modules/webhooks/<provider>/<provider>.schemas'
import { getHandler, isHandledEventType } from '@/modules/webhooks/<provider>/handlers'
import { createWebhookLogger } from '@/modules/webhooks/shared/webhook.logger'
import {
  WebhookVerificationError,
  WebhookPayloadError,
} from '@/modules/webhooks/shared/webhook.errors'

export async function POST(req: Request) {
  const requestId = crypto.randomUUID()
  let log = logger.child({ requestId, provider: 'provider' })

  try {
    const rawBody = await req.text()
    const signature = req.headers.get('provider-signature')

    // Verify signature
    const providerEvent = verifyProviderSignature(rawBody, signature)

    // Parse base event
    const parseResult = ProviderEventSchema.safeParse(providerEvent)
    if (!parseResult.success) {
      throw new WebhookPayloadError('provider', { issues: parseResult.error.issues })
    }

    const event = parseResult.data

    log = createWebhookLogger({
      provider: 'provider',
      eventType: event.type,
      eventId: event.id,
      requestId,
    })

    log.info({ event: 'webhook.received' }, 'Webhook received')

    // Skip unhandled events
    if (!isHandledEventType(event.type)) {
      log.info({ event: 'webhook.skipped', reason: 'Unhandled event type' }, 'Skipped')
      return NextResponse.json(
        wrapResponse({ received: true, eventId: event.id, processed: false }),
        { status: 200 }
      )
    }

    // Execute handler
    const handler = getHandler(event.type)
    if (!handler) {
      return NextResponse.json(
        wrapResponse({ received: true, eventId: event.id, processed: false }),
        { status: 200 }
      )
    }

    const start = Date.now()
    const result = await handler.handle(providerEvent, log)
    const duration = Date.now() - start

    log.info(
      { event: result.skipped ? 'webhook.skipped' : 'webhook.processed', duration },
      result.skipped ? 'Skipped' : 'Processed'
    )

    return NextResponse.json(
      wrapResponse({ received: true, eventId: event.id, processed: !result.skipped }),
      { status: 200 }
    )
  } catch (error) {
    if (error instanceof WebhookVerificationError) {
      log.warn({ event: 'webhook.verification_failed' }, 'Verification failed')
      return NextResponse.json(
        { code: error.code, message: error.message, requestId },
        { status: 401 }
      )
    }

    if (error instanceof WebhookPayloadError) {
      log.warn({ event: 'webhook.validation_failed' }, 'Validation failed')
      return NextResponse.json(
        { code: error.code, message: error.message, requestId },
        { status: 400 }
      )
    }

    log.error({ event: 'webhook.failed', err: error }, 'Processing failed')
    return NextResponse.json(
      { code: 'INTERNAL_ERROR', message: 'Unexpected error', requestId },
      { status: 500 }
    )
  }
}
```

## Idempotency Pattern

Check via domain logic, NOT a webhook events table:

```typescript
// Payment webhook
const existing = await this.paymentRepository.findByStripeInvoiceId(invoiceId)
if (existing) return { skipped: true, reason: 'Payment already processed' }

// User webhook  
const existing = await this.userRepository.findByClerkId(clerkUserId)
if (existing) return { skipped: true, reason: 'User already exists' }
```

## Checklist

- [ ] Shared components in `modules/webhooks/shared/`
- [ ] Provider schemas with Zod validation
- [ ] Signature validator using provider SDK
- [ ] Handler implements `IWebhookHandler` interface
- [ ] Handler registry maps event types
- [ ] Handlers delegate to Use Cases (not Services)
- [ ] Idempotency checked via domain queries
- [ ] Route verifies signature first
- [ ] Route returns standard envelope response
- [ ] All events logged with consistent context
