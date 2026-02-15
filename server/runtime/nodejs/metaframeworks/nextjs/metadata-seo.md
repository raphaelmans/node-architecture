# Metadata + SEO (Next.js)

> Server conventions for `generateMetadata`, `robots.ts`, and `sitemap.ts`.

## Goals

- Keep canonical metadata server-generated and consistent.
- Separate production indexing behavior from non-production.
- Keep dynamic SEO entries deterministic and validated.

## `generateMetadata` Rules

- Validate params before building metadata.
- Return safe defaults for missing/unresolvable resources.
- Keep canonical URL generation centralized.

## `robots.ts` Rules

- Non-production: disallow crawling by default.
- Production: explicitly disallow private/auth/admin paths.
- Always include sitemap URL in production output.

## `sitemap.ts` Rules

- Use stable route sources and canonical route builders.
- Include `lastModified` when available.
- Set reasonable `changeFrequency` and `priority` values.
- Use `revalidate` to avoid heavy regeneration on every request.

## Route Group SEO Controls

For private app sections (`admin`, `owner`, authenticated areas), define robots/noindex behavior at layout level when needed.

## Operational Notes

- Keep SEO logic in server files (`app/*`) only.
- Avoid embedding product copy logic in low-level metadata utilities.

