# Architecture Skill Consumers

The generated `guides/` bundle is deprecated and `copy-guides.sh` is disabled.

Use [INSTALL-SKILLS.md](./INSTALL-SKILLS.md) to install `$client`, `$server`, `$monorepo`, and `$development`.

Then use [Architecture Initialization](./ARCHITECTURE-INIT.md) with `/development init` to create a sectioned reference index and lightweight entry point. Detailed conventions remain in their authoritative references and load only when relevant.

## Source Model

- `development/core/`, `development/tools/`, `development/frameworks/`, and `development/runtimes/` own local development guidance; `development/skill/` packages it and `development/skill-maintenance/` checks source drift.

- `client/core/` and `client/frameworks/` remain the canonical authoring documents.
- `server/core/` and `server/runtime/` remain the canonical server authoring documents.
- `client/skill/references/` contains portable, concern-based derivatives for agents.
- `server/skill/references/` contains the matching server derivatives.
- The sibling `client/skill-maintenance/` and `server/skill-maintenance/` directories flag references that require review after source-doc changes; they are not installed with the skills.

Legacy integration files in this directory now provide migration pointers only; they are no longer copied into consumer repositories.

## Access and Persistence Leaves

These are references inside the existing skills, not separately installed plugins:

| Work | References to compose |
| --- | --- |
| Organization-backed product workspace | `$server` foundations + [tenancy](../server/skill/references/foundations/tenancy.md) |
| RBAC and branch-scoped access | `$server` security + [authorization](../server/skill/references/security/authorization.md) + [RBAC](../server/skill/references/security/rbac.md); add tenancy for organization scope |
| Node.js or Next.js server endpoint | The same server policy leaves plus the existing runtime adapter |
| Standalone React permission UX | `$client` react + [React access control](../client/skill/references/react/access-control.md) |
| Next.js permission UX and protected rendering | React access control + `$client` nextjs + [Next.js access control](../client/skill/references/nextjs/access-control.md) |
| Drizzle persistence | `$server` runtimes + data-flow + [Drizzle](../server/skill/references/runtimes/drizzle.md) |
| Supabase integration/direct persistence | `$server` runtimes + [Supabase](../server/skill/references/runtimes/supabase.md); add data-flow/security as needed |

Drizzle and Supabase are independent siblings: load either or both for the actual stack. The access model follows Better Auth conventions without installing it or assuming its teams provide branch-level roles. There is no PostgreSQL leaf; vendor docs own database mechanics. Product workspaces do not activate the monorepo `workspace` slice unless package topology is involved.
