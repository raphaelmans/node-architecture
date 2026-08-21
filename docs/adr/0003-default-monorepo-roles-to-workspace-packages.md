---
status: accepted
---

# Default monorepo roles to workspace packages

When a monorepo topology is detected, activated capability and adapter roles of a new module use the repository's workspace-package convention even when only one deployable currently consumes them. Explicit user scope may keep them app-local, and a cohesive existing app-local module remains in place for incremental operations unless migration is explicitly requested; unused roles remain absent. This favors a consistent reusable package graph without partially migrating existing modules or creating one package per operation or onion layer.
