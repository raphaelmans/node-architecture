# Webhook Provider Examples

## Stripe Implementation

### Folder Structure

```
modules/webhooks/stripe/
├── stripe.route.ts           # POST /api/webhooks/stripe
├── stripe.validator.ts       # Signature verification
├── stripe.schemas.ts         # Zod schemas per event type
└── handlers/
    ├── index.ts              # Handler registry
    ├── invoice-paid.handler.ts
    └── subscription-updated.handler.ts
```

### Zod Schemas

```typescript
// modules/webhooks/stripe/stripe.schemas.ts
import { z } from 'zod'

/**
 * Base Stripe event schema for initial parsing and routing.
 */
export const StripeEventSchema = z.object({
  id: z.string(),
  type: z.string(),
  data: z.object({
    object: z.record(z.unknown()),
  }),
})

export type StripeEvent = z.infer<typeof StripeEventSchema>

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
})

export type StripeInvoicePaidEvent = z.infer<typeof StripeInvoicePaidSchema>

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
      status: z.enum([
        'active',
        'canceled',
        'incomplete',
        'past_due',
        'trialing',
        'unpaid',
      ]),
      current_period_start: z.number(),
      current_period_end: z.number(),
    }),
  }),
})

export type StripeSubscriptionUpdatedEvent = z.infer<
  typeof StripeSubscriptionUpdatedSchema
>
```

### Signature Validator

```typescript
// modules/webhooks/stripe/stripe.validator.ts
import Stripe from 'stripe'
import { env } from '@/env'
import { WebhookVerificationError } from '../shared/webhook.errors'

const stripe = new Stripe(env.STRIPE_SECRET_KEY)

/**
 * Verifies Stripe webhook signature and returns parsed event.
 */
export function verifyStripeSignature(
  rawBody: string,
  signature: string | null
): Stripe.Event {
  if (!signature) {
    throw new WebhookVerificationError('stripe')
  }

  try {
    return stripe.webhooks.constructEvent(
      rawBody,
      signature,
      env.STRIPE_WEBHOOK_SECRET
    )
  } catch (err) {
    throw new WebhookVerificationError('stripe')
  }
}
```

### Handler Implementation

```typescript
// modules/webhooks/stripe/handlers/invoice-paid.handler.ts
import type { Logger } from '@/shared/infra/logger'
import type { IProcessPaymentUseCase } from '@/modules/payment/use-cases/process-payment.use-case.interface'
import type { IPaymentRepository } from '@/modules/payment/repositories/payment.repository.interface'
import { StripeInvoicePaidSchema } from '../stripe.schemas'
import { WebhookPayloadError } from '../../shared/webhook.errors'
import type { IWebhookHandler, WebhookHandlerResult } from './handler.interface'

export class InvoicePaidHandler implements IWebhookHandler {
  constructor(
    private processPaymentUseCase: IProcessPaymentUseCase,
    private paymentRepository: IPaymentRepository
  ) {}

  async handle(rawEvent: unknown, log: Logger): Promise<WebhookHandlerResult> {
    // Validate payload
    const result = StripeInvoicePaidSchema.safeParse(rawEvent)
    if (!result.success) {
      throw new WebhookPayloadError('stripe', {
        eventType: 'invoice.paid',
        issues: result.error.issues,
      })
    }

    const event = result.data
    const invoiceId = event.data.object.id

    // Idempotency check via domain
    const existing = await this.paymentRepository.findByStripeInvoiceId(invoiceId)
    if (existing) {
      return { skipped: true, reason: 'Payment already processed' }
    }

    log.info(
      {
        invoiceId,
        amount: event.data.object.amount_paid,
        currency: event.data.object.currency,
      },
      'Processing payment'
    )

    // Delegate to use case
    await this.processPaymentUseCase.execute({
      stripeInvoiceId: invoiceId,
      amount: event.data.object.amount_paid,
      currency: event.data.object.currency,
      customerId: event.data.object.customer,
    })

    return { skipped: false }
  }
}
```

### Handler Registry

```typescript
// modules/webhooks/stripe/handlers/index.ts
import type { IWebhookHandler } from './handler.interface'
import { InvoicePaidHandler } from './invoice-paid.handler'
import { SubscriptionUpdatedHandler } from './subscription-updated.handler'
import { makeProcessPaymentUseCase } from '@/modules/payment/factories/payment.factory'
import { makeUpdateSubscriptionUseCase } from '@/modules/subscription/factories/subscription.factory'
import { makePaymentRepository } from '@/modules/payment/factories/payment.factory'

type StripeEventType = 'invoice.paid' | 'customer.subscription.updated'

const handlers: Record<StripeEventType, () => IWebhookHandler> = {
  'invoice.paid': () =>
    new InvoicePaidHandler(makeProcessPaymentUseCase(), makePaymentRepository()),
  'customer.subscription.updated': () =>
    new SubscriptionUpdatedHandler(makeUpdateSubscriptionUseCase()),
}

export function getStripeHandler(eventType: string): IWebhookHandler | null {
  const factory = handlers[eventType as StripeEventType]
  return factory ? factory() : null
}

export function isHandledEventType(eventType: string): boolean {
  return eventType in handlers
}
```

