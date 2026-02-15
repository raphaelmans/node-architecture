# Caching + Revalidation (Next.js)

> Next.js App Router cache conventions for server-rendered pages and data.

## Scope

Use this for metaframework-specific caching behavior (`revalidate`, cache tags, on-demand invalidation).

## Baseline Patterns

- Route/page-level TTL with `export const revalidate = <seconds>`
- Data-level caching with `unstable_cache`
- Tagged entries for targeted invalidation

```ts
export const revalidate = 3600;

const getFeatured = unstable_cache(
  async () => fetchFeatured(),
  ["home-featured"],
  { tags: ["home:featured"] },
);
```

## On-Demand Invalidation

Use server actions or secure admin endpoints to invalidate:

- `revalidatePath(path)` for route-level refresh
- `revalidateTag(tag)` for shared data refresh

Guard invalidation endpoints/actions with auth/role checks.

## Tag Naming Convention

Use stable namespace tags:

- `<surface>:<resource>` (for example `home:featured`)
- Avoid per-request random tag names.

## Ownership Rules

- Write paths must own invalidation responsibility for affected tags/paths.
- Keep invalidation near mutation handlers, not scattered across UI.

## Failure Handling

- Invalidation failures should be logged with `requestId`.
- Mutation success should not silently depend on invalidation success for correctness.

