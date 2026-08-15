# AGENTS.md Alignment (Deprecated Copy Workflow)

The previous workflow copied architecture documents into `guides/` and required a large `AGENTS.md` include list. That workflow is disabled.

## Preferred Integration

1. Install the `$client` and `$server` skills using [INSTALL-SKILLS.md](./INSTALL-SKILLS.md).
2. Keep project-specific facts and constraints in the consuming repository's `AGENTS.md`.
3. Invoke `$client` for client tasks and `$server` for server tasks; each router loads only the relevant concern slices.

Do not paste every architecture document into `AGENTS.md`. The skills provide progressive disclosure and keep reusable guidance outside the project's always-loaded instruction budget.

## Behavioral Rules Worth Keeping Locally

- Do not refactor unrelated legacy code unless the user requests it.
- New and modified client or server files must follow the selected architecture slices.
- Framework guidance extends core contracts and does not override them.
- Ignore library-specific guidance when that library is not present or requested.

Keep repository-specific deployment, data, security, and migration constraints locally; the reusable skills do not infer project facts that are not present in the target repository.
