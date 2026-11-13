# Skillshare-Installable Skills

Date: 2026-11-14

## Changes

- Replaced the `packages/ui/<system>` placeholder with `packages/ui/<design-system>` in the client and monorepo canonical docs and the `$client` `workspace` and `$monorepo` `packages` references. Skillshare's install audit reads `<system>` as an agent directive tag and reported it as a HIGH prompt-injection finding.
- Added the missing `development/skill/agents/openai.yaml` and gave the `$development` description a "Use when" trigger, which skillshare's description lint requires.
- Declared the maintainer-only Turborepo project skill in `.skillshare/config.yaml` with a `skills.lock.json` pin, so `skillshare install -p` can restore it on a fresh clone. Previously the downloaded skill was gitignored but not declared, leaving the committed `.agents/skills/turborepo` and `.claude/skills/turborepo` links dangling and `skillshare doctor -p` reporting two broken symlinks. Stopped tracking the machine-local `.skillshare/skills/.metadata.json`.
- Added `scripts/validate-skills.py`, a standard-library check of what installers rely on, and documented it with an isolated skillshare test in `CONTRIBUTING.md`.
- Documented skillshare installation and updates in `consumer/INSTALL-SKILLS.md` and listed `$development` in the repository-local layout. A `--track` install is documented as unsupported for now: it audits the whole repository, and four code samples (two canonical, two legacy) match skillshare's CRITICAL prompt-override pattern.

## Validation

- Reviewed the client, monorepo, and server slices mapped to the renamed placeholder's sources; only the two references above mention it. Refreshed those fingerprints; all four drift checks report current and the server checker tests pass.
- Installed all four skills with skillshare v0.30.7 into an isolated home from the local checkout and from the pushed branch: exactly `client`, `server`, `monorepo`, and `development` were discovered and synced, `doctor` reported no skill errors, `audit` reported no finding above LOW, and `analyze` reported no lint issues. With a `high` audit threshold the previous revision refused `client` and `monorepo`; this revision installs all four.
