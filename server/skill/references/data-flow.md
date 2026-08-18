# Data-Flow Slice

Use this slice for route-to-repository flow, service/use-case selection, transaction ownership, repository design, persistence, ID generation, request-scoped composition, and public result mapping.

## Request Flow

```text
request
  -> adapter: extract/authenticate/validate
  -> controller: map input + actor
  -> service or use case
  -> repository/provider port
  -> infrastructure
  -> controller: map result to public payload
  -> adapter: validate payload + serialize envelope
```

Do not pass a framework request, generic context, logger, trace ID, or service container through this chain.

## Reads and Writes

- Simple read: controller -> one service -> repository.
- Single-domain write: controller -> one service; let the service own its atomic write behavior.
- Multi-service write: controller -> use case -> transaction manager -> participating services/repositories.
- Write plus external side effect: persist business state and an outbox/job record atomically, then dispatch after commit.

Controllers map public wire values to commands and internal values back to view models. Services return domain/application results rather than transport envelopes.

## Transactions

Keep the kernel transaction contract opaque:

```ts
declare const transactionContextBrand: unique symbol;

export type TransactionContext = {
  readonly [transactionContextBrand]: "TransactionContext";
};

export interface TransactionOptions {
  tx?: TransactionContext;
}
```

Only transaction infrastructure creates the context, and only repositories bridge it to a concrete ORM transaction. Use cases own multi-service transactions. Services and repositories accept optional `TransactionOptions` only when they participate in database work.

Never add request IDs, actors, loggers, analytics, or arbitrary metadata to `TransactionOptions`. Never retry generic work inside a PostgreSQL transaction after the transaction has entered an aborted state.

## Repository Boundary

- Accept domain/application values and optional transaction options.
- Return entities or explicit persistence results, not wire envelopes.
- Select the transaction client through one private helper.
- Translate only recognized constraints/provider codes to typed errors.
- Let unknown database failures propagate to central sanitization.
- Keep authorization and cross-entity business rules in services/use cases.
- Route workers, CLIs, and alternate transports through the same service/use-case capability authorization rather than duplicating ownership or tenant checks in adapters.
- Keep the repository beside its domain module. Shared database infrastructure supplies clients, schemas, and transaction plumbing but does not own domain-specific queries.

For known uniqueness failures, match the exact constraint name. Do not map every PostgreSQL `23505` to one domain conflict.

## ID Policy

Prefer database-generated UUIDs and return inserted rows. Generate IDs in the application only when the ID must exist before insertion, such as constructing related records or an outbox message in one transaction.

Treat a true UUID primary-key collision as an unexpected failure. Do not add a generic retry loop; ordinary uniqueness conflicts usually indicate a business key and must be translated by exact constraint.

## Request-Scoped Providers

When infrastructure depends on cookies, headers, or an authenticated provider session, construct that dependency in an outer request-scoped factory and inject the resulting port/service into the controller graph. Shared transport context may depend on a module-owned resolver interface; it must not construct module repositories directly.

## Review Checklist

- The adapter calls a controller, not a service or repository.
- The controller maps the public boundary and calls one application object.
- Transaction ownership sits at the smallest orchestration boundary spanning all writes.
- Only database operations receive transaction context.
- Repository errors are translated by exact recognized provider metadata.
- IDs and retries follow actual persistence semantics.
- Request-scoped provider clients cannot leak across requests.
- Results are mapped and response-validated before serialization.

## Derivation Sources

Derived from core flow, conventions, controllers, transaction, ID generation, tRPC composition, and Supabase persistence/composition guides. Exact paths and fingerprints are maintained outside the portable skill package.
