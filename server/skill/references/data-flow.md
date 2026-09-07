# Data-Flow Slice

Use this slice for route-to-repository flow, service/use-case selection, transaction ownership, repository design, persistence, ID generation, request-scoped composition, and public result mapping.

## Request Flow

This is the application-owned capability flow. Selected provider-native authentication/plugin endpoints retain their own handler/protocol; use [Better Auth](runtimes/better-auth.md) when applicable. Their integration projects plain app-facing results without exempting custom business operations from this flow.

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

For concrete persistence, load only the selected [Drizzle](runtimes/drizzle.md) or [Supabase](runtimes/supabase.md) leaf. Application-owned repository interfaces and records must not be derived from ORM or generated Supabase row types; map at the adapter boundary.

- Simple read: controller -> one service -> repository.
- Single-domain write: controller -> one service; let the service own its atomic write behavior.
- Multi-service write: controller -> use case -> participating services/repositories through a real shared transaction, or one purpose-specific atomic repository operation when the data API cannot share a transaction context.
- Write plus external side effect: persist business state and an outbox/job record atomically, then dispatch after commit.

Controllers map public wire values to commands and internal values back to view models. Services return domain/application results rather than transport envelopes.

## Transactions

When the selected driver supports a shared transaction, keep its kernel contract opaque:

```ts
declare const transactionContextBrand: unique symbol;

export type TransactionContext = {
  readonly [transactionContextBrand]: "TransactionContext";
};

export interface TransactionOptions {
  tx?: TransactionContext;
}
```

Only transaction infrastructure creates the context, and only persistence infrastructure/repositories bridge it to a concrete transaction. Use cases own multi-service atomicity. Services and repositories accept optional `TransactionOptions` only when they can participate in that real transaction.

For Supabase data-API multi-write work, define an application-owned atomic operation and implement it with one database function. A Drizzle implementation may fulfill the same operation with a transaction inside its adapter. Preserve preconditions, outcomes, rollback, errors, and replay semantics; do not fake `TransactionManager.run` over separate HTTP requests or accept ignored transaction options. Functions enforce authorization-critical preconditions at commit, and external effects remain outside the database transaction.

Never add request IDs, actors, loggers, analytics, or arbitrary metadata to `TransactionOptions`. Never retry generic work inside a PostgreSQL transaction after the transaction has entered an aborted state.

## Repository Boundary

- Accept domain/application values and optional transaction options.
- Return application-owned records or explicit results, not generated provider rows or wire envelopes.
- Select the transaction client through one private helper when shared transaction participation is supported.
- Translate only recognized constraints/provider codes to typed errors.
- Let unknown database failures propagate to central sanitization.
- Keep authorization and cross-entity policy owned by services/use cases; scoped queries, constraints, RLS, and atomic functions enforce that declared policy at the persistence boundary.
- Route workers, CLIs, and alternate transports through the same service/use-case capability authorization rather than duplicating ownership or tenant checks in adapters.
- Keep the repository beside its domain module. Shared database infrastructure supplies clients, schemas, and transaction plumbing but does not own domain-specific queries.

For known uniqueness failures, match both the installed PostgreSQL adapter's documented unique-violation signal and the exact constraint name. Do not map every database uniqueness failure to one domain conflict.

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

## Official Implementation References

- [PostgreSQL error codes](https://www.postgresql.org/docs/current/errcodes-appendix.html)
- [Drizzle ORM documentation](https://orm.drizzle.team/docs/overview)

Drizzle and direct Supabase access are independent persistence specializations. The stable rationale is to classify provider failures structurally and match domain conflicts by exact constraint; the selected database and driver documentation own concrete codes and error-object shapes. No standalone PostgreSQL leaf is required.

## Derivation Sources

Derived from core flow, conventions, controllers, transaction, ID generation, tRPC composition, and Supabase persistence/composition guides. Exact paths and fingerprints are maintained outside the portable skill package.
