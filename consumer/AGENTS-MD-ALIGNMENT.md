# AGENTS.md Alignment (Deprecated Copy Workflow)

The previous workflow copied architecture documents into `guides/` and required a large `AGENTS.md` include list. That workflow is disabled.

## Preferred Integration

1. Install `$development` and the applicable architecture skills using [INSTALL-SKILLS.md](./INSTALL-SKILLS.md).
2. Use [Architecture Initialization](./ARCHITECTURE-INIT.md) with `/development init` to create a navigation-only `ARCHITECTURE.md` index and maintain a short pointer in the existing agent instruction file. Keep conventions in their authoritative references and preserve unrelated instructions.
3. Invoke `$client`, `$server`, or `$monorepo` for matching tasks; each router loads only the relevant concern slices.

Do not paste every architecture document into `AGENTS.md`. The skills provide progressive disclosure and keep reusable guidance outside the project's always-loaded instruction budget.

## Behavioral Rules Worth Keeping Locally

- Do not refactor unrelated legacy code unless the user requests it.
- New and modified client or server files must follow the selected architecture slices.
- Framework guidance extends core contracts and does not override them.
- Ignore library-specific guidance when that library is not present or requested.

Keep repository-specific deployment, data, security, and migration constraints locally; the reusable skills do not infer project facts that are not present in the target repository.
