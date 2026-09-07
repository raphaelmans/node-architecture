# Drizzle Repository Convention

Use when Drizzle is installed or explicitly selected. It is an independent persistence implementation, not a prerequisite for Supabase and not tied to Supabase hosting. Apply [core conventions](../../../../core/conventions.md), [transactions](../../../../core/transaction.md), and the capability's access rules first.

If Better Auth uses this database, also apply [its integration convention](../better-auth/README.md) for auth schema generation, lifecycle ownership, and cross-operation transaction limits. Business repositories remain independent of that auth adapter.

## Application Boundary

- Keep repository contracts and application records owned by the domain/application module. Map selected rows into those records; ORM schema-derived types remain inside persistence infrastructure, not service interfaces or shared wire contracts.
- Keep concrete domain repositories beside their owning module or in its resolved adapter package. Shared database infrastructure owns the client, schema, driver setup, and transaction plumbing.
- Compose the selected driver from narrow validated configuration. Derive driver, pooling, migration, and deployment compatibility from the installed stack and current official docs.
- Translate recognized provider errors at the repository boundary; match exact constraints for domain conflicts. Do not leak driver failures or interpret every uniqueness error as the same business conflict.

## Atomic Operations

Use a real driver-supported transaction for related writes. The service/use case selects the application operation and atomicity boundary; infrastructure creates the opaque transaction context, and participating repositories bridge it to the same transaction client. Do not silently use the root client inside a transaction.

For an application operation also implemented by a Supabase database function, expose the same operation-level repository contract and observable result. A Drizzle adapter may execute that operation with its own transaction internally; it implements the application's declared boundary rather than inventing workflow policy. Do not require a Supabase HTTP adapter to emulate callback transactions.

Scope reads and guarded writes to the owning organization/resource, enforce declared relationship constraints, and protect race-sensitive authorization preconditions through commit. An SQL connection does not automatically carry a Supabase user's identity or RLS context; inspect its actual database role and test the selected enforcement path.

## Coexistence and Verification

Drizzle may coexist with Supabase Auth, Storage, Realtime, direct data repositories, or hosting. Assign one migration owner per schema object and one authority per write operation. Separate Supabase HTTP requests do not join an open Drizzle transaction merely because they reach the same database.

Verify record mapping, scoped reads/writes, recognized errors, rollback after an intermediate failure, and concurrent operations against the real database. Run equivalent contract scenarios for each implementation that is actually shipped; do not scaffold a second adapter just for hypothetical portability.

## Official Sources

- [Drizzle documentation](https://orm.drizzle.team/docs/overview)
- [Drizzle transactions](https://orm.drizzle.team/docs/transactions)
- [Drizzle migrations](https://orm.drizzle.team/docs/migrations)
- [Supabase with Drizzle](https://supabase.com/docs/guides/database/drizzle), only when that host is selected

These sources own current installation commands, driver APIs, schema syntax, and migration tooling. This leaf captures our ownership and compatibility approach, not a PostgreSQL or ORM manual.
