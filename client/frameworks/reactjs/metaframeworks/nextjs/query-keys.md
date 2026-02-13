# Query Keys (Moved)

Query key conventions are framework-agnostic and live in:

- [Query Keys (Core)](../../../../core/query-keys.md)

Next.js-specific usage notes:

- If you use non-tRPC HTTP clients (e.g. `ky` calling Next.js `route.ts`), you still use the same `src/common/query-keys/<feature>.ts` convention.
