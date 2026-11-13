---
status: accepted
---

# Use atomic repository operations where transactions cannot be shared

A shared transaction context works only when the selected driver can hold one real transaction across the participating calls. A data API such as Supabase's cannot, because each call is a separate request. For those implementations a multi-write operation is one purpose-specific, application-owned repository method fulfilled by a single database function, rather than an emulated transaction over several requests or a mandatory ORM beside the data API. The application still owns the policy and result contract; the function enforces the race-sensitive preconditions and persists required audit and outbox intent at the atomic boundary.

## Consequences

- The same repository contract may be fulfilled by a Drizzle implementation using an internal transaction; both preserve application records, rollback, and retry outcomes.
- Some business preconditions live in database functions, so they need real-database tests and a migration owner.
- A directly reachable database function is a public entrypoint and must enforce its full contract or be restricted to the intended caller.
- External effects such as email or storage never participate in the atomic operation.
