# Skillshare-Installable Skills

Date: 2026-11-14

## Changes

- Replaced the `packages/ui/<system>` placeholder with `packages/ui/<design-system>` in the client and monorepo canonical docs and the `$client` `workspace` and `$monorepo` `packages` references. Skillshare's install audit reads `<system>` as an agent directive tag and reported it as a HIGH prompt-injection finding.
- Added the missing `development/skill/agents/openai.yaml` and gave the `$development` description a "Use when" trigger, which skillshare's description lint requires.
- Declared the maintainer-only Turborepo project skill in `.skillshare/config.yaml` with a `skills.lock.json` pin, so `skillshare install -p` can restore it on a fresh clone. Previously the downloaded skill was gitignored but not declared, leaving the committed `.agents/skills/turborepo` and `.claude/skills/turborepo` links dangling and `skillshare doctor -p` reporting two broken symlinks. Stopped tracking the machine-local `.skillshare/skills/.metadata.json`.
- Added `scripts/validate-skills.py`, a standard-library check of what installers rely on, and documented it with an isolated skillshare test in `CONTRIBUTING.md`.
- Documented skillshare installation, tracked installs, and updates in `consumer/INSTALL-SKILLS.md` and listed `$development` in the repository-local layout.
- Removed the non-canonical `legacy/` directory and every pointer to it (README indexes and source tree, client/server READMEs, client core onboarding and anti-pattern lists, the Next.js index, inline "historical examples" pointers, and the diagram tree). The remaining canonical guidance is unchanged.
- Quoted the role-map keys in the Supabase and tRPC authentication samples (`"admin":`). Lines beginning with `admin:` matched skillshare's CRITICAL `prompt-injection-1` rule, which blocked `--track` installs because a tracked install audits the whole repository. `scripts/validate-skills.py` now checks the critical prompt-injection patterns repository-wide.

## Validation

- Reviewed the client, monorepo, and server slices mapped to every edited source (the placeholder rename, removed legacy pointers, and quoted sample keys); apart from the two placeholder references, none needed a content change. Refreshed only those reviewed fingerprints; all four drift checks report current and the server checker tests pass.
- Installed all four skills with skillshare v0.30.7 into an isolated home from the local checkout and from the pushed branch: exactly `client`, `server`, `monorepo`, and `development` were discovered and synced, `doctor` reported no skill errors, `audit` reported no finding above LOW, and `analyze` reported no lint issues. With a `high` audit threshold the previous revision refused `client` and `monorepo`; this revision installs all four. A `--track` install, previously blocked by four CRITICAL findings, now installs, syncs, audits, checks, and updates cleanly.