---

## Clerk Implementation

### Folder Structure

```
modules/webhooks/clerk/
├── clerk.route.ts
├── clerk.validator.ts
├── clerk.schemas.ts
└── handlers/
    ├── index.ts
    └── user-created.handler.ts
```

### Zod Schemas

```typescript
// modules/webhooks/clerk/clerk.schemas.ts
import { z } from 'zod'

/**
 * Base Clerk event schema.
 */
export const ClerkEventSchema = z.object({
  type: z.string(),
  data: z.record(z.unknown()),
  object: z.literal('event'),
})

export type ClerkEvent = z.infer<typeof ClerkEventSchema>

/**
 * user.created event schema.
 */
export const ClerkUserCreatedSchema = z.object({
  type: z.literal('user.created'),
  data: z.object({
    id: z.string(),
    email_addresses: z.array(
      z.object({
        id: z.string(),
        email_address: z.string(),
      })
    ),
    first_name: z.string().nullable(),
    last_name: z.string().nullable(),
    created_at: z.number(),
  }),
  object: z.literal('event'),
})

export type ClerkUserCreatedEvent = z.infer<typeof ClerkUserCreatedSchema>
```

### Signature Validator (Svix)

```typescript
// modules/webhooks/clerk/clerk.validator.ts
import { Webhook } from 'svix'
import { env } from '@/env'
import { WebhookVerificationError } from '../shared/webhook.errors'

/**
 * Verifies Clerk webhook signature using Svix.
 */
export function verifyClerkSignature(
  rawBody: string,
  headers: Headers
): unknown {
  const svixId = headers.get('svix-id')
  const svixTimestamp = headers.get('svix-timestamp')
  const svixSignature = headers.get('svix-signature')

  if (!svixId || !svixTimestamp || !svixSignature) {
    throw new WebhookVerificationError('clerk')
  }

  const wh = new Webhook(env.CLERK_WEBHOOK_SECRET)

  try {
    return wh.verify(rawBody, {
      'svix-id': svixId,
      'svix-timestamp': svixTimestamp,
      'svix-signature': svixSignature,
    })
  } catch (err) {
    throw new WebhookVerificationError('clerk')
  }
}
```

### User Created Handler

```typescript
// modules/webhooks/clerk/handlers/user-created.handler.ts
import type { Logger } from '@/shared/infra/logger'
import type { ICreateUserUseCase } from '@/modules/user/use-cases/create-user.use-case.interface'
import type { IUserRepository } from '@/modules/user/repositories/user.repository.interface'
import { ClerkUserCreatedSchema } from '../clerk.schemas'
import { WebhookPayloadError } from '../../shared/webhook.errors'
import type { IWebhookHandler, WebhookHandlerResult } from './handler.interface'

export class UserCreatedHandler implements IWebhookHandler {
  constructor(
    private createUserUseCase: ICreateUserUseCase,
    private userRepository: IUserRepository
  ) {}

  async handle(rawEvent: unknown, log: Logger): Promise<WebhookHandlerResult> {
    // Validate payload
    const result = ClerkUserCreatedSchema.safeParse(rawEvent)
    if (!result.success) {
      throw new WebhookPayloadError('clerk', {
        eventType: 'user.created',
        issues: result.error.issues,
      })
    }

    const event = result.data
    const clerkUserId = event.data.id

    // Idempotency check
    const existing = await this.userRepository.findByClerkId(clerkUserId)
    if (existing) {
      return { skipped: true, reason: 'User already exists' }
    }

    const primaryEmail = event.data.email_addresses[0]?.email_address

    log.info(
      { clerkUserId, email: primaryEmail },
      'Creating user from Clerk webhook'
    )

    await this.createUserUseCase.execute({
      clerkId: clerkUserId,
      email: primaryEmail,
      firstName: event.data.first_name,
      lastName: event.data.last_name,
    })

    return { skipped: false }
  }
}
```

---

## Shared Components

### Handler Interface

```typescript
// modules/webhooks/shared/handler.interface.ts
import type { Logger } from '@/shared/infra/logger'

export interface WebhookHandlerResult {
  skipped: boolean
  reason?: string
}

export interface IWebhookHandler {
  handle(rawEvent: unknown, log: Logger): Promise<WebhookHandlerResult>
}
```

