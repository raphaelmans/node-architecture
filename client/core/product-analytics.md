# Client Product Analytics

> Core standard for typed user/business events without coupling feature code to analytics vendors.

## Core Decision

Product analytics is separate from operational logging.

| Product analytics | Operational logging |
| --- | --- |
| Understand user and business behavior | Debug runtime behavior and failures |
| Typed product event registry | OpenTelemetry-shaped log records |
| Consent and identity lifecycle | Correlation, redaction, severity, sampling |
| Analytics destination adapter(s) | `debug`, Pino/server logs, Sentry |

Examples:

- Product event: `profile_updated`, `checkout_completed`, `feature_used`
- Operational event: `profile.update.failed`, `http.client.request.completed`

Do not route log records to analytics vendors or use analytics events as error logs.

## Contract

Prefer a discriminated union or schema registry over arbitrary event names and properties.

```ts
// src/common/analytics/types.ts
export type ProductEvent =
  | {
      name: "profile_created";
      properties: {
        source: "settings" | "onboarding";
      };
    }
  | {
      name: "profile_updated";
      properties: {
        source: "settings" | "onboarding";
      };
    }
  | {
      name: "checkout_completed";
      properties: {
        plan: "starter" | "pro";
        currency: string;
      };
    };

export interface ProductAnalytics {
  track(event: ProductEvent): void;
  identify(actor: {
    userId: string;
    accountId?: string;
  }): void;
  reset(): void;
}
```

The port is synchronous from the caller's perspective. Adapters own batching/delivery and swallow/report delivery failures so product analytics never blocks submit, navigation, or a committed business operation.

## Ownership

| Event | Owner |
| --- | --- |
| Successful client mutation outcome | Mutation hook or feature workflow that owns the action |
| Page/screen viewed | Route/screen integration |
| UI-only interaction such as dialog opened | Business component or feature interaction hook |
| Durable financial/compliance/business fact | Server-side analytics/outbox, not browser-only analytics |

Presentation-only components should normally receive callbacks and remain unaware of the analytics vendor.

Do not add a controller layer solely for analytics. Use the existing client layers; introduce a feature workflow/action only when the UX orchestration already justifies it.

## Create Data Flow

```text
CreateForm.onSubmit
  -> useMutCreate.mutateAsync
  -> FeatureApi.create
  -> ClientApi.post
  <- successful parsed model
  +-> ProductAnalytics.track("entity_created")
  +-> cache update/invalidation
  -> toast/navigation
```

Example:

```ts
export function createProfileMutation(deps: {
  profileApi: IProfileApi;
  cache: FeatureQueryCache;
  analytics: ProductAnalytics;
}) {
  return defineMutation({
    execute: (input: CreateProfileInput) => deps.profileApi.create(input),
    onSuccess: (profile, input) => {
      deps.analytics.track({
        name: "profile_created",
        properties: { source: input.source },
      });

      deps.cache.set(profileKeys.detail(profile.id), profile);
    },
  });
}
```

Emit after the meaningful operation succeeds. An attempted click is a different event from a completed business action and must have a different name/definition.

## Identity and Consent

- Gate analytics delivery through the adapter's consent policy.
- Call `identify` after authenticated identity becomes available.
- Call `reset` on logout or account/session reset.
- Keep anonymous/session identifiers provider-owned when possible.
- Use stable internal IDs only when approved; do not send email or other PII as a default identifier.
- Consent changes must affect future delivery without changing feature code.

Logging context and analytics identity may originate from the same authenticated session, but they remain separate runtime state and separate ports.

## Delivery and Adapters

```text
ProductAnalytics port
        |
        v
consent -> validation -> safe common context
        |
        v
adapter or composite adapter
        |
        +-- analytics destination A
        +-- analytics destination B (optional)
```

Adapters own:

- vendor SDK imports and credentials/configuration;
- event/property mapping;
- consent gating;
- batching, retries, and delivery policy;
- identity/session lifecycle; and
- non-fatal failure reporting through `AppLogger`.

Avoid analytics fan-out in feature code.

## Runtime Placement

```text
src/common/analytics/
  types.ts
  analytics.ts
  factory.ts             # createProductAnalytics
  consent.ts
  adapters/
    noop.ts
    debug.ts
    <vendor>.ts
    composite.ts          # only when multiple destinations are required
```

The debug analytics adapter is useful in development, but its output is still a product event and must not be confused with operational `AppLogger` records.

The composition root calls `createProductAnalytics` once for the browser application. Feature modules receive the `ProductAnalytics` port; they do not construct or cache vendor instances.

## Naming and Schema Rules

- Use one stable naming convention; this guide uses past-tense `snake_case` product events.
- Define what occurrence each event represents.
- Use bounded enums instead of arbitrary strings where possible.
- Never place dynamic identifiers in event names.
- Version intentionally breaking event schemas rather than silently changing meaning.
- Do not include raw form data, transport errors, stack traces, or sensitive payloads.

## Testing

Use a spy or fake analytics port:

```ts
const analytics = createAnalyticsSpy();

expect(analytics.track).toHaveBeenCalledWith({
  name: "profile_created",
  properties: { source: "settings" },
});
```

Test:

- success emits the intended event once;
- failure does not emit a completion event;
- analytics delivery failure does not fail the workflow;
- consent suppresses delivery;
- identify/reset lifecycle is correct; and
- no live analytics vendor is called in unit tests.

## Checklist

- [ ] `ProductAnalytics` is separate from `AppLogger`
- [ ] Events are typed through a union or schema registry
- [ ] Completion events emit only after success
- [ ] Critical durable business facts are not browser-only
- [ ] Consent and identity lifecycle live in adapters
- [ ] Analytics failures never fail the user workflow
- [ ] Feature code never imports a vendor analytics SDK
- [ ] Tests use spies/fakes rather than live destinations

## Related Docs

- [Client Operational Logging](./logging.md)
- [Client API Architecture](./client-api-architecture.md)
- [Client Conventions](./conventions.md)
- [Server Product Analytics](../../server/core/product-analytics.md)
