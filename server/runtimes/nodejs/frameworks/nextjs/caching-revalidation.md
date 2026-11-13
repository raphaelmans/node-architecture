# Caching + Revalidation (Next.js)

> Next.js App Router cache conventions for server-rendered pages and data.

## Scope

Use this for metaframework-specific caching behavior (`revalidate`, cache tags, on-demand invalidation).

## Choose the Cache Model First

Next.js 16 has two cache models. Do not mix their examples without explicitly
declaring which model the application uses.

### Cache Components enabled (current model)

```ts
import { cacheLife, cacheTag } from "next/cache";

export async function getFeatured() {
  "use cache";
  cacheLife("hours");
  cacheTag("home:featured");
  return fetchFeatured();
}
```

### Cache Components disabled (previous model)

Only in this model, use route/page `revalidate` and `unstable_cache`:

```ts
export const revalidate = 3600;

const getFeatured = unstable_cache(
  async () => fetchFeatured(),
  ["home-featured"],
  { tags: ["home:featured"], revalidate: 3600 },
);
```

## On-Demand Invalidation

Use server actions or secure admin endpoints to invalidate:

- `revalidatePath(path)` for route-level refresh
- `revalidateTag(tag, "max")` for stale-while-revalidate shared refresh
- `updateTag(tag)` when a Server Action requires read-your-own-writes behavior

Guard invalidation endpoints/actions with auth/role checks.

## Tag Naming Convention

Use stable namespace tags:

- `<surface>:<resource>` (for example `home:featured`)
- Avoid per-request random tag names.

## Ownership Rules

- Write paths must own invalidation responsibility for affected tags/paths.
- Keep invalidation near mutation handlers, not scattered across UI.

## Failure Handling

- Invalidation failures should use contextual `AppLogger`; it adds the namespaced request ID and active trace fields.
- Mutation success should not silently depend on invalidation success for correctness.

## References

- [Next.js Cache Components](https://nextjs.org/docs/app/getting-started/cache-components)
- [Caching without Cache Components (previous model)](https://nextjs.org/docs/app/guides/caching-without-cache-components)
- [`revalidateTag`](https://nextjs.org/docs/app/api-reference/functions/revalidateTag)
- [`updateTag`](https://nextjs.org/docs/app/api-reference/functions/updateTag)
