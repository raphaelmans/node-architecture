# Product Analytics

> Core standard for recording user and business behavior without coupling application code to analytics vendors.

## Boundary

Product analytics is not server logging.

| Server logs | Product analytics |
| --- | --- |
| Diagnose failures and runtime behavior | Understand user and business behavior |
| Structured backend through `AppLogger` | `ProductAnalytics` port |
| `requestId`, `traceId`, error details | `userId`, account ID, typed event properties |
| Operational retention/access policy | Product/privacy retention and consent policy |

Examples of product analytics events include `user_signed_up`, `feature_used`, and `checkout_completed`. Examples of operational logs include `Request completed`, `Webhook signature rejected`, and `Database connection failed`.

Audit records are a third concern. Security- or compliance-relevant actions must use a durable audit trail, not ordinary logs or analytics.

## Port and Typed Events

Application code depends on a vendor-neutral port:

```typescript
// shared/kernel/product-analytics.ts

export type ProductEvent =
  | {
      name: "user_created";
      userId: string;
      properties: { signupMethod: "email" | "oauth" };
    }
  | {
      name: "checkout_completed";
      userId: string;
      properties: { orderId: string; amount: number; currency: string };
    };

export interface ProductAnalytics {
  track(event: ProductEvent): Promise<void>;
}
```

Prefer an explicit discriminated union or schema registry over arbitrary event names and `Record<string, unknown>`. Typed events prevent silent drift between producers and analytics destinations.

## Multiple Destinations

Use Adapter plus Composite patterns when the same event must reach multiple vendors:

```text
ProductAnalytics
      |
      v
CompositeProductAnalytics
   +-- MixpanelAnalytics
   +-- GoogleAnalytics
```

```typescript
import { APP_ATTRIBUTES } from "@/shared/infra/observability/attributes";

export class CompositeProductAnalytics implements ProductAnalytics {
  constructor(
    private readonly destinations: Array<{
      name: string;
      adapter: ProductAnalytics;
    }>,
    private readonly logger: AppLogger,
  ) {}

  async track(event: ProductEvent): Promise<void> {
    const results = await Promise.allSettled(
      this.destinations.map(({ adapter }) => adapter.track(event)),
    );

    results.forEach((result, index) => {
      if (result.status === "rejected") {
        this.logger.warn(
          {
            err: result.reason,
            "otel.event.name": "product_analytics.delivery_failed",
            [APP_ATTRIBUTES.productEventName]: event.name,
            [APP_ATTRIBUTES.analyticsDestination]:
              this.destinations[index]?.name ?? "unknown",
          },
          "Product analytics delivery failed",
        );
      }
    });
  }
}
```

Vendor adapters own vendor payload mapping, credentials, batching, and API behavior. Application services must not import Mixpanel or Google Analytics SDKs directly.

## Dependency Injection

Inject logging and analytics as separate dependencies. Do not create a single `TelemetryService` with unrelated logging, analytics, and tracing methods.

```typescript
export class CreateUserUseCase {
  constructor(
    private readonly userService: IUserService,
    private readonly logger: AppLogger,
    private readonly analytics: ProductAnalytics,
  ) {}
}
```

This follows interface segregation: a class receives only the capabilities it needs, and tests can replace each independently.

## Delivery Semantics

Choose delivery based on business importance.

### Best-effort

Use direct post-commit delivery only when loss is acceptable. Catch failures so analytics cannot fail the business operation. Be careful in serverless runtimes: unawaited work may be terminated after the response.

### Reliable

For important state-change analytics, use the outbox pattern:

```text
Use case
  -> write domain state + analytics event in the same transaction
  -> commit
  -> background dispatcher
  -> CompositeProductAnalytics
       +-- Mixpanel
       +-- Google Analytics
```

The outbox stores delivery intent, not a vendor-specific payload. The dispatcher maps the canonical event to each destination and applies retry/idempotency policy. Follow [Async Jobs + Outbox](./async-jobs-outbox.md).

Analytics delivery failure must not roll back an already-committed domain operation.

## Factory Example

```typescript
// shared/infra/analytics/index.ts

export const productAnalytics: ProductAnalytics = new CompositeProductAnalytics(
  [
    {
      name: "mixpanel",
      adapter: new MixpanelAnalytics(mixpanelClient),
    },
    {
      name: "google-analytics",
      adapter: new GoogleAnalytics(googleAnalyticsClient),
    },
  ],
  appLogger,
);

// modules/user/factories/create-user.factory.ts

export function makeCreateUserUseCase(): CreateUserUseCase {
  return new CreateUserUseCase(
    makeUserService(),
    getContainer().appLogger,
    getContainer().productAnalytics,
  );
}

export function makeCreateUserController(): ICreateUserController {
  return new CreateUserController(
    makeCreateUserUseCase(),
  );
}
```

## Use-Case Example

```typescript
import { APP_ATTRIBUTES } from "@/shared/infra/observability/attributes";

async execute(command: CreateUserCommand): Promise<User> {
  this.logger.info({}, "Creating user");

  const user = await this.userService.create(command);

  this.logger.info(
    {
      "otel.event.name": "user.created",
      "code.function.name": "CreateUserUseCase.execute",
      "user.id": user.id,
    },
    "User created",
  );

  try {
    await this.analytics.track({
      name: "user_created",
      userId: user.id,
      properties: { signupMethod: command.signupMethod },
    });
  } catch (error) {
    this.logger.warn(
      {
        err: error,
        "otel.event.name": "product_analytics.delivery_failed",
        "user.id": user.id,
        [APP_ATTRIBUTES.productEventName]: "user_created",
      },
      "Product analytics delivery failed",
    );
  }

  return user;
}
```

If `user_created` must be guaranteed, replace the direct `track` call with a transactional outbox enqueue.

## Privacy and Data Rules

- Collect only fields needed for an explicit product question.
- Do not send passwords, tokens, authorization headers, full request bodies, or provider secrets.
- Treat user identifiers and event properties according to the applicable consent and retention policy.
- Keep vendor credentials in infrastructure configuration.
- Version or migrate event schemas deliberately; do not silently reuse an event name with new semantics.
- Prevent duplicate events through stable event IDs or idempotency keys where supported.

## Testing

- Unit tests inject a spy `ProductAnalytics` and assert the typed event.
- Composite tests verify all configured adapters receive the event.
- Failure tests verify one vendor failure does not prevent other destinations or fail the business operation.
- Outbox integration tests verify domain state and event intent commit or roll back together.
- Contract tests verify vendor payload mapping without exposing vendor types to application code.

## Checklist

- [ ] `ProductAnalytics` is separate from `AppLogger`
- [ ] Event names and properties are typed or schema-validated
- [ ] Vendor SDKs are confined to infrastructure adapters
- [ ] Multiple destinations use a composite adapter
- [ ] Analytics failures do not fail committed business operations
- [ ] Important events use transactional outbox delivery
- [ ] Consent, PII, retention, and deletion requirements are defined
- [ ] Tests use analytics spies/fakes rather than live vendors

## References

- [Observability](./observability.md)
- [Logging](./logging.md)
- [Event-Driven Patterns](./event-patterns.md)
- [Async Jobs + Outbox](./async-jobs-outbox.md)