### Webhook Errors

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

export class WebhookHandlerNotFoundError extends ValidationError {
  readonly code = 'WEBHOOK_HANDLER_NOT_FOUND'

  constructor(provider: string, eventType: string) {
    super(`No handler registered for ${provider} event: ${eventType}`)
  }
}
```

### Webhook Logger

```typescript
// modules/webhooks/shared/webhook.logger.ts
import { logger } from '@/shared/infra/logger'

export interface WebhookLogContext {
  provider: string
  eventType: string
  eventId: string
  requestId: string
}

export function createWebhookLogger(ctx: WebhookLogContext) {
  return logger.child({
    webhook: true,
    provider: ctx.provider,
    eventType: ctx.eventType,
    eventId: ctx.eventId,
    requestId: ctx.requestId,
  })
}
```

### Response Schema

```typescript
// modules/webhooks/shared/webhook.schemas.ts
import { z } from 'zod'

export const WebhookResponseSchema = z.object({
  data: z.object({
    received: z.literal(true),
    eventId: z.string(),
    processed: z.boolean(),
  }),
})

export type WebhookResponse = z.infer<typeof WebhookResponseSchema>
```

---

## Route Handler Template

```typescript
// modules/webhooks/<provider>/<provider>.route.ts
// Location: app/api/webhooks/<provider>/route.ts

import { NextResponse } from 'next/server'
import { logger } from '@/shared/infra/logger'
import { wrapResponse } from '@/shared/utils/response'
import { verify<Provider>Signature } from './<provider>.validator'
import { <Provider>EventSchema } from './<provider>.schemas'
import { get<Provider>Handler, isHandledEventType } from './handlers'
import { createWebhookLogger } from '../shared/webhook.logger'
import {
  WebhookVerificationError,
  WebhookPayloadError,
  WebhookHandlerNotFoundError,
} from '../shared/webhook.errors'

export async function POST(req: Request) {
  const requestId = crypto.randomUUID()
  let log = logger.child({ requestId, provider: '<provider>' })

  try {
    // 1. Get raw body and signature
    const rawBody = await req.text()
    const signature = req.headers.get('<provider>-signature')

    // 2. Verify signature
    const providerEvent = verify<Provider>Signature(rawBody, signature)

    // 3. Parse base event with Zod
    const parseResult = <Provider>EventSchema.safeParse(providerEvent)
    if (!parseResult.success) {
      throw new WebhookPayloadError('<provider>', {
        issues: parseResult.error.issues,
      })
    }

    const event = parseResult.data

    // 4. Create webhook-specific logger
    log = createWebhookLogger({
      provider: '<provider>',
      eventType: event.type,
      eventId: event.id,
      requestId,
    })

    log.info({ event: 'webhook.received' }, 'Webhook received')

    // 5. Check if we handle this event type
    if (!isHandledEventType(event.type)) {
      log.info(
        { event: 'webhook.skipped', reason: 'Unhandled event type' },
        'Webhook skipped'
      )
      return NextResponse.json(
        wrapResponse({
          received: true,
          eventId: event.id,
          processed: false,
        }),
        { status: 200 }
      )
    }

    // 6. Get and execute handler
    const handler = get<Provider>Handler(event.type)
    if (!handler) {
      throw new WebhookHandlerNotFoundError('<provider>', event.type)
    }

    const start = Date.now()
    const result = await handler.handle(providerEvent, log)
    const duration = Date.now() - start

    // 7. Log outcome
    if (result.skipped) {
      log.info(
        { event: 'webhook.skipped', reason: result.reason, duration },
        'Webhook skipped'
      )
    } else {
      log.info({ event: 'webhook.processed', duration }, 'Webhook processed')
    }

    // 8. Return success response
    return NextResponse.json(
      wrapResponse({
        received: true,
        eventId: event.id,
        processed: !result.skipped,
      }),
      { status: 200 }
    )
  } catch (error) {
    // Handle known errors
    if (error instanceof WebhookVerificationError) {
      log.warn(
        { event: 'webhook.verification_failed', err: error },
        'Webhook signature verification failed'
      )
      return NextResponse.json(
        { code: error.code, message: error.message, requestId },
        { status: 401 }
      )
    }

    if (error instanceof WebhookPayloadError) {
      log.warn(
        { event: 'webhook.validation_failed', err: error, details: error.details },
        'Webhook validation failed'
      )
      return NextResponse.json(
        { code: error.code, message: error.message, requestId, details: error.details },
        { status: 400 }
      )
    }

    // Unknown error
    log.error({ event: 'webhook.failed', err: error }, 'Webhook processing failed')
    return NextResponse.json(
      { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred', requestId },
      { status: 500 }
    )
  }
}
```
